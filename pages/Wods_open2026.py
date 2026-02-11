import streamlit as st

st.set_page_config(page_title="WODs Open 2026", layout="wide", page_icon="📅")

st.title("CrossFit Open 2026 — WODs")
st.info(
    "Les WODs 26.1, 26.2 et 26.3 seront publiés entre **le 26 février et le 16 mars 2026**.\n"
    "Reviens ici chaque jeudi soir (Paris) pour découvrir le nouveau WOD !"
)

cols = st.columns(3)
for i, wod in enumerate(["26.1", "26.2", "26.3"]):
    with cols[i]:
        st.subheader(f"{wod} — à venir")
        st.caption("Description officielle publiée le jeudi concerné.")
        st.progress(0, text="Décompte à venir")
