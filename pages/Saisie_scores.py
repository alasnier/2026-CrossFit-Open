# pages/Saisie_scores.py
import re

import streamlit as st

from auth_utils import is_authenticated, show_auth_status
from infra.db import get_session
from infra.models import Score, User, Wod

show_auth_status()

if not is_authenticated():
    st.warning("Veuillez vous connecter pour accéder à cette page.")
    st.stop()

st.title("Saisie des Scores des WODs")

user = st.session_state.get("user")

with get_session(readonly=True) as s:
    user_db = s.query(User).filter_by(email=user["email"]).first()
    user_id = user_db.id if user_db else None

if not user_id:
    st.warning("Utilisateur introuvable — reconnectez-vous.")
    st.stop()

wod_descriptions = {
    "26.1": """
**26.1** AMRAP 15 minutes
- 3 lateral burpees over the dumbbell
- 3 dumbbell hang clean-to-overheads
- 30-foot walking lunge (2 x 15 feet)

**After completing each round, add 3 reps to the burpees and hang clean-to-overheads.**

♀️ 35-lb (15-kg) dumbbell / ♂️ 50-lb (22.5-kg) dumbbell
""",
    "26.2": """
**26.2** (22.3 repeat) For time :
- 21 pull-ups / 42 double-unders / 21 thrusters (weight 1)
- 18 chest-to-bar pull-ups / 36 double-unders / 18 thrusters (weight 2)
- 15 bar muscle-ups / 30 double-unders / 15 thrusters (weight 3)

**Time cap: 12 minutes**

♀️ 65, 75, 85 lb (29, 34, 38 kg) / ♂️ 95, 115, 135 lb (43, 52, 61 kg)
""",
    "26.3": """
**26.3** For time :
- 5 wall walks / 50-calorie row
- 5 wall walks / 25 deadlifts
- 5 wall walks / 25 cleans
- 5 wall walks / 25 snatches
- 5 wall walks / 50-calorie row

**Time cap: 20 minutes**

♀️ 155-lb deadlift, 85-lb clean, 65-lb snatch / ♂️ 225-lb deadlift, 135-lb clean, 95-lb snatch
""",
}

score_instructions = {
    "26.1": "🔥 **Score = nombre total de répétitions** (AMRAP 15 min).",
    "26.2": "⏱️ **Score = temps MM:SS** si fini avant le cap, sinon **CAP:XX** où XX = reps manquantes.",
    "26.3": "⏱️ **Score = temps MM:SS** si fini avant le cap, sinon **CAP:XX** où XX = reps manquantes.",
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


wod = st.selectbox("Sélectionner le WOD", ["26.1", "26.2", "26.3"])
st.markdown(f"### WOD {wod}")
st.markdown(wod_descriptions[wod])
st.markdown("---")
st.markdown(score_instructions.get(wod, ""))
st.markdown("---")

# Charger les métadonnées du WOD et le score existant
with get_session(readonly=True) as s:
    wod_meta = s.query(Wod).filter(Wod.wod == wod).first()
    wod_type = wod_meta.type if wod_meta else "reps"
    timecap = wod_meta.timecap_seconds if wod_meta else None
    existing = s.query(Score).filter_by(user_id=user_id, wod=wod).first()
    existing_score_str = existing.score if existing else None
    existing_score_id = existing.id if existing else None

if existing_score_str:
    st.warning(f"✅ Score actuel pour {wod} : **{existing_score_str}**")
    modify = st.checkbox("Modifier votre score ?")
else:
    modify = True

if modify:
    new_score = None

    if wod_type == "time":
        score_input = st.text_input(
            "Entrez votre score (format 'MM:SS' ou 'CAP:XX')",
            value=existing_score_str or "",
        )
        if score_input:
            seconds = normalize_time_score(score_input, timecap or 0)
            if seconds is None:
                st.error("❌ Format incorrect. Utilisez 'MM:SS' (ex: 09:45) ou 'CAP:XX' (ex: CAP:05).")
            else:
                new_score = score_input.strip().upper()
    else:
        default_val = int(existing_score_str) if (existing_score_str and existing_score_str.isdigit()) else 0
        reps_val = st.number_input(
            "Entrez votre nombre de répétitions",
            min_value=0,
            step=1,
            value=default_val,
        )
        new_score = str(int(reps_val))

    label_btn = "Mettre à jour" if existing_score_id else "Enregistrer"
    if st.button(label_btn):
        if new_score:
            with get_session() as s:
                if existing_score_id:
                    # FIX : recharger l'objet dans la nouvelle session, pas l'ancien
                    score_obj = s.query(Score).filter_by(id=existing_score_id).first()
                    if score_obj:
                        score_obj.score = new_score
                else:
                    s.add(Score(user_id=user_id, wod=wod, score=new_score))
                s.commit()
            st.success(f"✅ Score **{new_score}** enregistré pour le WOD {wod} !")
            st.rerun()
        else:
            st.error("Veuillez entrer un score valide avant d'enregistrer.")
