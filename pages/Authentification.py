from datetime import datetime

import streamlit as st
from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import declarative_base, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from infra.db import bootstrap_after_create, get_engine, get_session

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    sex = Column(String(10), nullable=False)
    birth_year = Column(Integer, nullable=False)
    level = Column(String(10), nullable=False)
    category = Column(String(20), nullable=False)
    age = Column(Integer, nullable=False)
    scores = relationship("Score", back_populates="user", cascade="all, delete")


class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wod = Column(String(10), nullable=False)  # '26.1' etc.
    score = Column(String(20), nullable=False)  # 'MM:SS' ou répétitions
    created_at = Column(TIMESTAMP, server_default=func.now())
    user = relationship("User", back_populates="scores")


class Wod(Base):
    __tablename__ = "wods"
    wod = Column(String(10), primary_key=True)  # '26.1'
    label = Column(String(100), nullable=False)
    type = Column(String(10), nullable=False)  # 'time' | 'reps'
    timecap_seconds = Column(Integer, nullable=True)  # cap en secondes


# Création des tables puis bootstrap auto (seed + index)
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


def login():
    if "user" not in st.session_state:
        st.session_state["user"] = None

    if st.session_state["user"] is None:
        st.subheader("Login / Register")

        with st.form(key="register_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            sex = st.radio("Sex", ["Male", "Female"])
            birth_year = st.number_input(
                "Year of Birth", min_value=1950, max_value=datetime.now().year
            )
            level = st.radio("Workout Level", ["Scaled", "RX"])
            submit_button = st.form_submit_button("Register")

            if submit_button:
                if not name or not email or not password or not birth_year:
                    st.error("Please fill in all the fields.")
                else:
                    age, category = calculate_age_category(birth_year)
                    with get_session() as session:
                        existing_user = session.query(User).filter_by(email=email).first()
                        if existing_user:
                            st.error("Email already registered. Please login.")
                        else:
                            hashed_password = generate_password_hash(
                                password, method="pbkdf2:sha256"
                            )
                            new_user = User(
                                name=name,
                                email=email,
                                password=hashed_password,
                                sex=sex,
                                birth_year=birth_year,
                                level=level,
                                category=category,
                                age=age,
                            )
                            session.add(new_user)
                            st.session_state["user"] = {
                                "name": name,
                                "email": email,
                                "sex": sex,
                                "birth_year": birth_year,
                                "level": level,
                                "category": category,
                                "age": age,
                            }
                            st.success(
                                f"Welcome {name}! You are categorized as {category} ({age} years old)."
                            )

        st.subheader("Or Login:")
        with st.form(key="login_form"):
            email_login = st.text_input("Email")
            password_login = st.text_input("Password", type="password")
            submit_button_login = st.form_submit_button("Login")

            if submit_button_login:
                with get_session(readonly=True) as session:
                    user = session.query(User).filter_by(email=email_login).first()
                    if user and check_password_hash(user.password, password_login):
                        st.session_state["user"] = {
                            "name": user.name,
                            "email": user.email,
                            "sex": user.sex,
                            "birth_year": user.birth_year,
                            "level": user.level,
                            "category": user.category,
                            "age": user.age,
                        }
                        st.success(f"Logged in as {user.name}")
                    else:
                        st.error("Invalid email or password. Please try again.")
    else:
        st.subheader(f"Hello {st.session_state['user']['name']}!")
        if st.button("Logout"):
            st.session_state["user"] = None
            st.success("Logged out successfully.")


login()


def change_password():
    st.subheader("Change Password if you want:")
    with get_session() as session:
        user = session.query(User).filter_by(email=st.session_state["user"]["email"]).first()
        if user:
            with st.form(key="change_password_form"):
                old_password = st.text_input("Old Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                submit_button = st.form_submit_button("Change Password")

                if submit_button:
                    if not old_password or not new_password or not confirm_password:
                        st.error("All fields are required.")
                    elif not check_password_hash(user.password, old_password):
                        st.error("Incorrect old password.")
                    elif new_password != confirm_password:
                        st.error("New passwords do not match.")
                    else:
                        user.password = generate_password_hash(new_password, method="pbkdf2:sha256")
                        st.success("Your password has been updated successfully!")


if st.session_state.get("user"):
    change_password()
