import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import os

# --- CONFIG & ADMIN SETTINGS ---
st.set_page_config(page_title="DJS SAE Recruitment Portal", layout="wide")
MASTER_PASSWORD = "T7@k9#Lm2$Q4" 

# --- LOGO MAPPING ---
# Maps team names to their respective image filenames
TEAM_LOGOS = {
    "Astra": "DJS Astra.jpg.jpg",
    "Helios": "DJS Helios.jpg.jpg",
    "Impulse": "DJS Impulse.jpg.jpg",
    "Karting": "DJS Karting.jpg.jpg",
    "Kronos": "DJS Kronos.jpg.jpg",
    "Miles": "DJS Miles.jpg.jpg",
    "Phoenix": "DJS Phoenix.jpg.jpg",
    "Racing": "DJS Racing.jpg.jpg",
    "Robocon": "DJS Robocon.jpg.jpg",
    "Skylark": "DJS Skylark.jpg.jpg",
    "Speedsters": "DJS Speedsters.jpg.jpg"
}

# --- STATE MANAGEMENT ---
if 'dialog_active' not in st.session_state:
    st.session_state.dialog_active = False
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

# --- SILENT BACKGROUND SYNC ---
# Auto-refreshes every 3 seconds to keep the queue live for all 400+ students
if not st.session_state.dialog_active:
    st_autorefresh(interval=3000, limit=None, key="live_sync")

