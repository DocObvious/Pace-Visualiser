import streamlit as st
import matplotlib.pyplot as plt
import io

# --- Helper Functions ---
def fmt_time(s):
    h, m = divmod(int(s), 3600)
    m, sec = divmod(m, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h > 0 else f"{m}:{sec:02d}"

def pace_to_seconds(ts):
    try:
        if ':' in ts:
            m, s = map(int, ts.split(':'))
            return (m * 60) + s
        return int(ts) * 60
    except:
        return 480 

st.set_page_config(page_title="Pace Visualiser", page_icon="🏃", layout="wide")

st.markdown("""
    <style>
    .stTextInput>div>div>input { font-family: 'Courier New', monospace; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏃 Pace Visualiser")

# --- Sidebar ---
with st.sidebar.expander("🛠️ Core Settings", expanded=True):
    unit = st.radio("Distance Unit", ["Miles", "Kilometers"])

with st.sidebar.expander("📝 Data Entry Tools", expanded=True):
    block_pace = st.text_input("Pace to Apply", value="8:00" if unit == "Miles" else "5:00")
    col_s1, col_s2 = st.columns(2)
    start_range = col_s1.number_input("From", min_value=1, value=1)
    end_range = col_s2.number_input("To", min_value=1, value=26 if unit == "Miles" else 42)
    
    if st.button("Apply to Range"):
        num = 26 if unit == "Miles" else 42
        for i in range(int(start_range)-1, int(end_range)):
            if i < num:
                st.session_state.paces[i] = block_pace
                st.session_state[f"input_{i}"] = block_pace
        st.rerun()

with st.sidebar.expander("🎨 Graph Aesthetics", expanded=True):
    theme = st.selectbox("Theme", ["Dark Mode", "Light Mode"])
    y_floor = st.text_input("Graph Floor (Slowest)", value="10.0")
    y_ceiling = st.text_input("Graph Ceiling (Fastest)", value="6.0")
    bar_color = st.color_picker("Bar Color", "#3498db")
    line_color = st.color_picker("Avg Pace Line Color", "#ff7f50")
    target_color = st.color_picker("Target Line Color", "#ffffff")

# --- Logic ---
num_units = 26 if unit == "Miles" else 42
if 'paces' not in st.session_state or st.session_state.get('last_unit') != unit:
    st.session_state.paces = ["8:00" if unit == "Miles" else "5:00"] * num_units
    st.session_state.last_unit = unit

# --- Data Entry (Vertical for Mobile Consistency) ---
with st.expander(f"Individual {unit} Splits", expanded=True):
    for i in range(num_units):
        row = st.columns([1, 4])
        row[0].write(f"**{i+1}**")
        st.session_state.paces[i] = row[1].text_input(
            label=f"split_{i}", value=st.session_state.paces[i], 
            key=f"input_{i}", label_visibility="collapsed"
        )

# --- Report Generation ---
if st.button("GENERATE PERFORMANCE REPORT", type="primary", use_container_width=True):
    paces_secs = [pace_to_seconds(p) for p in st.session_state.paces]
    paces_mins = [p / 60.0 for p in paces_secs]
    running_avgs = [sum(paces_mins[:i])/i for i in range(1, num_units + 1)]
    total_avg = sum(paces_mins) / num_units
    
    # Aesthetics logic
    plt.style.use('dark_background' if theme == "Dark Mode" else 'default')
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plotting everything
    ax.bar(range(1, num_units+1), paces_mins, color=bar_color, alpha=0.5, label='Split Pace')
    ax.plot(range(1, num_units+1), running_avgs, color=line_color, marker='o', linewidth=2.5, label='Rolling Avg')
    ax.axhline(y=total_avg, color=target_color, linestyle='--', label='Target Avg')
    
    # Y-Axis range safety
    f_val, c_val = float(y_floor), float(y_ceiling)
    ax.set_ylim(min(f_val, c_val), max(f_val, c_val))
    
    ax.legend()
    st.pyplot(fig)
