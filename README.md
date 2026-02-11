# 2026 CrossFit Games Open — Box Interne

Application de suivi des scores pour l'Open CrossFit 2026, optimisée pour une gestion interne en box.

## Fonctionnalités
- **Authentification** : Inscription et gestion de profil (Sexe, Niveau RX/Scaled, Catégorie d'âge).
- **Saisie des Scores** : Interface dédiée pour les WODs 26.1, 26.2 et 26.3 avec validation des formats (Reps ou Temps/CAP).
- **Classement Dynamique** : Leaderboard filtrable par sexe et niveau, incluant un classement général (Overall) basé sur les points.
- **Statistiques Avancées** : Visualisation de la distribution des scores (percentiles) et analyses par catégorie.

## Stack Technique
- **Framework** : [Streamlit](https://streamlit.io)
- **Base de Données** : [Neon Postgres 17](https://neon.tech) (Serverless)
- **ORM** : SQLAlchemy 2.0
- **Analyse de données** : Pandas, Numpy, Plotly

## Configuration & Déploiement

### Base de données
L'application utilise Neon Postgres. La structure des tables et les données initiales (WODs) sont créées automatiquement au premier démarrage.

**Secrets requis (Streamlit Cloud ou .streamlit/secrets.toml) :**
```toml
[database]
url = "postgresql://user:password@ep-xxx.aws.neon.tech/neondb?sslmode=require"
```

### Installation locale
1. Cloner le dépôt.
2. Installer les dépendances : `pip install -r requirements.txt` (généré via `pip-compile requirements.in`).
3. Configurer la variable d'environnement `DATABASE_URL` ou le fichier `secrets.toml`.
4. Lancer : `streamlit run Home.py`.

## Sécurité
- Mots de passe hachés via PBKDF2 (Werkzeug).
- Connexions DB sécurisées (SSL requis).
- Isolation des sessions via SQLAlchemy.
