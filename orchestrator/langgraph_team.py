# orchestrator/langgraph_team.py (Version simplifiée pour CI Robuste)
from __future__ import annotations

import json
import os
import sys
import textwrap
from typing import TypedDict

from google import genai
from google.genai import types
from langgraph.graph import StateGraph


# ---------- Utils ----------
def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def write_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- LLM (google-genai) ----------
def init_client() -> genai.Client:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    return genai.Client(api_key=api_key)


def gemini_json(client: genai.Client, prompt: str) -> dict:
    # On change de réservoirs pour éviter les erreurs 429 persistantes
    models_to_try = [
        "gemini-3-flash-preview",  # Nouvelle génération (Quota souvent distinct)
        "gemini-1.5-flash",  # Ancienne génération (Le plus de chances d'être dispo)
        "gemini-exp-1206",  # Modèle expérimental (Quota à part)
        "gemini-2.0-flash",  # Ton choix initial (en dernier recours)
    ]

    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
    )

    for model_name in models_to_try:
        print(f"[gemini] Tentative avec : {model_name}")
        try:
            # On ne fait qu'une tentative rapide pour passer au suivant si ça bloque
            resp = client.models.generate_content(model=model_name, contents=prompt, config=config)
            print(f"[gemini] Succès avec {model_name} !")
            return json.loads(resp.text or "{}")

        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                # Si le quota journalier est atteint (limit: 0), on n'attend pas, on switch.
                if "PerDay" in err_msg:
                    print(f"[gemini] {model_name} : Quota journalier vide. Suivant...")
                else:
                    print(f"[gemini] {model_name} : Trop de requêtes. Suivant...")
                continue
            else:
                print(f"[gemini] Erreur sur {model_name}: {err_msg}")
                continue

    print("[gemini] 🚨 ÉCHEC : Tous les modèles sont épuisés pour aujourd'hui.")
    return {}


# ---------- État partagé ----------
class State(TypedDict):
    spec_path: str
    plan: dict
    diffs: list[dict]


# ---------- Node Unique : Planner + Coder ----------
def plan_and_code(state: State) -> dict:
    client = init_client()
    spec = read(state["spec_path"])
    agents_rules = read("agents/AGENTS.md")

    # On ne lit que les fichiers pertinents pour limiter les tokens (README ici)
    # Pour le test, on force la lecture du README et requirements.in
    target_files = ["README.md", "requirements.in"]
    file_contents = ""
    for path in target_files:
        if os.path.exists(path):
            file_contents += f"\n--- {path} ---\n{read(path)}\n"

    prompt = textwrap.dedent(f"""
    Tu es un expert DevOps/Python. Applique la SPEC demandée.
    Retourne un JSON strict : {{ "diffs": [{{"path": "...", "content_after": "..."}}] }}
    
    RÈGLES :
    1. Si la spec demande de modifier le README, réécris tout le fichier proprement.
    2. Si 'requirements.in' doit être maj, change-le (mais ne touche PAS à requirements.txt, la CI s'en occupe).
    
    SPEC:
    {spec}

    FICHIERS ACTUELS:
    {file_contents}
    """)

    out = gemini_json(client, prompt)
    return {"diffs": out.get("diffs", [])}


# ---------- Graphe Simple ----------
graph = StateGraph(State)
graph.add_node("plan_and_code", plan_and_code)
graph.set_entry_point("plan_and_code")
graph.set_finish_point("plan_and_code")  # Fin immédiate, la CI gère la suite
compiled = graph.compile()

if __name__ == "__main__":
    spec = sys.argv[1] if len(sys.argv) > 1 else "specs/feature-template.yaml"
    result = compiled.invoke({"spec_path": spec, "diffs": []})
    write_json("diffs.json", result.get("diffs", []))
    print("[Agent] Diffs générés dans diffs.json")
