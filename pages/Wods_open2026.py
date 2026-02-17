import streamlit as st

from auth_utils import show_auth_status

# CORRECTION: Déplacer en haut
st.set_page_config(
    page_title="2026 Open WODs",
    layout="wide",
    page_icon="📅",
)

show_auth_status()


st.title("2026 Open WODs")
st.sidebar.header("2026 Open WODs")


st.info(
    "Les WODs 26.1, 26.2 et 26.3 seront publiés entre **le 26 février et le 16 mars 2026**.\n"
    "Reviens ici chaque jeudi soir (Paris) pour découvrir le nouveau WOD !"
)

cols = st.columns(3)
for i, wod in enumerate(["26.1", "26.2", "26.3"]):
    with cols[i]:
        st.subheader(f"{wod} — à venir")
        st.caption("Description officielle publiée le jeudi concerné.")
        st.progress(20, text="Décompte à venir")
