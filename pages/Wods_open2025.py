import streamlit as st


# Config default settings of the page.


st.set_page_config(
    page_title="Wods open2025",
    layout="wide",
    page_icon="2025",
)

left_co, cent_co, last_co = st.columns(3)
with left_co:
    st.markdown(
        "**25.1**   As many rounds and reps as possible in 15 minutes of :",
    )
with cent_co:
    st.markdown("""
3 lateral burpees over the dumbbell \n
3 dumbbell hang clean-to-overheads \n
30-foot walking lunge (2 x 15 feet) \n
""")
    st.markdown("")
    st.markdown(
        "**After completing each round, add 3 reps to the burpees and hang clean-to-overheads.**"
    )
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
        "**25.2** (22.3 repeat) For time :",
    )
with cent_co2:
    st.markdown("""
21 pull-ups\n
42 double-unders\n
21 thrusters (weight 1)\n
18 chest-to-bar pull-ups\n
36 double-unders\n
18 thrusters (weight 2)\n
15 bar muscle-ups\n
30 double-unders\n
15 thrusters (weight 3) \n
""")
    st.markdown("")
    st.markdown("**Time cap: 12 minutes**")
with last_co2:
    st.markdown("""
♀️ 65, 75, 85 lb (29, 34, 38 kg)

♂️ 95, 115, 135 lb (43, 52, 61 kg)""")

st.markdown(
    "---"
)  # ----------------------------------------------------------------------------------------------------

left_co3, cent_co3, last_co3 = st.columns(3)
with left_co3:
    st.markdown(
        "**25.3** For time :",
    )
with cent_co3:
    st.markdown("""
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
""")
    st.markdown("")
    st.markdown("**Time cap: 20 minutes**")
with last_co3:
    st.markdown("""
♀️ 155-lb (70-kg) deadlift, 85-lb (38-kg) clean, 65-lb (29-kg) snatch

♂️ 225-lb (102-kg) deadlift, 135-lb (61-kg) clean, 95-lb (43-kg) snatch""")
