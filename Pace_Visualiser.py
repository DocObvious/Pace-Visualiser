import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
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

# --- App Config & Styling ---
st.set_page_config(page_title="Pace Visualiser", page_icon="🏃", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 2.2em; margin-top: 5px; }
    .stTextInput>div>div>input { font-family: 'Courier New', monospace; font-weight: bold; }
    .mile-label { margin-top: 32px; font-weight: bold; font-size: 1.0em; color: #666; }
    .intro-text { font-size: 1.1em; color: #555; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.title("🏃 Pace Visualiser")
st.markdown('<div class="intro-text">Analyze your marathon splits with precision. Use the bulk entry tool to save time!</div>', unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.title("App Dashboard")

with st.sidebar.expander("🛠️ Core Settings", expanded=True):
    unit = st.sidebar.radio("Distance Unit", ["Miles", "Kilometers"])

with st.sidebar.expander("📝 Data Entry Tools", expanded=True):
    block_pace = st.text_input("Pace to Apply", value="8:00" if unit == "Miles" else "5:00")
    col_s1, col_s2 = st.columns(2)
    start_range = col_s1.number_input("From", min_value=1, value=1)
    end_range = col_s2.number_input("To", min_value=1, value=26 if unit == "Miles" else 42)
    
    if st.sidebar.button(f"Apply to Range"):
        num_units = 26 if unit == "Miles" else 42
        for i in range(int(start_range)-1, int(end_range)):
            if i < num_units:
                # Update the source data
                st.session_state.paces[i] = block_pace
                # UPDATE THE WIDGET KEYS DIRECTLY (Fixes the Button Issue)
                st.session_state[f"input_{i}"] = block_pace
        st.rerun()

with st.sidebar.expander("🎨 Graph Aesthetics", expanded=False):
    theme_choice = st.selectbox("Base Theme", ["Dark Mode", "Light Mode"])
    y_min = st.slider("Graph Floor (Slowest)", 4.0, 15.0, 10.0)
    y_max = st.slider("Graph Ceiling (Fastest)", 4.0, 15.0, 6.0)
    st.divider()
    bar_color = st.color_picker("Split Bar Color", "#3498db")
    line_color = st.color_picker("Average Line Color", "#ff7f50")
    target_color = st.color_picker("Target Line Color", "#ffffff")

# --- Logic Setup ---
num_units = 26 if unit == "Miles" else 42
finish_stretch = 0.2 if unit == "Miles" else 0.195

if 'paces' not in st.session_state or st.session_state.get('last_unit') != unit:
    st.session_state.paces = ["8:00" if unit == "Miles" else "5:00"] * num_units
    st.session_state.last_unit = unit

# --- Data Entry Grid ---
with st.expander(f"Individual {unit} Splits", expanded=True):
    grid_cols = 6 if unit == "Kilometers" else 4
    cols = st.columns(grid_cols)
    
    for i in range(num_units):
        with cols[i % grid_cols]:
            c_lab, c_inp = st.columns([1, 3])
            c_lab.markdown(f'<div class="mile-label">{i+1}</div>', unsafe_allow_html=True)
            
            # This is bound to the keys updated in the sidebar
            st.session_state.paces[i] = c_inp.text_input(
                label=f"split_{i}", 
                value=st.session_state.paces[i], 
                key=f"input_{i}", 
                label_visibility="hidden"
            )

# --- Analysis & Generation ---
if st.button("GENERATE PERFORMANCE REPORT", type="primary", use_container_width=True):
    # Capture fresh paces
    paces_secs = [pace_to_seconds(p) for p in st.session_state.paces]
    unit_range = list(range(1, num_units + 1))
    paces_mins = [p / 60.0 for p in paces_secs]
    running_avgs = [sum(paces_mins[:i])/i for i in range(1, num_units + 1)]
    
    total_avg_secs = sum(paces_secs) / num_units
    
    # Corrected KM math (21.1km half)
    if unit == "Kilometers":
        first_half_secs = sum(paces_secs[:21]) + (paces_secs[21] * 0.1)
    else:
        first_half_secs = sum(paces_secs[:13]) + (paces_secs[13] * 0.1)
        
    full_total_secs = sum(paces_secs) + (paces_secs[-1] * finish_stretch)
    second_half_secs = full_total_secs - first_half_secs

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Time", fmt_time(full_total_secs))
    m2.metric("Avg Pace", f"{fmt_time(total_avg_secs)}/{unit[:2].lower()}")
    m3.metric("1st Half", fmt_time(first_half_secs))
    m4.metric("2nd Half", fmt_time(second_half_secs))

    # --- Plotting ---
    plt.style.use('dark_background' if theme_choice == "Dark Mode" else 'default')
    bg_color = '#0e1117' if theme_choice == "Dark Mode" else '#ffffff'
    text_color = 'white' if theme_choice == "Dark Mode" else 'black'
    grid_color = '#444' if theme_choice == "Dark Mode" else '#ddd'

    fig, ax = plt.subplots(figsize=(14, 7), facecolor=bg_color)
    ax.set_facecolor(bg_color)

    ax.bar(unit_range, paces_mins, color=bar_color, alpha=0.4, width=0.7, label='Split Pace')
    ax.plot(unit_range, running_avgs, color=line_color, marker='o', markersize=4, 
            linewidth=2.5, label='Running Average')
    ax.axhline(y=total_avg_secs/60.0, color=target_color, linestyle='--', alpha=0.5, label='Target Avg')
    
    # Tick Logic
    ax.set_xticks(unit_range)
    ax.set_xticklabels(unit_range, fontsize=8 if unit == "Kilometers" else 10)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', color=grid_color, linestyle='--', alpha=0.4)
    
    # Invert the logic so Slowest (Floor) is at the bottom and Fastest (Ceiling) is at top
    ax.set_ylim(min(y_min, y_max), max(y_min, y_max))
    
    ax.set_title(f"PACE VISUALISER: PERFORMANCE REPORT ({unit.upper()})", 
                 fontsize=14, fontweight='bold', color=text_color, pad=25)
    
    # Overlay Statistics
    stats_box = (f"RESULT: {fmt_time(full_total_secs)}\n"
                 f"AVG: {fmt_time(total_avg_secs)}/{unit[:2].lower()}\n"
                 f"1ST HALF: {fmt_time(first_half_secs)}\n"
                 f"2ND HALF: {fmt_time(second_half_secs)}")
    
    ax.text(0.02, 0.95, stats_box, transform=ax.transAxes, fontsize=10, 
            color=text_color, family='monospace', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.6', facecolor=bg_color, alpha=0.8, edgecolor=bar_color))

    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    st.download_button("💾 Download Graph", buf.getvalue(), "pace_report.png", "image/png")
