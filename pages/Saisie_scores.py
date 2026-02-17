# pages/Saisie_scores.py

import streamlit as st

# Assurez-vous que auth_utils.py est à la racine de votre projet
from auth_utils import is_authenticated, show_auth_status

# Affiche le statut de connexion dans la sidebar au début de chaque page
show_auth_status()

# --- Protection de la page ---
# Si l'utilisateur n'est pas connecté, on arrête l'exécution de la page ici
if not is_authenticated():
    st.warning("Veuillez vous connecter pour accéder à cette page.")
    st.stop()  # Très important: arrête l'exécution du script

# --- Contenu de la page de saisie des scores (uniquement visible si connecté) ---
st.title("Saisie des Scores")
st.write(f"Bonjour {st.session_state.user['name']}, saisissez vos scores ici.")

# Exemple de formulaire
with st.form("score_form"):
    wod = st.selectbox("Choisissez le WOD", ["26.1", "26.2", "26.3"])
    score = st.text_input("Votre score (ex: 12:34 ou 150)")
    submitted = st.form_submit_button("Enregistrer le score")
    if submitted:
        # Ici, vous ajouteriez la logique pour sauvegarder le score en base de données
        st.success(f"Score '{score}' pour le WOD {wod} enregistré !")
