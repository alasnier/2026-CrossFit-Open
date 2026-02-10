# orchestrator/langgraph_team.py (v2 LLM - Gemini)
import glob
import json
import os
import subprocess
import sys
import textwrap
from typing import Dict, List, TypedDict

# Gemini (google-generativeai)
import google.generativeai as genai

# LangGraph
from langgraph.graph import StateGraph


# -------- Utils shell / IO --------
def sh(cmd: str) -> str:
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return (res.stdout or "") + (("\n[stderr]\n" + res.stderr) if res.stderr else "")


def read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def write_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -------- LLM setup (Gemini) --------
def init_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    genai.configure(api_key=api_key)
    # modèle rapide et économique pour CI
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )


def gemini_json(model, prompt: str) -> dict:
    """Appelle Gemini et parse du JSON strict (response_mime_type=application/json)."""
    resp = model.generate_content(prompt)
    txt = resp.text or "{}"
    try:
        return json.loads(txt)
    except Exception:
        # Dernier recours : tenter d'extraire un bloc JSON
        start = txt.find("{")
        end = txt.rfind("}")
        return json.loads(txt[start : end + 1]) if start >= 0 and end >= 0 else {}


# -------- État partagé --------
class State(TypedDict):
    spec_path: str
    plan: dict
    security_report: str
    diffs: List[dict]  # [{path, content_after}]
    test_report: str
    docs_note: str


# -------- Nœuds d'agents --------
def planner(state: State) -> Dict:
    model = init_gemini()
    spec = read(state["spec_path"])
    agents_rules = read("agents/AGENTS.md")
    repo_tree = "\n".join(
        sorted(
            [
                p
                for p in glob.glob("**/*", recursive=True)
                if os.path.isfile(p) and not p.startswith(".git/")
            ][:200]
        )
    )
    plan_schema = textwrap.dedent(
        """
    Tu es @planner. Produit un JSON strict correspondant à ce schéma:
    {
      "targets": [{"path": "string", "reason": "string"}],
      "constraints": {"forbidden_globs": ["string"], "allowed_roots": ["string"]},
      "notes": "string"
    }
    Règles:
    - Respecte AGENTS.md (frontières/style).
    - Propose une mise à jour 2026 minimale et sûre (README, libellés, petits correctifs).
    - Interdiction de modifier creds, .env, .github, venv, credentials/, *.key, *.pem.
    - Préfère des changements atomiques faciles à review.
    Contexte SPEC:
    """
        + spec
        + "\n\nAGENTS.md:\n"
        + agents_rules
        + "\n\nArborescence (200 premiers fichiers):\n"
        + repo_tree
    )
    plan = gemini_json(model, plan_schema)
    # Valeurs par défaut sûres
    plan.setdefault("constraints", {})
    plan["constraints"].setdefault(
        "forbidden_globs",
        [".github/**", ".venv/**", "credentials/**", "**/*.key", "**/*.pem"],
    )
    plan["constraints"].setdefault("allowed_roots", ["", "src", "pages", "docs"])
    return {"plan": plan}


def auditor(state: State) -> Dict:
    out = []
    out.append(sh("ruff check --fix ."))
    out.append(sh("bandit -r . -q || exit 0"))
    out.append(sh("safety scan -r requirements.txt || exit 0"))
    return {"security_report": "\n\n".join(out)}


def coder(state: State) -> Dict:
    """
    Coder conservateur: propose des diffs sûrs (README / libellés 2026).
    Schéma de sortie: [{"path": "README.md", "content_after": "<nouveau contenu>"}]
    """
    model = init_gemini()
    plan = state.get("plan", {})
    targets = plan.get("targets", [])
    diffs: List[dict] = []

    # 1) README.md (si présent) — exemple concret
    if os.path.exists("README.md"):
        before = read("README.md")
        prompt = textwrap.dedent(f"""
        Tu es @coder. Modifie le contenu pour refléter "CrossFit Open 2026".
        - Conserve le style et les sections existantes.
        - Corrige les références "2025" obsolètes si elles signifient l'édition en cours.
        - Ne change pas les badges/URLs si tu n'es pas certain.
        - Retourne STRICTEMENT un JSON: {{"path":"README.md","content_after":"..."}}
        CONTENU_ACTUEL:
        <<README>>
        {before}
        <<FIN>>
        """)
        patch = gemini_json(model, prompt)
        if patch.get("path") == "README.md" and patch.get("content_after"):
            diffs.append(patch)

    # 2) Cibles additionnelles proposées par le plan (petits fichiers texte)
    safe_roots = set(plan.get("constraints", {}).get("allowed_roots", []))
    forbidden = plan.get("constraints", {}).get("forbidden_globs", [])
    for t in targets[:5]:  # limite à 5 pour CI
        p = t.get("path", "")
        if not p or not os.path.exists(p) or os.path.isdir(p):
            continue
        # filtre simple "allowed_roots"
        root = p.split("/")[0] if "/" in p else ""
        if safe_roots and root not in safe_roots:
            continue
        # garde-fous sur taille
        if os.path.getsize(p) > 200_000:
            continue
        before = read(p)
        # Demande une petite correction/MAJ 2026 (si applicable)
        prompt = textwrap.dedent(f"""
        Tu es @coder. Si et seulement si une mise à jour "Open 2026" est pertinente, propose une version corrigée du fichier.
        Sinon, retourne le fichier inchangé.
        JSON STRICT: {{"path":"{p}","content_after":"..."}}
        CONTENU_ACTUEL:
        <<FILE>>
        {before}
        <<FIN>>
        """)
        patch = gemini_json(model, prompt)
        if (
            patch.get("path") == p
            and patch.get("content_after")
            and patch["content_after"] != before
        ):
            diffs.append(patch)

    return {"diffs": diffs}


def tester(state: State) -> Dict:
    return {"test_report": sh("pytest -q || exit 0")}


def docs(state: State) -> Dict:
    note = "MAJ docs recommandée si de nouvelles règles/données 2026 sont ajoutées."
    return {"docs_note": note}


# -------- Graphe LangGraph --------
graph = StateGraph(State)
graph.add_node("planner", planner)
graph.add_node("auditor", auditor)
graph.add_node("coder", coder)
graph.add_node("tester", tester)
graph.add_node("docs", docs)

graph.add_edge("planner", "auditor")
graph.add_edge("auditor", "coder")
graph.add_edge("coder", "tester")
graph.add_edge("tester", "docs")

graph.set_entry_point("planner")
graph.set_finish_point("docs")

compiled = graph.compile()

if __name__ == "__main__":
    spec = sys.argv[1] if len(sys.argv) > 1 else "specs/feature-template.yaml"
    result = compiled.invoke({"spec_path": spec, "diffs": []})
    # Artefacts pour la PR
    write_json(
        "agent_artifacts.json",
        {
            "plan": result.get("plan"),
            "security_report": result.get("security_report"),
            "test_report": result.get("test_report"),
            "docs_note": result.get("docs_note"),
        },
    )
    write_json("diffs.json", result.get("diffs", []))
    print("\n[Agent artifacts written to agent_artifacts.json + diffs.json]")
