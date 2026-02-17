# pages/Authentification.py
from datetime import datetime

import streamlit as st
from werkzeug.security import check_password_hash, generate_password_hash

from infra.db import bootstrap_after_create, get_engine, get_session
from infra.models import Base, User

# Création des tables via les modèles importés
Base.metadata.create_all(get_engine())
bootstrap_after_create()


def calculate_age_category(birth_year, current_year=datetime.now().year):
    age = current_year - birth_year
    if age <= 17:
        category = "Teenager"
    elif age < 35:
        category = "Elite"
    else:
        category = "Masters"
    return age, category


if st.session_state.get("user"):
    st.switch_page("Home.py")

st.subheader("S'inscrire")
with st.form(key="register_form"):
    name = st.text_input("Nom complet", key="register_name")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Mot de passe", type="password", key="register_password")
    sex = st.radio("Sexe", ["Male", "Female"], key="register_sex")
    birth_year = st.number_input(
        "Année de naissance",
        min_value=1950,
        max_value=datetime.now().year,
        key="register_birth_year",
    )
    level = st.radio("Niveau", ["Scaled", "RX"], key="register_level")
    submit_button = st.form_submit_button("S'inscrire")

    if submit_button:
        if not all([name, email, password, birth_year]):
            st.error("Veuillez remplir tous les champs.")
        else:
            age, category = calculate_age_category(birth_year)
            with get_session() as session:
                if session.query(User).filter_by(email=email).first():
                    st.error("Cet email est déjà enregistré. Veuillez vous connecter.")
                else:
                    hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
                    new_user = User(
                        name=name,
                        email=email,
                        password=hashed_password,
                        sex=sex,
                        birth_year=int(birth_year),
                        level=level,
                        category=category,
                        age=age,
                    )
                    session.add(new_user)
                    # FIX : commit explicite AVANT st.switch_page
                    # st.switch_page interrompt l'exécution immédiatement,
                    # empêchant le context manager de faire son commit automatique.
                    session.commit()
                    st.session_state["user"] = {"name": name, "email": email}
            st.switch_page("Home.py")

st.subheader("Ou se connecter")
with st.form(key="login_form"):
    email_login = st.text_input("Email", key="login_email")
    password_login = st.text_input("Mot de passe", type="password", key="login_password")
    submit_button_login = st.form_submit_button("Se connecter")

    if submit_button_login:
        with get_session(readonly=True) as session:
            user = session.query(User).filter_by(email=email_login).first()
            if user and check_password_hash(user.password, password_login):
                st.session_state["user"] = {"name": user.name, "email": user.email}
            else:
                st.error("Email ou mot de passe incorrect.")

        if st.session_state.get("user"):
            st.switch_page("Home.py")
