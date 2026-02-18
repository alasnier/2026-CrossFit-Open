# Home.py
import streamlit as st

from auth_utils import show_auth_status

st.set_page_config(
    page_title="2026 Crossfit Games Open",
    layout="wide",
    page_icon="💪",
)

show_auth_status()


left_title, center_title, right_title = st.columns(3)

with center_title:
    st.header("2026 CrossFit Games Open")
    st.markdown("Alex Lasnier - [LinkedIn](https://www.linkedin.com/in/alex-lasnier)")

    st.subheader("3 WEEKS - 3 WORKOUTS")
    st.markdown(
        "Workouts are released on Thursdays at 12 p.m. (PT) / 09 p.m. (Paris Hour)."
        "\n\n"
        "Scores are due by Monday at 5 p.m. (PT) / 2 a.m. (Paris Hour)."
    )

left_co, last_co = st.columns(2)

image_height = "500px"

with left_co:
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; align-items: center; height: {image_height};">
            <img src="https://crossfitgrandduc.com/wp-content/themes/grandduc/assets/img/crossfitgrandduc/crossfit-grandduc-hyrox.jpg" style="max-height: 100%; max-width: 100%; object-fit: contain;">
        </div>
        """,
        unsafe_allow_html=True,
    )
with last_co:
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; align-items: center; height: {image_height};">
            <img src="https://res.cloudinary.com/keystone-demo/image/upload/v1767612050/crossfit-open-2026.png" style="max-height: 100%; max-width: 100%; object-fit: contain;">
        </div>
        """,
        unsafe_allow_html=True,
    )

left_subtitle, center_subtitle, right_ubtitle = st.columns(3)

with center_subtitle:
    st.header("Next stage ⇒ Semifinals")
    st.markdown("The top athletes and teams from the Open.")
