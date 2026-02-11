import streamlit as st

from infra.db import get_session
from pages.Authentification import Score, User, Wod

st.title("Classement des Athlètes")

sex_selected = st.selectbox("Sexe", ["Male", "Female"], index=0)
level_selected = st.selectbox("Niveau", ["RX", "Scaled", "Coach"], index=0)
wod_selected = st.selectbox("Choisissez le WOD", ["Overall", "26.1", "26.2", "26.3"])


def _score_to_seconds(score_str: str) -> int | None:
    try:
        parts = list(map(int, score_str.split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        return None
    return None


def _get_wod(wod: str):
    with get_session(readonly=True) as s:
        return s.query(Wod).filter(Wod.wod == wod).first()


def calculer_classement(wod: str, sex: str, level: str):
    with get_session(readonly=True) as s:
        rows = (
            s.query(User.name, User.level, User.sex, Score.score)
            .join(Score, User.id == Score.user_id)
            .filter(Score.wod == wod, User.sex == sex, User.level == level)
            .all()
        )

    if not rows:
        return {}, {}

    wod_meta = _get_wod(wod)
    wod_type = wod_meta.type if wod_meta else "reps"

    classement, raw_scores = {}, {}
    for name, level, sex, score in rows:
        raw_scores.setdefault((name, level, sex), {})[wod] = score
        if wod_type == "time":
            secs = _score_to_seconds(score)
            classement.setdefault((level, sex), []).append(
                (name, secs if secs is not None else 10**9)
            )
        else:
            try:
                classement.setdefault((level, sex), []).append((name, int(score)))
            except Exception:
                classement.setdefault((level, sex), []).append((name, 0))

    for key in classement:
        if wod_type == "time":
            classement[key] = sorted(classement[key], key=lambda x: x[1])  # ASC
        else:
            classement[key] = sorted(classement[key], key=lambda x: x[1], reverse=True)  # DESC
    return classement, raw_scores


if wod_selected == "Overall":
    general_classement, scores_details = {}, {}
    for wod in ["26.1", "26.2", "26.3"]:
        wod_classement, wod_scores = calculer_classement(wod, sex_selected, level_selected)
        for (level, sex), athletes in wod_classement.items():
            for i, (name, _) in enumerate(athletes):
                general_classement.setdefault((name, level, sex), 0)
                general_classement[(name, level, sex)] += i + 1
                scores_details.setdefault((name, level, sex), {}).update(
                    wod_scores.get((name, level, sex), {})
                )

    sorted_general = sorted(general_classement.items(), key=lambda x: x[1])
    st.table(
        {
            "Place": [i + 1 for i in range(len(sorted_general))],
            "Nom": [c[0][0] for c in sorted_general],
            "Niveau": [c[0][1] for c in sorted_general],
            "Sexe": [c[0][2] for c in sorted_general],
            "26.1": [scores_details[c[0]].get("26.1", "-") for c in sorted_general],
            "26.2": [scores_details[c[0]].get("26.2", "-") for c in sorted_general],
            "26.3": [scores_details[c[0]].get("26.3", "-") for c in sorted_general],
            "Points Totaux": [c[1] for c in sorted_general],
        }
    )
else:
    classement, scores_details = calculer_classement(wod_selected, sex_selected, level_selected)
    for (level, sex), athletes in classement.items():
        st.subheader(f"Classement {level} - {sex}")
        sorted_classement = [
            (name, scores_details[(name, level, sex)][wod_selected]) for name, _ in athletes
        ]
        st.table(
            {
                "Place": [i + 1 for i in range(len(sorted_classement))],
                "Nom": [c[0] for c in sorted_classement],
                "Score": [c[1] for c in sorted_classement],
                "Points": [i + 1 for i in range(len(sorted_classement))],
            }
        )
