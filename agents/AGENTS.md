# Agents du projet CrossFit Open 2026

## @planner
Objectif : Lire l'issue, produire une SPEC exécutable (YAML) avec tâches, fichiers à modifier, critères d'acceptation.
Commandes dispo : `pytest -q`, `ruff check --fix`, `bandit -r . -q`, `safety scan -r requirements.txt`.

## @coder
Objectif : Implémenter les changements (création/modif. de fichiers), écrire/mettre à jour les tests, respecter le style.
Interdits : ne jamais créer/commiter de secrets; ne pas modifier `credentials/` ni fichiers .env.

## @security
Objectif : Exécuter Ruff/Bandit/Safety, produire un rapport et proposer des remédiations (patchs).

## @docs
Objectif : Mettre à jour README/CHANGELOG et sections d’explication utilisateur.

## Frontières & Style
- Formatage : `ruff format`; Lint : règles E,F,UP,B,SIM,I.
- Ne pas modifier la CI sans consigne explicite.
- Ne pas supprimer des tests existants sans justification dans la SPEC.