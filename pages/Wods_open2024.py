import streamlit as st


# Config default settings of the page.


st.set_page_config(
    page_title="Wods open2024",
    layout="wide",
    page_icon="2024",
)
# st.sidebar.header("2024 Open Wods")

left_co, cent_co, last_co = st.columns(3)
with left_co:
    st.markdown(
        "**24.1**   For time:   - Time cap: 15 minutes",
    )
with cent_co:
    st.markdown("""
21 dumbbell snatches, arm 1 \n
21 lateral burpees over dumbbell \n
21 dumbbell snatches, arm 2 \n
21 lateral burpees over dumbbell \n
15 dumbbell snatches, arm 1 \n
15 lateral burpees over dumbbell \n
15 dumbbell snatches, arm 2 \n
15 lateral burpees over dumbbell \n
9 dumbbell snatches, arm 1 \n
9 lateral burpees over dumbbell \n
9 dumbbell snatches, arm 2 \n
9 lateral burpees over dumbbell \n""")
with last_co:
    st.markdown("""
♀️ 35-lb (15-kg) dumbbell

♂️ 50-lb (22.5-kg) dumbbell""")

st.markdown(
    "---"
)  # ----------------------------------------------------------------------------------------------------

left_co2, cent_co2, last_co2 = st.columns(3)

with left_co2:
    st.markdown(
        """**24.2** As many rounds and reps as possible in 20 minutes of: \n""",
    )

with cent_co2:
    st.markdown("""
300-meter row \n
10 deadlifts \n
50 double-unders \n
""")
with last_co2:
    st.markdown("""
♀️ 125 lb (56 kg)
                
♂️ 185 lb (83 kg)""")

st.markdown(
    "---"
)  # ----------------------------------------------------------------------------------------------------

left_co3, cent_co3, last_co3 = st.columns(3)

with left_co3:
    st.markdown(
        """**24.3** All for time: \n""",
    )

with cent_co3:
    st.markdown("""
5 rounds of: \n
10 thrusters, weight 1 \n
10 chest-to-bar pull-ups \n
Rest 1 minute, then: \n """)
    st.markdown("""\n""")
    st.markdown("""5 rounds of: \n
7 thrusters, weight 2 \n
7 bar muscle-ups \n
Time cap: 15 minutes \n""")
with last_co3:
    st.markdown("""
♀️ 165, 95 lb (29, 43 kg)
                
♂️ 95, 135 lb (43, 61 kg)""")
