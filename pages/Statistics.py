import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from pages.Authentification import engine, User, Score
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

st.title("Statistiques des Scores des WODs")

# Chargement des scores
scores = (
    session.query(
        User.name, User.sex, User.level, User.category, Score.wod, Score.score
    )
    .join(Score, User.id == Score.user_id)
    .all()
)

data = pd.DataFrame(
    scores, columns=["Nom", "Sexe", "Niveau", "Catégorie", "WOD", "Score"]
)


def convert_to_seconds(time_str):
    """Convertit un temps format MM:SS ou HH:MM:SS en secondes."""
    try:
        parts = list(map(int, time_str.split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except (ValueError, AttributeError):
        return None
    return None


# Définition des WODs temps et répétitions
wods_time = ["25.2", "25.3"]
wods_rep = ["25.1"]

# Conversion des scores
data["Score"] = data.apply(
    lambda row: convert_to_seconds(row["Score"])
    if row["WOD"] in wods_time
    else pd.to_numeric(row["Score"], errors="coerce"),
    axis=1,
)

st.subheader("Statistiques par WOD")
wod_selected = st.selectbox("Choisissez un WOD", ["25.1", "25.2", "25.3"], index=0)

subset = data[data["WOD"] == wod_selected]
if not subset.empty:
    # Graphique des percentiles
    percentiles = np.arange(0, 101, 10)
    male_scores = subset[subset["Sexe"] == "Male"]["Score"].dropna()
    female_scores = subset[subset["Sexe"] == "Female"]["Score"].dropna()

    male_percentiles = (
        np.percentile(male_scores, 100 - percentiles)
        if not male_scores.empty
        else np.zeros_like(percentiles)
    )
    female_percentiles = (
        np.percentile(female_scores, 100 - percentiles)
        if not female_scores.empty
        else np.zeros_like(percentiles)
    )

    df_plot = pd.DataFrame(
        {
            "Percentiles": percentiles.tolist() * 2,
            "Score": np.concatenate([male_percentiles, female_percentiles]),
            "Sexe": ["Hommes"] * len(percentiles) + ["Femmes"] * len(percentiles),
        }
    )

    fig = px.line(
        df_plot,
        x="Percentiles",
        y="Score",
        color="Sexe",
        markers=True,
        title=f"Distribution des Scores - {wod_selected}",
        color_discrete_map={"Hommes": "#89b385", "Femmes": "#dcaa78"},
    )
    st.plotly_chart(fig)

    # Moyennes et Time Cap
    if wod_selected in wods_time:
        st.subheader("Statistiques Temps")
        male_mean = male_scores.mean() if not male_scores.empty else 0
        female_mean = female_scores.mean() if not female_scores.empty else 0
        time_cap = 900  # Exemple : 15 minutes
        time_cap_male = (
            (male_scores >= time_cap).mean() * 100 if not male_scores.empty else 0
        )
        time_cap_female = (
            (female_scores >= time_cap).mean() * 100 if not female_scores.empty else 0
        )

        st.write(f"Temps moyen Hommes : {male_mean:.2f} secondes")
        st.write(f"Temps moyen Femmes : {female_mean:.2f} secondes")
        st.write(f"Hommes terminant avant time cap : {100 - time_cap_male:.2f}%")
        st.write(f"Femmes terminant avant time cap : {100 - time_cap_female:.2f}%")
    else:
        st.subheader("Statistiques Répétitions")
        male_mean = male_scores.mean() if not male_scores.empty else 0
        female_mean = female_scores.mean() if not female_scores.empty else 0

        st.write(f"Répétitions moyennes Hommes : {male_mean:.0f}")
        st.write(f"Répétitions moyennes Femmes : {female_mean:.0f}")

    # Répartition des participants par sexe et niveau
    st.subheader("Répartition des Participants par Sexe et Niveau")
    gender_level_count = (
        subset.groupby(["Sexe", "Niveau"]).size().reset_index(name="Nombre")
    )

    fig_level = px.bar(
        gender_level_count,
        x="Niveau",
        y="Nombre",
        color="Sexe",
        barmode="group",
        title="Répartition par sexe et niveau",
        labels={"Niveau": "Niveau", "Nombre": "Nombre de participants"},
        color_discrete_map={"Male": "#89b385", "Female": "#dcaa78"},
    )
    st.plotly_chart(fig_level)
