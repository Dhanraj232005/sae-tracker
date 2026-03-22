import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SAE Team Portal", layout="wide", initial_sidebar_state="collapsed")

# --- TEAM LOGO MAPPING ---
# Replace these URLs with your actual team logo links if you have them!
LOGO_MAP = {
    "Miles": "https://img.icons8.com/fluency/96/lightning-bolt.png",
    "Racing": "https://img.icons8.com/fluency/96/f1-car.png",
    "Phoenix": "https://img.icons8.com/fluency/96/fire-element.png",
    "Kronos": "https://img.icons8.com/fluency/96/clock.png",
    "Helios": "https://img.icons8.com/fluency/96/sun.png",
    "Speedsters": "https://img.icons8.com/fluency/96/speed.png",
    "Robocon": "https://img.icons8.com/fluency/96/robot-vacuum.png"
}

# --- PRO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    .header-box {
        background: linear-gradient(90deg, #1f242b 0%, #0d1117 100%);
        padding: 20px;
        border-radius: 15px;
        border-bottom: 2px solid #f1c40f;
        text-align: center;
        margin-bottom: 25px;
    }
    .status-badge { padding: 4px 12px; border-radius: 15px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    .status-completed { background-color: #238636; color: white; }
    .status-in-progress { background-color: #da3633; color: white; animation: pulse 1.5s infinite; }
    .status-waiting { background-color: #30363d; color: #adbac7; }
    
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    
    .tag-done { color: #2ecc71; border: 1px solid #2ecc71; padding: 2px 8px; border-radius: 5px; margin-right: 5px; font-size: 10px; font-weight: bold; }
    .tag-pending { color: #f1c40f; border: 1px solid #f1c40f; padding: 2px 8px; border-radius: 5px; margin-right: 5px; font-size: 10px; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

@st.cache_data(ttl=1)
def load_data():
    try:
        c = pd.read_excel(FILE_NAME, sheet_name='Candidates')
        cr = pd.read_excel(FILE_NAME, sheet_name='Credentials')
        return c, cr
    except: return None, None

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'df' not in st.session_state:
    c, _ = load_data()
    st.session_state.df = c

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🏎️ SAE RECRUITMENT</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        user = st.text_input("Coordinator ID")
        pw = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            c, cr = load_data()
            if cr is not None:
                user_data = cr[(cr['Username'] == user) & (cr['Password'] == pw)]
                if not user_data.empty:
                    st.session_state.logged_in = True
                    st.session_state.role = user_data.iloc[0]['Role']
                    st.session_state.team = user_data.iloc[0]['Assigned Team']
                    st.rerun()
else:
    team = st.session_state.team
    
    # --- DYNAMIC TEAM HEADER WITH LOGO ---
    logo_url = LOGO_MAP.get(team, "https://img.icons8.com/fluency/96/formula-1.png")
    st.markdown(f"""
        <div class="header-box">
            <img src="{logo_url}" width="80">
            <h2 style="margin-top: 10px; color: white;">TEAM {team.upper()}</h2>
            <p style="color: #768390; font-size: 0.9rem;">Interview Control Dashboard</p>
        </div>
        """, unsafe_allow_html=True)

    search_query = st.text_input("🔍 Search Roll No or Name")
    
    df = st.session_state.df
    mask = (df['Pref 1'] == team) | (df['Pref 2'] == team) | (df['Pref 3'] == team) | (df['Pref 4'] == team)
    team_df = df[mask]
    
    if search_query:
        team_df = team_df[team_df['Full Name'].str.contains(search_query, case=False) | team_df['Roll No'].astype(str).str.contains(search_query)]

    for idx, row in team_df.iterrows():
        status = str(row['Status'])
        prefs = [row['Pref 1'], row['Pref 2'], row['Pref 3'], row['Pref 4']]
        
        is_interviewing = status == "In Progress"
        finished_this_team = f"Done:{team}" in status
        all_done = all(f"Done:{p}" in status for p in prefs)

        header = f"{row['Full Name']} - {row['Roll No']}"
        badge = '<span class="status-badge status-waiting">WAITING</span>'
        if all_done: badge = '<span class="status-badge status-completed">ALL DONE ✅</span>'
        elif is_interviewing: badge = '<span class="status-badge status-in-progress">LIVE NOW 🔴</span>'

        with st.expander(header):
            st.markdown(badge, unsafe_allow_html=True)
            
            tags_html = ""
            for p in prefs:
                if f"Done:{p}" in status:
                    tags_html += f'<span class="tag-done">✓ {p}</span> '
                else:
                    tags_html += f'<span class="tag-pending">{p}</span> '
            st.markdown(f"<div style='margin: 10px 0;'>{tags_html}</div>", unsafe_allow_html=True)

            if is_interviewing:
                st.info(f"⏱️ Started at: {row['Start Time']}")

            st.divider()
            c1, c2 = st.columns(2)
            
            if c1.button("▶ START", key=f"s_{idx}", use_container_width=True, disabled=(is_interviewing or finished_this_team)):
                st.session_state.df.at[idx, 'Status'] = "In Progress"
                st.session_state.df.at[idx, 'Start Time'] = datetime.now().strftime("%H:%M:%S")
                st.rerun()
            
            if c2.button("⏹ STOP", key=f"p_{idx}", use_container_width=True, disabled=not is_interviewing):
                clean_status = status.replace("In Progress", "").replace("Ready", "").strip(", ")
                st.session_state.df.at[idx, 'Status'] = f"{clean_status}, Done:{team}".strip(", ")
                st.session_state.df.at[idx, 'End Time'] = datetime.now().strftime("%H:%M:%S")
                st.rerun()

    # Logout in Sidebar
    with st.sidebar:
        st.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
