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
    .mile-label { font-weight: bold; font-size: 1.1em; color: #666; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏃 Pace Visualiser")
st.markdown('<div class="intro-text">Analyze your marathon splits with precision. Use the bulk entry tool to save time!  Use this tool to visualise predicted marathon splits by mile or km. Ideal to allow you to visualise a strong pacing strategy or to model a route with hills at particular miles/km</div>', unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar.expander("🛠️ Core Settings", expanded=True):
    unit = st.radio("Distance Unit", ["Miles", "Kilometers"])

# Fixes the switch glitch between Miles and KM
num_units = 26 if unit == "Miles" else 42
if 'paces' not in st.session_state or len(st.session_state.paces) != num_units:
    default_p = "8:00" if unit == "Miles" else "5:00"
    st.session_state.paces = [default_p] * num_units
    for key in list(st.session_state.keys()):
        if key.startswith("input_"):
            del st.session_state[key]

with st.sidebar.expander("📝 Data Entry Tools", expanded=True):
    block_pace = st.text_input("Pace to Apply", value="8:00" if unit == "Miles" else "5:00")
    col_s1, col_s2 = st.columns(2)
    start_range = col_s1.number_input("From", min_value=1, value=1)
    end_range = col_s2.number_input("To", min_value=1, value=num_units)
    
    if st.button("Apply to Range"):
        for i in range(int(start_range)-1, int(end_range)):
            if i < num_units:
                st.session_state.paces[i] = block_pace
                st.session_state[f"input_{i}"] = block_pace
        st.rerun()

with st.sidebar.expander("🎨 Graph Aesthetics", expanded=True):
    theme = st.selectbox("Theme", ["Dark Mode", "Light Mode"])
    # Adjusted labels to reflect your preference
    y_min = st.text_input("Graph Baseline (Fastest)", value="4.0")
    y_max = st.text_input("Graph Peak (Slowest)", value="12.0")
    st.divider()
    bar_color = st.color_picker("Bar Color", "#3498db")
    line_color = st.color_picker("Rolling Avg Color", "#ff7f50")
    target_color = st.color_picker("Target Line Color", "#ffffff")

# --- Data Entry Grid ---
with st.expander(f"Individual {unit} Splits", expanded=True):
    for i in range(num_units):
        row = st.columns([1, 5])
        row[0].markdown(f'<div class="mile-label">{i+1}</div>', unsafe_allow_html=True)
        st.session_state.paces[i] = row[1].text_input(
            label=f"split_{i}", 
            value=st.session_state.paces[i], 
            key=f"input_{i}", 
            label_visibility="collapsed"
        )

# --- Analysis & Generation ---
if st.button("GENERATE PERFORMANCE REPORT", type="primary", use_container_width=True):
    paces_secs = [pace_to_seconds(p) for p in st.session_state.paces]
    paces_mins = [p / 60.0 for p in paces_secs]
    running_avgs = [sum(paces_mins[:i])/i for i in range(1, num_units + 1)]
    total_avg_secs = sum(paces_secs) / num_units
    
    finish_stretch = 0.2 if unit == "Miles" else 0.195
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
    plt.style.use('dark_background' if theme == "Dark Mode" else 'default')
    bg_color = '#0e1117' if theme == "Dark Mode" else '#ffffff'
    text_color = 'white' if theme == "Dark Mode" else 'black'
    
    fig, ax = plt.subplots(figsize=(14, 7), facecolor=bg_color)
    ax.set_facecolor(bg_color)

    unit_range = range(1, num_units + 1)
    ax.bar(unit_range, paces_mins, color=bar_color, alpha=0.4, label='Split Pace')
    ax.plot(unit_range, running_avgs, color=line_color, marker='o', linewidth=2, label='Rolling Avg pace')
    ax.axhline(y=total_avg_secs/60.0, color=target_color, linestyle='--', alpha=0.6, label='Avg pace')
    
    ax.set_xticks(unit_range)
    ax.set_xticklabels(unit_range, fontsize=8 if unit == "Kilometers" else 10)
    
    # Standard orientation: Smallest number at bottom, Largest at top
    # This means the "slowest" (highest number) creates the biggest bars
    try:
        val_min, val_max = float(y_min), float(y_max)
        ax.set_ylim(min(val_min, val_max), max(val_min, val_max))
    except:
        ax.set_ylim(4.0, 12.0)

    ax.set_title(f"PACE VISUALISER ({unit.upper()})", fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right')

    stats_text = (f"RESULT: {fmt_time(full_total_secs)}\n"
                  f"AVG pace: {fmt_time(total_avg_secs)}/{unit[:2].lower()}\n"
                  f"1ST HALF: {fmt_time(first_half_secs)}\n"
                  f"2ND HALF: {fmt_time(second_half_secs)}")
    
    ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, fontsize=11, 
            color=text_color, family='monospace', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.6', facecolor=bg_color, alpha=0.8, edgecolor=bar_color))

    st.pyplot(fig)
    
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    st.download_button("💾 Download High-Res Image", buf.getvalue(), "pace_report.png", "image/png")
        
