# auth_utils.py

import streamlit as st


def show_auth_status():
    """
    Affiche le statut de connexion dans la barre latérale.
    - Si l'utilisateur est connecté, affiche son nom et un bouton de déconnexion.
    - Si l'utilisateur n'est pas connecté, affiche un lien vers la page de connexion.
    """
    # Initialise la session si elle n'existe pas
    if "user" not in st.session_state:
        st.session_state.user = None

    # Logique d'affichage dans la barre latérale
    if st.session_state.user:
        st.sidebar.write(f"Connecté en tant que : **{st.session_state.user['name']}**")
        if st.sidebar.button("Se déconnecter"):
            st.session_state.user = None
            # Redirige vers la page de connexion après la déconnexion
            st.switch_page("pages/Authentification.py")
    else:
        st.sidebar.write("Vous n'êtes pas connecté.")
        st.sidebar.page_link("pages/Authentification.py", label="Se connecter / S'inscrire")


def is_authenticated():
    """Vérifie si un utilisateur est authentifié."""
    return st.session_state.user is not None
