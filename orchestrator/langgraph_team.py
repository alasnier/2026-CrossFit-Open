# orchestrator/langgraph_team.py (v3 - google-genai SDK)
import glob
import json
import os
import subprocess
import sys
import textwrap
import time
from typing import Dict, List, TypedDict

# Nouveau SDK (google-genai, remplace google-generativeai déprécié)
from google import genai
from google.genai import types

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


# -------- LLM setup (google-genai) --------
def init_client() -> genai.Client:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    return genai.Client(api_key=api_key)


def gemini_json(client: genai.Client, prompt: str, retries: int = 1) -> dict:
    """Appelle Gemini avec retry exponentiel sur 429, retourne du JSON strict."""
    model = "gemini-2.0-flash-001"  # free tier : 1500 req/jour, 15 req/min
    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
    )
    for attempt in range(retries):
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            txt = resp.text or "{}"
            try:
                return json.loads(txt)
            except Exception:
                start = txt.find("{")
                end = txt.rfind("}")
                return (
                    json.loads(txt[start : end + 1]) if start >= 0 and end >= 0 else {}
                )
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e):
                wait = 60 * (attempt + 1)  # 60s, 120s, 180s
                print(
                    f"[gemini] 429 quota — attente {wait}s (tentative {attempt + 1}/{retries})"
                )
                time.sleep(wait)
            else:
                raise
    return {}


# -------- État partagé --------
class State(TypedDict):
    spec_path: str
    plan: dict
    security_report: str
    diffs: List[dict]
    test_report: str
    docs_note: str


# -------- Nœuds d'agents --------


def plan_and_code(state: State) -> Dict:
    client = init_client()  # google-genai Client
    spec = read(state["spec_path"])
    agents_rules = read("agents/AGENTS.md")
    # Limiter l'arborescence à 80 fichiers pour réduire les tokens
    repo_tree = "\n".join(
        sorted(
            [
                p
                for p in glob.glob("**/*", recursive=True)
                if os.path.isfile(p) and not p.startswith(".git/")
            ][:80]
        )
    )
    prompt = textwrap.dedent(f"""
    Tu es une équipe @planner+@coder. Retourne STRICTEMENT un JSON:
    {{
      "plan": {{
        "targets": [{{"path":"string","reason":"string"}}],
        "constraints": {{"forbidden_globs":["string"],"allowed_roots":["string"]}},
        "notes":"string"
      }},
      "diffs": [{{"path":"string","content_after":"string"}}]
    }}
    Règles:
    - Respecte AGENTS.md (frontières/style).
    - Mise à jour 2026 minimale et sûre (README/libellés, petits correctifs).
    - Interdit: creds, .env, .github, venv, credentials/, *.key, *.pem.
    - Préfère des changements atomiques.
    SPEC:
    {spec}

    AGENTS.md:
    {agents_rules}

    Arborescence (80 premiers fichiers):
    {repo_tree}
    """)
    out = gemini_json(client, prompt, retries=1)  # <— 1 seule tentative
    plan = out.get("plan", {})
    # sane defaults
    plan.setdefault("constraints", {})
    plan["constraints"].setdefault(
        "forbidden_globs",
        [".github/**", ".venv/**", "credentials/**", "**/*.key", "**/*.pem"],
    )
    plan["constraints"].setdefault("allowed_roots", ["", "pages", "docs"])
    return {"plan": plan, "diffs": out.get("diffs", [])}


def auditor(state: State) -> Dict:
    out = []
    out.append(sh("ruff check --fix ."))
    out.append(sh("bandit -r . -q || exit 0"))
    out.append(sh("safety scan -r requirements.txt || exit 0"))
    return {"security_report": "\n\n".join(out)}


def tester(state: State) -> Dict:
    return {"test_report": sh("pytest -q || exit 0")}


def docs(state: State) -> Dict:
    return {
        "docs_note": "MAJ docs recommandée si de nouvelles règles/données 2026 sont ajoutées."
    }


# -------- Graphe LangGraph --------
graph = StateGraph(State)
graph.add_node("plan_and_code", plan_and_code)
graph.add_node("auditor", auditor)
graph.add_node("tester", tester)
graph.add_node("docs", docs)

graph.add_edge("plan_and_code", "auditor")
graph.add_edge("auditor", "tester")
graph.add_edge("tester", "docs")
graph.set_entry_point("plan_and_code")
graph.set_finish_point("docs")

compiled = graph.compile()

if __name__ == "__main__":
    spec = sys.argv[1] if len(sys.argv) > 1 else "specs/feature-template.yaml"
    result = compiled.invoke({"spec_path": spec, "diffs": []})
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
