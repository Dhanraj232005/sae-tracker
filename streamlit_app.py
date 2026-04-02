import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import os

# --- CONFIG & ADMIN SETTINGS ---
st.set_page_config(page_title="DJS SAE Recruitment Portal", layout="wide")
MASTER_PASSWORD = "MilesAdmin2026" 

# --- LOGO MAPPING ---
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

# Silent Sync
if not st.session_state.dialog_active:
    st_autorefresh(interval=3000, limit=None, key="live_sync")

# --- UI STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .header-box { background: #1f242b; padding: 25px; border-radius: 12px; border-bottom: 5px solid #f1c40f; text-align: center; margin-bottom: 25px; }
    .process-section { background-color: #1e3a5f; padding: 25px; border-radius: 12px; border: 2px solid #3498db; margin-bottom: 25px; }
    .hold-section { background-color: #3b1e5f; padding: 25px; border-radius: 12px; border: 2px solid #9b59b6; margin-bottom: 25px; }
    .done-section { background-color: #1a1c23; padding: 20px; border-radius: 12px; border-left: 6px solid #238636; margin-top: 35px; }
    
    .tag-done { background-color: #238636; color: white; padding: 4px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; }
    .tag-hold { background-color: #9b59b6; color: white; padding: 4px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; }
    .tag-process { background-color: #3498db; color: white; padding: 4px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; }
    .tag-pending { border: 1px solid #f1c40f; color: #f1c40f; padding: 4px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; }
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
    name = str(t_name).strip()
    if "Speedster" in name.title(): return "Speedsters"
    return name.title()

# --- ADMIN RESET DIALOG ---
@st.dialog("⚠️ MASTER AUTHORIZATION")
def master_reset_dialog(action_type, sap_id=None, current_team=None):
    st.session_state.dialog_active = True
    st.warning(f"Action: {action_type.upper()}")
    pwd = st.text_input("Enter Admin Password", type="password")
    if st.button("Confirm", use_container_width=True):
        if pwd == MASTER_PASSWORD:
            if action_type == "all":
                global_db.clear()
            else:
                global_db.setdefault(sap_id, {})[current_team] = "Pending"
            st.session_state.dialog_active = False
            st.rerun()
        else:
            st.error("Invalid Password.")

# --- LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>SAE RECRUITMENT</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            df_all, cr = load_data()
            if df_all is not None:
                match = cr[(cr['Username'] == u) & (cr['Password'] == p)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.team = normalize_team(match.iloc[0]['Assigned Team'])
                    st.rerun()
                else: st.error("Invalid credentials.")
else:
    # --- MAIN UI ---
    team = st.session_state.team
    
    # Header with Logo and Title
    col_logo, col_title = st.columns([1, 5])
    logo_path = TEAM_LOGOS.get(team)
    if logo_path and os.path.exists(logo_path):
        col_logo.image(logo_path, width=110)
    
    # Strictly display "SPEEDSTERS" for the specific team on screen
    display_name = "SPEEDSTERS" if team == "Speedsters" else team.upper()
    st.markdown(f'<div class="header-box"><h1>{display_name}</h1></div>', unsafe_allow_html=True)

    df_all, _ = load_data()
    pref_cols = [f'Team preference list [{i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"}]' for i in range(1, 12)]
    
    mask = df_all[pref_cols].apply(lambda x: x.astype(str).str.contains("Speedster" if team == "Speedsters" else team, case=False)).any(axis=1)
    team_df = df_all[mask]

    search = st.text_input("🔍 Search Name or SAP ID")
    if search:
        team_df = team_df[team_df['Full Name'].str.contains(search, case=False) | team_df['SAP ID'].astype(str).str.contains(search)]

    proc, hold, pend, done = [], [], [], []
    for _, row in team_df.iterrows():
        sid = str(row['SAP ID'])
        stat = global_db.get(sid, {}).get(team, "Pending")
        if stat == "In Process": proc.append(row)
        elif stat == "Hold": hold.append(row)
        elif stat == "Done": done.append(row)
        else: pend.append(row)

    def draw_tags(row, sid):
        html = ""
        for c in pref_cols:
            t = normalize_team(row[c])
            if t:
                s = global_db.get(sid, {}).get(t, "Pending")
                cls = "tag-done" if s=="Done" else "tag-hold" if s=="Hold" else "tag-process" if s=="In Process" else "tag-pending"
                html += f'<span class="{cls}">{t}</span>'
        return html

    # Sections
    if proc:
        st.markdown('<div class="process-section">', unsafe_allow_html=True)
        st.subheader("🔵 Currently Interviewing")
        for r in proc:
            sid = str(r['SAP ID'])
            st.write(f"### {r['Full Name']} ({sid})")
            st.markdown(f"<div>{draw_tags(r, sid)}</div>", unsafe_allow_html=True)
            c = st.columns(3)
            if c[0].button("✅ COMPLETE", key=f"d_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Done"; st.rerun()
            if c[1].button("⏸️ HOLD", key=f"h_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Hold"; st.rerun()
            if c[2].button("🔙 QUEUE", key=f"q_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Pending"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if hold:
        st.markdown('<div class="hold-section">', unsafe_allow_html=True)
        st.subheader("🟣 On Hold")
        for r in hold:
            sid = str(r['SAP ID'])
            st.write(f"**{r['Full Name']}** ({sid})")
            c = st.columns(2)
            if c[0].button("▶ RESUME", key=f"re_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "In Process"; st.rerun()
            if c[1].button("🔙 QUEUE", key=f"q2_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Pending"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.subheader(f"📋 Waiting List ({len(pend)})")
    for r in pend:
        sid = str(r['SAP ID'])
        with st.expander(f"➔ {r['Full Name']} ({sid})"):
            st.markdown(f"<div style='margin-bottom:10px;'>{draw_tags(r, sid)}</div>", unsafe_allow_html=True)
            if st.button("▶ START INTERVIEW", key=f"s_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "In Process"; st.rerun()

    if done:
        st.markdown("<div class='done-section'>", unsafe_allow_html=True)
        st.subheader("🏁 Finished")
        for r in done:
            sid = str(r['SAP ID'])
            c1, c2 = st.columns([5, 1])
            c1.write(f"✅ **{r['Full Name']}** ({sid})")
            if c2.button("Reset 🔒", key=f"u_{sid}", use_container_width=True):
                master_reset_dialog("single", sid, team)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- FOOTER BUTTONS ---
    st.write("---")
    f1, f2 = st.columns(2)
    if f1.button("🚨 CLEAR ALL DATA", use_container_width=True):
        master_reset_dialog("all")
    if f2.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
