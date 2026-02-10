import streamlit as st
from pages.Authentification import engine, User, Score
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Connexion à la base de données
Session = sessionmaker(bind=engine)
session = Session()

# Titre de la page
st.title("Saisie des Scores des WODs")

# Récupération de l'utilisateur dans la session
user = st.session_state.get("user")  # Récupère l'objet utilisateur stocké
if not user:
    st.warning(
        "Veuillez vous connecter pour enregistrer votre score => onglet Authentification (Barre Laterale Gauche)"
    )
    st.stop()

user_email = user["email"]
user = session.query(User).filter_by(email=user_email).first()

wod_descriptions = {
    "25.1": """
**25.1** AMRAP 15 minutes \n
3 lateral burpees over the dumbbell\n
3 dumbbell hang clean-to-overheads\n
30-foot walking lunge (2 x 15 feet)\n
**After completing each round, add 3 reps to the burpees and hang clean-to-overheads.**\n
♀️ 35-lb (15-kg) dumbbell / ♂️ 50-lb (22.5-kg) dumbbell
""",
    "25.2": """
**25.2** (22.3 repeat) For time :\n
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
    "25.3": """
**25.3** For time :\n
5 wall walks\n
50-calorie row\n
5 wall walks\n
25 deadlifts\n
5 wall walks\n
25 cleans\n
5 wall walks\n
25 snatches\n
5 wall walks\n
50-calorie row\n
**Time cap: 20 minutes**\n
♀️ 155-lb (70-kg) deadlift, 85-lb (38-kg) clean, 65-lb (29-kg) snatch  / ♂️ 225-lb (102-kg) deadlift, 135-lb (61-kg) clean, 95-lb (43-kg) snatch
""",
}

score_instructions = {
    "25.3": """
    🏋️ **Comment entrer votre score ?**
    - Si vous terminez avant la limite de temps (20 minutes), entrez votre temps sous le format **MM:SS**.
    - Si vous n’avez pas terminé avant le time cap :
      - **Entrez "20:XX"**, où **XX = 1 seconde par répétition manquante**.
      - Exemple : il vous restait 5 répétitions à faire → votre score est **20:05**.
    """,
    "25.1": """
🔥 **Comment entrer votre score ?**  
- Ce WOD est un **AMRAP de 15 minutes**.  
- Entrez **le nombre total de répétitions effectuées** pendant les 20 minutes.
""",
}


# Si l'utilisateur est trouvé, afficher les options de saisie
if user:
    wod = st.selectbox("Sélectionner le WOD", ["25.3"])
    st.markdown(f"### WOD {wod}")
    st.markdown(wod_descriptions[wod])
    st.markdown("---")
    st.markdown(score_instructions[wod])
    st.markdown("---")

    # Vérifier si l'utilisateur a déjà enregistré un score
    existing_score = session.query(Score).filter_by(user_id=user.id, wod=wod).first()

    if existing_score:
        st.warning(f"Score actuel pour {wod} : {existing_score.score}")
        modify = st.checkbox("Modifier votre score ?")
    else:
        modify = True

    if modify:
        new_score = None
        if wod in ["25.3"]:
            score_input = st.text_input(
                "Entrez votre score (format MM:SS)",
                existing_score.score if existing_score else "",
            )
            try:
                new_score = datetime.strptime(score_input, "%M:%S").strftime("%M:%S")
            except ValueError:
                st.error("Format de temps incorrect. Utilisez MM:SS.")
        elif wod == "25.1":
            new_score = st.number_input(
                "Entrez votre nombre de répétitions",
                min_value=0,
                step=1,
                value=int(existing_score.score) if existing_score else 0,
            )

        if st.button("Enregistrer" if not existing_score else "Mettre à jour"):
            if new_score:
                if existing_score:
                    existing_score.score = str(new_score)
                else:
                    new_score_entry = Score(
                        user_id=user.id, wod=wod, score=str(new_score)
                    )
                    session.add(new_score_entry)
                session.commit()
                st.success("Score enregistré avec succès !")
else:
    st.warning(
        "Veuillez vous connecter pour enregistrer votre score => onglet Authentification (Barre Laterale Gauche)"
    )