# --- UI & COLOR STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Header & Logo Container */
    .header-box { background: #1f242b; padding: 25px; border-radius: 12px; border-bottom: 4px solid #f1c40f; text-align: center; margin-bottom: 25px; }
    
    /* Section containers for clear visual separation */
    .process-section { background-color: #1e3a5f; padding: 25px; border-radius: 12px; border: 2px solid #3498db; margin-bottom: 25px; }
    .hold-section { background-color: #3b1e5f; padding: 25px; border-radius: 12px; border: 2px solid #9b59b6; margin-bottom: 25px; }
    .done-section { background-color: #1a1c23; padding: 20px; border-radius: 12px; border-left: 6px solid #238636; margin-top: 35px; }
    
    /* Status Tags for Preference Tracking */
    .tag-done { background-color: #238636; color: white; padding: 4px 12px; border-radius: 15px; margin-right: 6px; font-size: 11px; font-weight: bold; }
    .tag-hold { background-color: #9b59b6; color: white; padding: 4px 12px; border-radius: 15px; margin-right: 6px; font-size: 11px; font-weight: bold; }
    .tag-process { background-color: #3498db; color: white; padding: 4px 12px; border-radius: 15px; margin-right: 6px; font-size: 11px; font-weight: bold; }
    .tag-pending { color: #f1c40f; border: 1px solid #f1c40f; padding: 4px 12px; border-radius: 15px; margin-right: 6px; font-size: 11px; }
    
    /* Button alignment and styling */
    .stButton>button { border-radius: 10px; font-weight: 600; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

@st.cache_resource
def get_global_db():
    return {}

global_db = get_global_db()

@st.cache_data(ttl=5)
def load_data():
    try:
        df = pd.read_excel(FILE_NAME, sheet_name='Form Responses 1')
        creds = pd.read_excel(FILE_NAME, sheet_name='Credentials')
        return df, creds
    except:
        return None, None

def normalize_team(t_name):
    if pd.isna(t_name): return ""
    return str(t_name).strip().title()

# --- MASTER KEY DIALOG ---
@st.dialog("🔒 Master Authorization Required")
def master_reset_dialog(action_type, sap_id=None, current_team=None):
    st.session_state.dialog_active = True
    pwd = st.text_input("Enter Admin Password:", type="password")
    c1, c2 = st.columns(2)
    if c1.button("Confirm", use_container_width=True):
        if pwd == MASTER_PASSWORD:
            if action_type == "all":
                global_db.clear()
            else:
                global_db.setdefault(sap_id, {})[current_team] = "Pending"
            st.session_state.dialog_active = False
            st.rerun()
        else:
            st.error("Invalid Password.")
    if c2.button("Cancel", use_container_width=True):
        st.session_state.dialog_active = False
        st.rerun()

# --- LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>SAE RECRUITMENT LOGIN</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        u, p = st.text_input("Username"), st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            df_all, cr = load_data()
            if df_all is not None:
                user_match = cr[(cr['Username'] == u) & (cr['Password'] == p)]
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.team = normalize_team(user_match.iloc[0]['Assigned Team'])
                    st.rerun()
                else: st.error("Invalid Credentials")
else:
    # --- ADMIN SIDEBAR WITH LOGO ---
    with st.sidebar:
        current_team = st.session_state.team
        
        # Display the specific logo for the logged-in team
        logo_file = TEAM_LOGOS.get(current_team)
        if logo_file and os.path.exists(logo_file):
            st.image(logo_file, use_container_width=True)
        else:
            st.info(f"Team {current_team}")
            
        st.divider()
        if st.button("Wipe All Data 🚨", use_container_width=True):
            master_reset_dialog("all")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    team = st.session_state.team
    st.markdown(f'<div class="header-box"><h1>TEAM {team.upper()}</h1></div>', unsafe_allow_html=True)

    df_all, _ = load_data()
    pref_cols = [f'Team preference list [{i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"}]' for i in range(1, 12)]
    
    # Filter candidates based on preferences
    mask = df_all[pref_cols].apply(lambda x: x.astype(str).str.contains(team, case=False)).any(axis=1)
    team_df = df_all[mask]

    # --- SEARCH ---
    query = st.text_input("🔍 Search Name or SAP ID")
    if query:
        team_df = team_df[team_df['Full Name'].str.contains(query, case=False, na=False) | team_df['SAP ID'].astype(str).str.contains(query, na=False)]

    # Categorize students by interview status
    process_list, hold_list, pending_list, done_list = [], [], [], []
    for _, row in team_df.iterrows():
        sid = str(row['SAP ID'])
        status = global_db.get(sid, {}).get(team, "Pending")
        if status == "In Process": process_list.append(row)
        elif status == "Hold": hold_list.append(row)
        elif status == "Done": done_list.append(row)
        else: pending_list.append(row)

    def render_tags(row_data, sap_id):
        tags_html = ""
        for col in pref_cols:
            p_team = normalize_team(row_data[col])
            if p_team:
                t_stat = global_db.get(sap_id, {}).get(p_team, "Pending")
                css = "tag-done" if t_stat == "Done" else "tag-hold" if t_stat == "Hold" else "tag-process" if t_stat == "In Process" else "tag-pending"
                tags_html += f'<span class="{css}">{p_team}</span>'
        return tags_html

    # --- MAIN INTERFACE ---
    
    # Interviewing Now
    if process_list:
        st.markdown('<div class="process-section">', unsafe_allow_html=True)
        st.subheader("🔵 Currently Interviewing")
        for row in process_list:
            sid = str(row['SAP ID'])
            st.markdown(f'<div style="color: #3498db; font-size: 22px; font-weight: bold;">{row["Full Name"]} ({sid})</div>', unsafe_allow_html=True)
            st.markdown(f"<div style='margin-bottom:15px;'>{render_tags(row, sid)}</div>", unsafe_allow_html=True)
            
            btn_cols = st.columns(3)
            if btn_cols[0].button("✅ COMPLETE", key=f"d_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Done"; st.rerun()
            if btn_cols[1].button("⏸️ HOLD", key=f"h_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Hold"; st.rerun()
            if btn_cols[2].button("🔙 QUEUE", key=f"q_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Pending"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # On Hold
    if hold_list:
        st.markdown('<div class="hold-section">', unsafe_allow_html=True)
        st.subheader("🟣 On Hold")
        for row in hold_list:
            sid = str(row['SAP ID'])
            st.write(f"**{row['Full Name']}** ({sid})")
            btn_cols = st.columns(2)
            if btn_cols[0].button("▶ RESUME", key=f"r_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "In Process"; st.rerun()
            if btn_cols[1].button("🔙 QUEUE", key=f"q2_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Pending"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Waiting List
    st.subheader(f"📋 Waiting List ({len(pending_list)})")
    for row in pending_list:
        sid = str(row['SAP ID'])
        with st.expander(f"➔ {row['Full Name']} ({sid})"):
            st.markdown(f"<div style='margin-bottom:15px;'>{render_tags(row, sid)}</div>", unsafe_allow_html=True)
            if st.button("▶ START INTERVIEW", key=f"s_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "In Process"; st.rerun()

    # Finished
    if done_list:
        st.markdown("<div class='done-section'>", unsafe_allow_html=True)
        st.subheader("🏁 Finished Interviews")
        for row in done_list:
            sid = str(row['SAP ID'])
            c_a, c_b = st.columns([5, 1])
            c_a.write(f"✅ **{row['Full Name']}** ({sid})")
            if c_b.button("Undo 🔒", key=f"u_{sid}", use_container_width=True):
                master_reset_dialog("single", sid, team)
        st.markdown("</div>", unsafe_allow_html=True)
