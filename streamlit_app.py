import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import os

# --- CONFIG & ADMIN SETTINGS ---
st.set_page_config(page_title="DJS SAE Recruitment Portal", layout="wide")
MASTER_PASSWORD = "T7@k9#Lm2$Q4" 

# --- LOGO MAPPING ---
# Updated to match your final logo list and the specific spelling: THE SPEEDSTERS
TEAM_LOGOS = {
    "Astra": "DJS Astra.jpg",
    "Helios": "DJS Helios.jpg",
    "Impulse": "DJS Impulse.jpg",
    "Karting": "DJS Karting.jpg",
    "Kronos": "DJS Kronos.jpg",
    "Miles": "DJS Miles.jpg",
    "Phoenix": "DJS Phoenix.jpg",
    "Racing": "DJS Racing.jpg",
    "Robocon": "DJS Robocon.jpg",
    "Skylark": "DJS Skylark.jpg",
    "THE SPEEDSTERS": "DJS Speedsters.jpg"
}

# --- STATE MANAGEMENT ---
if 'dialog_active' not in st.session_state:
    st.session_state.dialog_active = False
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

# Silent Sync (No loading bars or audio alerts)
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
    
    /* Clean button look */
    .stButton>button { border-radius: 8px; font-weight: 600; }
    
    /* Status Tags */
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
    if "Speedsters" in name or "SPEEDSTERS" in name: return "THE SPEEDSTERS"
    return name.title()

# --- ADMIN RESET DIALOG ---
@st.dialog("⚠️ MASTER RESET")
def master_reset_dialog(action_type, sap_id=None, current_team=None):
    st.session_state.dialog_active = True
    st.error("Admin credentials required to clear data.")
    pwd = st.text_input("Master Password", type="password")
    if st.button("Confirm Wipe", use_container_width=True):
        if pwd == MASTER_PASSWORD:
            if action_type == "all":
                global_db.clear()
            else:
                global_db.setdefault(sap_id, {})[current_team] = "Pending"
            st.session_state.dialog_active = False
            st.rerun()
        else:
            st.error("Access Denied.")

# --- LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>SAE RECRUITMENT</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Access Portal", use_container_width=True):
            df_all, cr = load_data()
            if df_all is not None:
                match = cr[(cr['Username'] == u) & (cr['Password'] == p)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.team = normalize_team(match.iloc[0]['Assigned Team'])
                    st.rerun()
                else: st.error("Wrong credentials.")
else:
    # --- SIDEBAR (ADMIN & LOGO) ---
    with st.sidebar:
        # 1. CLEAR ALL BUTTON (Placed at the very top for visibility)
        st.subheader("🛠️ ADMIN TOOLS")
        if st.button("🚨 CLEAR ALL DATA", use_container_width=True):
            master_reset_dialog("all")
        st.divider()

        # 2. LOGO
        team = st.session_state.team
        logo_path = TEAM_LOGOS.get(team)
        if logo_path and os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.info(f"Team: {team}")
            
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- MAIN INTERFACE ---
    st.markdown(f'<div class="header-box"><h1>{team.upper()}</h1></div>', unsafe_allow_html=True)

    df_all, _ = load_data()
    pref_cols = [f'Team preference list [{i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"}]' for i in range(1, 12)]
    
    # Filter for candidates
    mask = df_all[pref_cols].apply(lambda x: x.astype(str).str.contains(team, case=False)).any(axis=1)
    team_df = df_all[mask]

    # Search (Search name or SAP ID)
    search = st.text_input("🔍 Search Student Name / SAP ID")
    if search:
        team_df = team_df[team_df['Full Name'].str.contains(search, case=False) | team_df['SAP ID'].astype(str).str.contains(search)]

    # Status Lists
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

    # 1. INTERVIEWING NOW
    if proc:
        st.markdown('<div class="process-section">', unsafe_allow_html=True)
        st.subheader("🔵 Current Interview")
        for r in proc:
            sid = str(r['SAP ID'])
            st.write(f"### {r['Full Name']} ({sid})")
            st.markdown(f"<div>{draw_tags(r, sid)}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            if cols[0].button("✅ COMPLETE", key=f"d_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Done"; st.rerun()
            if cols[1].button("⏸️ HOLD", key=f"h_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Hold"; st.rerun()
            if cols[2].button("🔙 QUEUE", key=f"q_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Pending"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. ON HOLD
    if hold:
        st.markdown('<div class="hold-section">', unsafe_allow_html=True)
        st.subheader("🟣 On Hold")
        for r in hold:
            sid = str(r['SAP ID'])
            st.write(f"**{r['Full Name']}** ({sid})")
            cols = st.columns(2)
            if cols[0].button("▶ RESUME", key=f"res_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "In Process"; st.rerun()
            if cols[1].button("🔙 QUEUE", key=f"q2_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "Pending"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. WAITING LIST
    st.subheader(f"📋 Waiting List ({len(pend)})")
    for r in pend:
        sid = str(r['SAP ID'])
        with st.expander(f"➔ {r['Full Name']} ({sid})"):
            st.markdown(f"<div style='margin-bottom:10px;'>{draw_tags(r, sid)}</div>", unsafe_allow_html=True)
            if st.button("▶ START INTERVIEW", key=f"str_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "In Process"; st.rerun()

    # 4. FINISHED
    if done:
        st.markdown("<div class='done-section'>", unsafe_allow_html=True)
        st.subheader("🏁 Finished Today")
        for r in done:
            sid = str(r['SAP ID'])
            c1, c2 = st.columns([5, 1])
            c1.write(f"✅ **{r['Full Name']}** ({sid})")
            if c2.button("Undo 🔒", key=f"un_{sid}", use_container_width=True):
                master_reset_dialog("single", sid, team)
        st.markdown("</div>", unsafe_allow_html=True)
