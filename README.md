# 2026 CrossFit Games Open — Box Interne

Ce projet permet d’organiser un **Open interne** à la box :
- **Inscription** et **saisie des scores** par les athlètes
- **Classements** par sexe / niveau (RX, Scaled, Coach)
- **Stats** et percentiles rapides

**Fenêtre 2026** : 26 fév. → 16 mars 2026 (3 semaines, 3 WODs).

## Stack technique
- **Frontend/UX** : [Streamlit](https://streamlit.io) (Python)
- **Base de données** : Postgres **managed** (Neon ou Supabase, Free tier)
- **CI/CD** : GitHub Actions (lint, audit deps, PR auto)
- **Agents IA** : LangGraph + API Gemini pour générer des PRs (plan/diffs)

## Démo (vidéo)
- 🎥 *Vidéo de démonstration* : [Lien YouTube/Loom]  
  > Astuce : dépose aussi un MP4 (≤25–50 Mo) dans `assets/demo/` ou en **GitHub Release**, puis `st.video(URL)` côté Streamlit.

## Démarrage local
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export STREAMLIT_SECRETS='{"database":{"url":"postgresql://...sslmode=require"}}'
streamlit run Home.py
```

## Déploiement

Secrets (DB, clés API) via Streamlit Cloud / GitHub Secrets.
Ne pas committer de secrets (voir section sécurité).

Sécurité

Les clés API sont stockées en secrets (CI/Cloud).
En cas de fuite : rotation immédiate + purge d’historique Git. (Guide GitHub)