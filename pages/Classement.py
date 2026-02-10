import streamlit as st
from pages.Authentification import engine, User, Score
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

st.title("Classement des Athlètes")

# Filtres
sex_selected = st.selectbox("Sexe", ["Male", "Female"], index=0)
level_selected = st.selectbox("Niveau", ["RX", "Scaled", "Coach"], index=0)
wod_selected = st.selectbox("Choisissez le WOD", ["Overall", "25.1", "25.2", "25.3"])


# WODs triés par ordre croissant (temps)
wods_time = ["25.2", "25.3"]  # Liste des WODs temps (exemple)


# Fonction pour calculer les classements et récupérer les scores
def calculer_classement(wod, sex, level):
    scores = (
        session.query(User.name, User.level, User.sex, Score.score)
        .join(Score, User.id == Score.user_id)
        .filter(Score.wod == wod, User.sex == sex, User.level == level)
        .all()
    )

    if not scores:
        return {}, {}

    classement = {}
    raw_scores = {}
    for name, level, sex, score in scores:
        raw_scores.setdefault((name, level, sex), {})[wod] = score
        if ":" in score:  # Score au format temps (MM:SS)
            time_parts = list(map(int, score.split(":")))
            total_seconds = time_parts[0] * 60 + time_parts[1]
            classement.setdefault((level, sex), []).append((name, total_seconds))
        else:  # Score basé sur les répétitions
            classement.setdefault((level, sex), []).append((name, int(score)))

    # Appliquer le tri en fonction du WOD
    for key in classement:
        classement[key] = sorted(
            classement[key],
            key=lambda x: x[1],
            reverse=(
                wod not in wods_time
            ),  # Croissant pour les WODs temps, décroissant pour les répétitions
        )

    return classement, raw_scores


if wod_selected == "Overall":
    general_classement = {}
    scores_details = {}
    for wod in ["25.1", "25.2", "25.3"]:
        wod_classement, wod_scores = calculer_classement(
            wod, sex_selected, level_selected
        )
        for (level, sex), athletes in wod_classement.items():
            for i, (name, _) in enumerate(athletes):
                general_classement.setdefault((name, level, sex), 0)
                general_classement[(name, level, sex)] += i + 1  # Points cumulés
                scores_details.setdefault((name, level, sex), {}).update(
                    wod_scores.get((name, level, sex), {})
                )

    sorted_general_classement = sorted(general_classement.items(), key=lambda x: x[1])

    st.table(
        {
            "Place": [i + 1 for i in range(len(sorted_general_classement))],
            "Nom": [c[0][0] for c in sorted_general_classement],
            "Niveau": [c[0][1] for c in sorted_general_classement],
            "Sexe": [c[0][2] for c in sorted_general_classement],
            "25.1": [
                scores_details[c[0]].get("25.1", "-") for c in sorted_general_classement
            ],
            "25.2": [
                scores_details[c[0]].get("25.2", "-") for c in sorted_general_classement
            ],
            "25.3": [
                scores_details[c[0]].get("25.3", "-") for c in sorted_general_classement
            ],
            "Points Totaux": [c[1] for c in sorted_general_classement],
        }
    )
else:
    classement, scores_details = calculer_classement(
        wod_selected, sex_selected, level_selected
    )

    for (level, sex), athletes in classement.items():
        st.subheader(f"Classement {level} - {sex}")
        sorted_classement = [
            (name, scores_details[(name, level, sex)][wod_selected])
            for name, _ in athletes
        ]
        st.table(
            {
                "Place": [i + 1 for i in range(len(sorted_classement))],
                "Nom": [c[0] for c in sorted_classement],
                "Score": [c[1] for c in sorted_classement],
                "Points": [i + 1 for i in range(len(sorted_classement))],
            }
        )
