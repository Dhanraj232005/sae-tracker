import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SAE Team Portal", layout="wide", initial_sidebar_state="collapsed")

# --- TEAM LOGO MAPPING ---
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
    .header-box { background: linear-gradient(90deg, #1f242b 0%, #0d1117 100%); padding: 20px; border-radius: 15px; border-bottom: 2px solid #f1c40f; text-align: center; margin-bottom: 25px; }
    .status-badge { padding: 4px 12px; border-radius: 15px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    .status-completed { background-color: #238636; color: white; }
    .status-in-progress { background-color: #da3633; color: white; animation: pulse 1.5s infinite; }
    .status-waiting { background-color: #30363d; color: #adbac7; }
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    .tag-done { color: #2ecc71; border: 1px solid #2ecc71; padding: 2px 8px; border-radius: 5px; margin-right: 5px; font-size: 10px; font-weight: bold; }
    .tag-pending { color: #f1c40f; border: 1px solid #f1c40f; padding: 2px 8px; border-radius: 5px; margin-right: 5px; font-size: 10px; }
    </style>
    """, unsafe_allow_html=True)

# FILE NAMES - Update these to match your GitHub exactly!
MAIN_DB = "SAE_Interview_Database.xlsx"
SECOND_DB = "Second_Sheet_Name.xlsx" # <-- CHANGE THIS TO YOUR NEW FILE NAME

@st.cache_data(ttl=1)
def load_all_data():
    try:
        c = pd.read_excel(MAIN_DB, sheet_name='Candidates')
        cr = pd.read_excel(MAIN_DB, sheet_name='Credentials')
        # Load the second file
        extra_data = pd.read_excel(SECOND_DB) 
        return c, cr, extra_data
    except Exception as e:
        return None, None, None

# Session Logic
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'df' not in st.session_state:
    c, _, _ = load_all_data()
    st.session_state.df = c

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🏎️ SAE RECRUITMENT</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        user = st.text_input("Coordinator ID")
        pw = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            c, cr, _ = load_all_data()
            if cr is not None:
                user_data = cr[(cr['Username'] == user) & (cr['Password'] == pw)]
                if not user_data.empty:
                    st.session_state.logged_in = True
                    st.session_state.role = user_data.iloc[0]['Role']
                    st.session_state.team = user_data.iloc[0]['Assigned Team']
                    st.rerun()
else:
    team = st.session_state.team
    logo_url = LOGO_MAP.get(team, "https://img.icons8.com/fluency/96/formula-1.png")
    
    # Header
    st.markdown(f'<div class="header-box"><img src="{logo_url}" width="60"><h2>TEAM {team.upper()}</h2></div>', unsafe_allow_html=True)

    # --- TOP ACTIONS: EXPORT & SEARCH ---
    col1, col2 = st.columns([3, 1])
    search_query = col1.text_input("🔍 Search Roll No or Name")
    
    # Export Button is now prominently at the top right
    csv = st.session_state.df.to_csv(index=False).encode('utf-8')
    col2.download_button("📤 EXPORT ALL", csv, f"SAE_Results_{team}.csv", use_container_width=True)

    # Filtering Logic
    df = st.session_state.df
    mask = (df['Pref 1'] == team) | (df['Pref 2'] == team) | (df['Pref 3'] == team) | (df['Pref 4'] == team)
    team_df = df[mask]
    
    if search_query:
        team_df = team_df[team_df['Full Name'].str.contains(search_query, case=False) | team_df['Roll No'].astype(str).str.contains(search_query)]

    # Display List
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
            
            # Show Pref Tags
            tags_html = "".join([f'<span class="{"tag-done" if f"Done:{p}" in status else "tag-pending"}">{"✓ " if f"Done:{p}" in status else ""}{p}</span> ' for p in prefs])
            st.markdown(f"<div style='margin: 10px 0;'>{tags_html}</div>", unsafe_allow_html=True)

            if is_interviewing: st.info(f"⏱️ Started at: {row['Start Time']}")

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

    # Sidebar Logout
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
