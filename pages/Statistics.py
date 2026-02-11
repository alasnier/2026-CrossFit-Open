import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from infra.db import get_session
from pages.Authentification import Score, User, Wod

st.title("Statistiques des Scores des WODs")


def normalize_for_stats(value: str, wod_type: str, timecap: int | None) -> float | None:
    """
    - 'time' : renvoie des secondes (float), comprend 'MM:SS' et 'CAP:XX' (cap + XX).
    - 'reps' : renvoie un entier (float) représentant les répétitions.
    """
    if wod_type == "time":
        if not value:
            return None
        s = value.strip().upper()
        if s.startswith("CAP:"):
            try:
                over = int(s.split(":")[1])
                return float((timecap or 0) + over)
            except Exception:
                return None
        try:
            parts = list(map(int, s.split(":")))
            if len(parts) == 2:
                return float(parts[0] * 60 + parts[1])
            elif len(parts) == 3:
                return float(parts[0] * 3600 + parts[1] * 60 + parts[2])
        except Exception:
            return None
        return None
    else:
        try:
            return float(int(value))
        except Exception:
            return None


# Charger toutes les lignes nécessaires avec jointure Wod
with get_session(readonly=True) as s:
    rows = (
        s.query(
            User.name,
            User.sex,
            User.level,
            User.category,
            Score.wod,
            Score.score,
            Wod.type,
            Wod.timecap_seconds,
        )
        .join(Score, User.id == Score.user_id)
        .join(Wod, Wod.wod == Score.wod)
        .all()
    )

if not rows:
    st.info("Aucune donnée.")
    st.stop()

data = pd.DataFrame(
    rows, columns=["Nom", "Sexe", "Niveau", "Catégorie", "WOD", "ScoreBrut", "Type", "CapSec"]
)
# Normaliser en valeur numérique exploitable
data["Score"] = data.apply(
    lambda r: normalize_for_stats(r["ScoreBrut"], r["Type"], r["CapSec"]), axis=1
)

st.subheader("Statistiques par WOD")
# WODs disponibles depuis la table
wods = sorted(data["WOD"].unique().tolist())
wod_selected = st.selectbox("Choisissez un WOD", wods, index=0 if wods else None)

subset = data[(data["WOD"] == wod_selected)].copy()
if subset.empty:
    st.info("Aucune donnée pour ce WOD.")
    st.stop()

# Percentiles séparés H/F
percentiles = np.arange(0, 101, 10)
male = subset[subset["Sexe"] == "Male"]["Score"].dropna()
female = subset[subset["Sexe"] == "Female"]["Score"].dropna()

# Pour les 'time', score = secondes => percentiles inversés pour tracer des 'meilleurs = plus bas'
is_time = subset["Type"].iloc[0] == "time"
if is_time:
    male_percentiles = (
        np.percentile(male, 100 - percentiles) if not male.empty else np.zeros_like(percentiles)
    )
    female_percentiles = (
        np.percentile(female, 100 - percentiles) if not female.empty else np.zeros_like(percentiles)
    )
else:
    male_percentiles = (
        np.percentile(male, percentiles) if not male.empty else np.zeros_like(percentiles)
    )
    female_percentiles = (
        np.percentile(female, percentiles) if not female.empty else np.zeros_like(percentiles)
    )

df_plot = pd.DataFrame(
    {
        "Percentiles": percentiles.tolist() * 2,
        "Score": np.concatenate([male_percentiles, female_percentiles]),
        "Sexe": ["Hommes"] * len(percentiles) + ["Femmes"] * len(percentiles),
    }
)

title = f"Distribution des Scores - {wod_selected} ({'temps' if is_time else 'répétitions'})"
fig = px.line(
    df_plot,
    x="Percentiles",
    y="Score",
    color="Sexe",
    markers=True,
    title=title,
    color_discrete_map={"Hommes": "#89b385", "Femmes": "#dcaa78"},
)
st.plotly_chart(fig)

# Statistiques complémentaires
if is_time:
    st.subheader("Statistiques Temps")
    male_mean = male.mean() if not male.empty else 0
    female_mean = female.mean() if not female.empty else 0
    time_cap = int(subset["CapSec"].iloc[0] or 0)
    pct_m_before = (male < time_cap).mean() * 100 if (time_cap and not male.empty) else 0
    pct_f_before = (female < time_cap).mean() * 100 if (time_cap and not female.empty) else 0

    st.write(f"Temps moyen Hommes : {male_mean:.2f} s")
    st.write(f"Temps moyen Femmes : {female_mean:.2f} s")
    if time_cap:
        st.write(f"Hommes terminant avant cap : {pct_m_before:.2f}%")
        st.write(f"Femmes terminant avant cap : {pct_f_before:.2f}%")
else:
    st.subheader("Statistiques Répétitions")
    male_mean = male.mean() if not male.empty else 0
    female_mean = female.mean() if not female.empty else 0
    st.write(f"Répétitions moyennes Hommes : {male_mean:.0f}")
    st.write(f"Répétitions moyennes Femmes : {female_mean:.0f}")

# Répartition des participants par sexe et niveau
st.subheader("Répartition des Participants par Sexe et Niveau")
gender_level_count = subset.groupby(["Sexe", "Niveau"]).size().reset_index(name="Nombre")
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
