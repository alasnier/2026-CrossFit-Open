# Home.py
import streamlit as st

from auth_utils import show_auth_status

st.set_page_config(
    page_title="2026 Crossfit Games Open",
    layout="wide",
    page_icon="💪",
)

show_auth_status()

st.header("2026 CrossFit Games Open")
st.markdown("Alex Lasnier - [LinkedIn](https://www.linkedin.com/in/alex-lasnier)")

st.subheader("3 WEEKS - 3 WORKOUTS")
st.markdown(
    "Workouts are released on Thursdays at 12 p.m. (PT) / 09 p.m. (Paris Hour) and scores are due by Monday at 5 p.m. (PT) / 2 a.m. (Paris Hour)."
)

left_co, cent_co, last_co = st.columns(3)
with cent_co:
    st.image("crossfit-open-2026.png")

st.header("Next stage ⇒ Semifinals")
st.markdown("The top athletes and teams from the Open.")
