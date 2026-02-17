import numpy as np
import pandas as pd
import plotly.express as px

# Home.py
import streamlit as st

from auth_utils import is_authenticated, show_auth_status

# Affiche le statut de connexion dans la sidebar au début de chaque page
show_auth_status()

# --- Protection de la page ---
# Si l'utilisateur n'est pas connecté, on arrête l'exécution de la page ici
if not is_authenticated():
    st.warning("Veuillez vous connecter pour accéder à cette page.")
    st.stop()

# --- Contenu de la page d'accueil (uniquement visible si connecté) ---
st.title("Page d'Accueil")
st.write(f"Bienvenue sur la page d'accueil, {st.session_state.user['name']}!")

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


# ── Chargement des données ───────────────────────────────────────────────────
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
    st.info("Aucune donnée disponible — soyez le premier à enregistrer un score !")
    st.stop()

data = pd.DataFrame(
    rows,
    columns=["Nom", "Sexe", "Niveau", "Catégorie", "WOD", "ScoreBrut", "Type", "CapSec"],
)
data["Score"] = data.apply(
    lambda r: normalize_for_stats(r["ScoreBrut"], r["Type"], r["CapSec"]), axis=1
)

# ── Sélection du WOD ────────────────────────────────────────────────────────
st.subheader("Statistiques par WOD")
wods = sorted(data["WOD"].unique().tolist())
wod_selected = st.selectbox("Choisissez un WOD", wods)

subset = data[data["WOD"] == wod_selected].copy()
if subset.empty:
    st.info("Aucune donnée pour ce WOD.")
    st.stop()

# ── Distribution par percentiles ────────────────────────────────────────────
percentiles = np.arange(0, 101, 10)
male = subset[subset["Sexe"] == "Male"]["Score"].dropna()
female = subset[subset["Sexe"] == "Female"]["Score"].dropna()

is_time = subset["Type"].iloc[0] == "time"

# Pour les WODs 'time' : meilleur score = plus petit → inverser les percentiles
# afin que le graphe aille "du meilleur (bas) au moins bon (haut)"
if is_time:
    male_percentiles = (
        np.percentile(male, 100 - percentiles)
        if not male.empty
        else np.zeros_like(percentiles, dtype=float)
    )
    female_percentiles = (
        np.percentile(female, 100 - percentiles)
        if not female.empty
        else np.zeros_like(percentiles, dtype=float)
    )
else:
    male_percentiles = (
        np.percentile(male, percentiles)
        if not male.empty
        else np.zeros_like(percentiles, dtype=float)
    )
    female_percentiles = (
        np.percentile(female, percentiles)
        if not female.empty
        else np.zeros_like(percentiles, dtype=float)
    )

df_plot = pd.DataFrame(
    {
        "Percentiles": percentiles.tolist() * 2,
        "Score": np.concatenate([male_percentiles, female_percentiles]),
        "Sexe": ["Hommes"] * len(percentiles) + ["Femmes"] * len(percentiles),
    }
)

y_label = "Temps (secondes)" if is_time else "Répétitions"
title = f"Distribution des Scores — {wod_selected} ({'temps' if is_time else 'répétitions'})"

fig = px.line(
    df_plot,
    x="Percentiles",
    y="Score",
    color="Sexe",
    markers=True,
    title=title,
    labels={"Score": y_label, "Percentiles": "Percentile (%)"},
    color_discrete_map={"Hommes": "#89b385", "Femmes": "#dcaa78"},
)
st.plotly_chart(fig, use_container_width=True)

# ── Statistiques complémentaires ────────────────────────────────────────────
if is_time:
    st.subheader("Statistiques Temps")
    time_cap = int(subset["CapSec"].iloc[0] or 0)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Temps moyen Hommes", f"{male.mean():.0f} s" if not male.empty else "—")
        if time_cap and not male.empty:
            pct = (male < time_cap).mean() * 100
            st.metric("Hommes terminant avant cap", f"{pct:.1f}%")
    with col2:
        st.metric("Temps moyen Femmes", f"{female.mean():.0f} s" if not female.empty else "—")
        if time_cap and not female.empty:
            pct = (female < time_cap).mean() * 100
            st.metric("Femmes terminant avant cap", f"{pct:.1f}%")

    if time_cap:
        st.caption(f"Time cap : {time_cap // 60} min ({time_cap} s)")
else:
    st.subheader("Statistiques Répétitions")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Reps moyennes Hommes", f"{male.mean():.0f}" if not male.empty else "—")
        st.metric("Meilleur score Hommes", f"{male.max():.0f}" if not male.empty else "—")
    with col2:
        st.metric("Reps moyennes Femmes", f"{female.mean():.0f}" if not female.empty else "—")
        st.metric("Meilleur score Femmes", f"{female.max():.0f}" if not female.empty else "—")

# ── Répartition par sexe et niveau ──────────────────────────────────────────
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
st.plotly_chart(fig_level, use_container_width=True)

# ── Nombre total de participants ─────────────────────────────────────────────
st.caption(
    f"Total participants sur {wod_selected} : "
    f"{len(subset['Nom'].unique())} athlètes "
    f"({len(male)} H / {len(female)} F)"
)
