import re

import streamlit as st

from infra.db import get_session
from pages.Authentification import Score, User, Wod

st.title("Saisie des Scores des WODs")

user = st.session_state.get("user")
if not user:
    st.warning(
        "Veuillez vous connecter pour enregistrer votre score => onglet Authentification (Barre Laterale Gauche)"
    )
    st.stop()

with get_session(readonly=True) as s:
    user_db = s.query(User).filter_by(email=user["email"]).first()

wod_descriptions = {
    "26.1": """
**26.1** AMRAP 15 minutes \n
3 lateral burpees over the dumbbell\n
3 dumbbell hang clean-to-overheads\n
30-foot walking lunge (2 x 15 feet)\n
**After completing each round, add 3 reps to the burpees and hang clean-to-overheads.**\n
♀️ 35-lb (15-kg) dumbbell / ♂️ 50-lb (22.5-kg) dumbbell
""",
    "26.2": """
**26.2** (22.3 repeat) For time :\n
21 pull-ups\n
42 double-unders\n
21 thrusters (weight 1)\n
18 chest-to-bar pull-ups\n
36 double-unders\n
18 thrusters (weight 2)\n
15 bar muscle-ups\n
30 double-unders\n
15 thrusters (weight 3) \n
**Time cap: 12 minutes**\n
♀️ 65, 75, 85 lb (29, 34, 38 kg)  / ♂️ 95, 115, 135 lb (43, 52, 61 kg)
""",
    "26.3": """
**26.3** For time :\n
5 wall walks\n
50-calorie row\n
5 wall walks\n
26 deadlifts\n
5 wall walks\n
26 cleans\n
5 wall walks\n
26 snatches\n
5 wall walks\n
50-calorie row\n
**Time cap: 20 minutes**\n
♀️ 155-lb (70-kg) deadlift, 85-lb (38-kg) clean, 65-lb (29-kg) snatch  / ♂️ 225-lb (102-kg) deadlift, 135-lb (61-kg) clean, 95-lb (43-kg) snatch
""",
}

score_instructions = {
    "26.3": """
    🏋️ **Comment entrer votre score ?**
    - Si vous terminez avant la limite de temps, entrez **MM:SS**.
    - Si vous n’avez pas terminé avant le time cap :
      - **Entrez "CAP:XX"**, où **XX = 1 seconde par répétition manquante** (ex: 12' => CAP:05 => 725 s si cap=720).
    """,
    "26.1": """
🔥 **Comment entrer votre score ?**  
- Ce WOD est un **AMRAP de 15 minutes**.  
- Entrez **le nombre total de répétitions**.
""",
}


def normalize_time_score(input_str: str, timecap_seconds: int) -> int | None:
    if not input_str:
        return None
    s = input_str.strip().upper()
    m = re.match(r"^CAP:(\d{1,3})$", s)
    if m:
        return timecap_seconds + int(m.group(1))
    try:
        parts = list(map(int, s.split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        return None
    return None


if user_db:
    wod = st.selectbox("Sélectionner le WOD", ["26.1", "26.2", "26.3"])
    st.markdown(f"### WOD {wod}")
    st.markdown(wod_descriptions[wod])
    st.markdown("---")
    st.markdown(score_instructions.get(wod, ""))
    st.markdown("---")

    with get_session(readonly=True) as s:
        wod_meta = s.query(Wod).filter(Wod.wod == wod).first()
        existing_score = s.query(Score).filter_by(user_id=user_db.id, wod=wod).first()

    if existing_score:
        st.warning(f"Score actuel pour {wod} : {existing_score.score}")
        modify = st.checkbox("Modifier votre score ?")
    else:
        modify = True

    if modify:
        new_score = None
        if wod_meta and wod_meta.type == "time":
            score_input = st.text_input(
                "Entrez votre score (format 'MM:SS' ou 'CAP:XX')",
                existing_score.score if existing_score else "",
            )
            seconds = normalize_time_score(score_input, wod_meta.timecap_seconds or 0)
            if score_input and seconds is None:
                st.error("Format incorrect. Utilisez 'MM:SS' ou 'CAP:XX'.")
            new_score = score_input if seconds is not None else None
        else:
            reps_val = st.number_input(
                "Entrez votre nombre de répétitions",
                min_value=0,
                step=1,
                value=int(existing_score.score)
                if (existing_score and existing_score.score.isdigit())
                else 0,
            )
            new_score = str(reps_val)

        if st.button("Enregistrer" if not existing_score else "Mettre à jour"):
            if new_score:
                with get_session() as s:
                    if existing_score:
                        existing_score.score = str(new_score)
                    else:
                        s.add(Score(user_id=user_db.id, wod=wod, score=str(new_score)))
                st.success("Score enregistré avec succès !")
else:
    st.warning("Utilisateur introuvable — reconnectez-vous.")
