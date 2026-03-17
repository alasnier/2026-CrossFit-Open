import streamlit as st

from auth_utils import show_auth_status

st.set_page_config(
    page_title="2026 Open WODs",
    layout="wide",
    page_icon="📅",
)

show_auth_status()

st.title("2026 Open WODs")
st.sidebar.header("2026 Open WODs")

st.info("Les WODs 26.1, 26.2 et 26.3 sont publiés entre **le 26 février et le 16 mars 2026**.")

st.markdown("---")

# ── WOD 26.1 ────────────────────────────────────────────────────────────────
st.header("WOD 26.1")
st.markdown("**For time:**")

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("""
    - 20 wall-ball shots
    - 18 box jump-overs
    - 30 wall-ball shots
    - 18 box jump-overs
    - 40 wall-ball shots
    - 18 medicine-ball box step-overs
    - 66 wall-ball shots
    - 18 medicine-ball box step-overs
    - 40 wall-ball shots
    - 18 box jump-overs
    - 30 wall-ball shots
    - 18 box jump-overs
    - 20 wall-ball shots
    """)
with col2:
    st.markdown("""
    **Time cap:** 12 minutes
    
    **Poids et Hauteurs :**
    - ♀ 14-lb (6-kg) medicine ball, 9-foot target, 20-inch box
    - ♂ 20-lb (9-kg) medicine ball, 10-ft target, 24-inch box
    """)

st.markdown("---")

# ── WOD 26.2 ────────────────────────────────────────────────────────────────
st.header("WOD 26.2")
st.markdown("**For time:**")

col3, col4 = st.columns([2, 1])
with col3:
    st.markdown("""
    - 80-foot dumbbell overhead walking lunge
    - 20 alternating dumbbell snatches
    - 20 pull-ups
    - 80-foot dumbbell overhead walking lunge
    - 20 alternating dumbbell snatches
    - 20 chest-to-bar pull-ups
    - 80-foot dumbbell overhead walking lunge
    - 20 alternating dumbbell snatches
    - 20 muscle-ups
    """)
with col4:
    st.markdown("""
    **Time cap:** 15 minutes
    
    **Poids :**
    - ♀ 35-lb (15-kg) dumbbell
    - ♂ 50-lb (22.5-kg) dumbbell
    """)

st.markdown("---")

# ── WOD 26.3 ────────────────────────────────────────────────────────────────
st.header("WOD 26.3")
st.markdown("**For time:**")

col5, col6 = st.columns([2, 1])
with col5:
    st.markdown("""
    **2 rounds of:**
    - 12 burpees over the bar
    - 12 cleans, weight 1
    - 12 burpees over the bar
    - 12 thrusters, weight 1
    
    **2 rounds of:**
    - 12 burpees over the bar
    - 12 cleans, weight 2
    - 12 burpees over the bar
    - 12 thrusters, weight 2
    
    **2 rounds of:**
    - 12 burpees over the bar
    - 12 cleans, weight 3
    - 12 burpees over the bar
    - 12 thrusters, weight 3
    """)
with col6:
    st.markdown("""
    **Time cap:** 16 minutes
    
    **Poids :**
    - ♀ 65, 75, 85 lb (29, 34, 38 kg)
    - ♂ 95, 115, 135 lb (43, 52, 61 kg)
    """)
