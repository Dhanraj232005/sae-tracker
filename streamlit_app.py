import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- CONFIG & ADMIN SETTINGS ---
st.set_page_config(page_title="SAE Recruitment Portal", layout="wide")
MASTER_PASSWORD = "MilesAdmin2026" 

# --- STATE MANAGEMENT ---
if 'dialog_active' not in st.session_state:
    st.session_state.dialog_active = False
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

# --- SILENT BACKGROUND SYNC ---
# This pauses the refresh if you are typing in the Master Key dialog
if not st.session_state.dialog_active:
    st_autorefresh(interval=3000, limit=None, key="live_sync")

# --- UI & COLOR STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stProgress > div > div > div > div { background-image: none; }
    .header-box { background: #1f242b; padding: 20px; border-radius: 10px; border-bottom: 3px solid #f1c40f; text-align: center; margin-bottom: 20px; }
    
    /* Section Styles */
    .process-section { background-color: #1e3a5f; padding: 20px; border-radius: 10px; border: 2px solid #3498db; margin-bottom: 20px; }
    .hold-section { background-color: #3b1e5f; padding: 20px; border-radius: 10px; border: 2px solid #9b59b6; margin-bottom: 20px; }
    .done-section { background-color: #1a1c23; padding: 15px; border-radius: 10px; border-left: 5px solid #238636; margin-top: 30px; }
    
    /* Tag Styles */
    .tag-done { background-color: #238636; color: white; padding: 3px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; font-weight: bold; }
    .tag-hold { background-color: #9b59b6; color: white; padding: 3px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; font-weight: bold; }
    .tag-process { background-color: #3498db; color: white; padding: 3px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; font-weight: bold; }
    .tag-pending { color: #f1c40f; border: 1px solid #f1c40f; padding: 3px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; }
    
    .stButton>button { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

# --- GLOBAL DATABASE (PERSISTENT) ---
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
    name = str(t_name).strip().title()
    # Enforce correct spelling
    if "Speedster" in name: return "Speedsters"
    return name

# --- MASTER KEY DIALOG ---
@st.dialog("🔒 Master Authorization Required")
def master_reset_dialog(sap_id, current_team):
    st.session_state.dialog_active = True
    st.warning(f"Resetting interview status for **{sap_id}**.")
    pwd = st.text_input("Enter Admin Password:", type="password")
    
    c1, c2 = st.columns(2)
    if c1.button("Confirm Reset", use_container_width=True):
        if pwd == MASTER_PASSWORD:
            global_db.setdefault(sap_id, {})[current_team] = "Pending"
            st.session_state.dialog_active = False
            st.rerun()
        else:
            st.error("Invalid Password.")
            
    if c2.button("Cancel", use_container_width=True):
        st.session_state.dialog_active = False
        st.rerun()

# --- APP LOGIC ---
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
    team = st.session_state.team
    st.markdown(f'<div class="header-box"><h1>TEAM {team.upper()}</h1></div>', unsafe_allow_html=True)

    df_all, _ = load_data()
    pref_cols = [f'Team preference list [{i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"}]' for i in range(1, 12)]
    
    for col in pref_cols:
        if col in df_all.columns:
            df_all[col] = df_all[col].apply(normalize_team)

    mask = df_all[pref_cols].apply(lambda x: x.astype(str).str.contains(team, case=False)).any(axis=1)
    team_df = df_all[mask]

    # --- ADMIN EXPORT ---
    export_data = []
    for _, row in team_df.iterrows():
        sid = str(row['SAP ID'])
        export_row = {"Full Name": row['Full Name'], "SAP ID": sid}
        for col in pref_cols:
            p_team = row[col]
            if p_team:
                status = global_db.get(sid, {}).get(p_team, "Pending")
                export_row[f"Status at {p_team}"] = status
        export_data.append(export_row)
    
    csv = pd.DataFrame(export_data).to_csv(index=False).encode('utf-8')
    c_search, c_btn = st.columns([3, 1])
    query = c_search.text_input("🔍 Search Name/SAP ID")
    c_btn.download_button("📥 DOWNLOAD LIVE DATA", csv, f"{team}_Live_Data.csv", use_container_width=True)

    if query:
        team_df = team_df[team_df['Full Name'].str.contains(query, case=False, na=False) | team_df['SAP ID'].astype(str).str.contains(query, na=False)]

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
            p_team = row_data[col]
            if p_team:
                t_stat = global_db.get(sap_id, {}).get(p_team, "Pending")
                css = "tag-done" if t_stat == "Done" else "tag-hold" if t_stat == "Hold" else "tag-process" if t_stat == "In Process" else "tag-pending"
                tags_html += f'<span class="{css}">{p_team}</span>'
        return tags_html

    # --- 1. IN PROCESS (BLUE) ---
    if process_list:
        st.markdown('<div class="process-section">', unsafe_allow_html=True)
        st.subheader("🔵 Interviewing Now")
        for row in process_list:
            sid = str(row['SAP ID'])
            st.markdown(f'<div style="color: #3498db; font-size: 20px; font-weight: bold;">{row["Full Name"]} ({sid})</div>', unsafe_allow_html=True)
            st.markdown(f"<div>{render_tags(row, sid)}</div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ COMPLETE", key=f"d_{sid}"):
                global_db.setdefault(sid, {})[team] = "Done"; st.rerun()
            if c2.button("⏸️ HOLD", key=f"h_{sid}"):
                global_db.setdefault(sid, {})[team] = "Hold"; st.rerun()
            if c3.button("🔙 QUEUE", key=f"q_{sid}"):
                global_db.setdefault(sid, {})[team] = "Pending"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 2. HOLD (PURPLE) ---
    if hold_list:
        st.markdown('<div class="hold-section">', unsafe_allow_html=True)
        st.subheader("🟣 On Hold")
        for row in hold_list:
            sid = str(row['SAP ID'])
            st.markdown(f'<div style="color: #9b59b6; font-weight: bold;">{row["Full Name"]} ({sid})</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("▶ RESUME", key=f"r_{sid}"):
                global_db.setdefault(sid, {})[team] = "In Process"; st.rerun()
            if c2.button("🔙 QUEUE", key=f"q2_{sid}"):
                global_db.setdefault(sid, {})[team] = "Pending"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. QUEUE (YELLOW) ---
    st.subheader(f"📋 Waiting List ({len(pending_list)})")
    for row in pending_list:
        sid = str(row['SAP ID'])
        with st.expander(f"➔ {row['Full Name']} ({sid})"):
            st.markdown(f"<div>{render_tags(row, sid)}</div>", unsafe_allow_html=True)
            if st.button("▶ START", key=f"s_{sid}", use_container_width=True):
                global_db.setdefault(sid, {})[team] = "In Process"; st.rerun()

    # --- 4. FINISHED (GREEN) ---
    if done_list:
        st.markdown("<div class='done-section'>", unsafe_allow_html=True)
        st.subheader("🏁 Finished Interviews")
        for row in done_list:
            sid = str(row['SAP ID'])
            col_a, col_b = st.columns([5, 1])
            col_a.write(f"✅ **{row['Full Name']}** ({sid})")
            if col_b.button("Undo 🔒", key=f"u_{sid}"):
                master_reset_dialog(sid, team)
        st.markdown("</div>", unsafe_allow_html=True)
