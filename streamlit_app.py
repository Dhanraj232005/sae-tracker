import streamlit as st
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="SAE Recruitment", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS: THE "SAE DARK" THEME ---
st.markdown("""
    <style>
    .header-box { background: linear-gradient(90deg, #1f242b 0%, #0d1117 100%); padding: 25px; border-radius: 15px; border-bottom: 3px solid #f1c40f; text-align: center; margin-bottom: 30px; }
    .status-badge { padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    .status-completed { background-color: #238636; color: white; }
    .status-in-progress { background-color: #da3633; color: white; animation: pulse 1.5s infinite; }
    .status-waiting { background-color: #30363d; color: #adbac7; border: 1px solid #444c56; }
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    .tag-done { color: #2ecc71; border: 1px solid #2ecc71; padding: 3px 10px; border-radius: 6px; margin-right: 6px; font-size: 11px; font-weight: bold; }
    .tag-pending { color: #f1c40f; border: 1px solid #f1c40f; padding: 3px 10px; border-radius: 6px; margin-right: 6px; font-size: 11px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE SETTINGS ---
FILE_NAME = "SAE_Interview_Database.xlsx"
LOGO_MAP = {
    "Miles": "https://img.icons8.com/fluency/96/lightning-bolt.png",
    "Racing": "https://img.icons8.com/fluency/96/f1-car.png",
    "Karting": "https://img.icons8.com/fluency/96/f1-car-side-view.png",
    "Speedster": "https://img.icons8.com/fluency/96/speed.png",
    "Phoenix": "https://img.icons8.com/fluency/96/fire-element.png"
}

@st.cache_data(ttl=1)
def load_data():
    try:
        # Load Main Data (Sheet name from Google Form)
        df = pd.read_excel(FILE_NAME, sheet_name='Form Responses 1')
        # Load Credentials
        creds = pd.read_excel(FILE_NAME, sheet_name='Credentials')
        
        # Initialize tracking columns if they are missing
        for col in ['Status', 'Start Time', 'End Time']:
            if col not in df.columns: df[col] = "Ready"
        return df, creds
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None, None

# --- SESSION & LOGIN LOGIC ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'df' not in st.session_state:
    c, _ = load_data()
    st.session_state.df = c

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🏎️ SAE RECRUITMENT LOGIN</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u = st.text_input("Coordinator ID")
        p = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            c, cr = load_data()
            if cr is not None:
                user_match = cr[(cr['Username'] == u) & (cr['Password'] == p)]
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.team = user_match.iloc[0]['Assigned Team']
                    st.rerun()
else:
    # --- DASHBOARD START ---
    team = st.session_state.team
    logo = LOGO_MAP.get(team, "https://img.icons8.com/fluency/96/formula-1.png")
    
    st.markdown(f'<div class="header-box"><img src="{logo}" width="70"><h2>TEAM {team.upper()}</h2><p>Interview Control Panel</p></div>', unsafe_allow_html=True)

    # --- TOP ACTIONS: SEARCH & EXPORT ---
    col_search, col_export = st.columns([3, 1])
    
    with col_search:
        search_q = st.text_input("🔍 Search SAP ID or Name", placeholder="Type to filter 200+ students...")

    with col_export:
        csv_data = st.session_state.df.to_csv(index=False).encode('utf-8')
        st.download_button("📤 EXPORT DATA", csv_data, f"SAE_Results_{team}.csv", use_container_width=True)

    # --- DATA FILTERING ---
    df = st.session_state.df
    pref_cols = ['Team preference list [1st]', 'Team preference list [2nd]', 'Team preference list [3rd]', 'Team preference list [4th]']
    
    # Filter for candidates who picked THIS team in ANY of their top 4 prefs
    mask = df[pref_cols].apply(lambda x: x.str.contains(team, na=False)).any(axis=1)
    team_df = df[mask]
    
    if search_q:
        team_df = team_df[team_df['Full Name'].str.contains(search_q, case=False, na=False) | 
                         team_df['SAP ID'].astype(str).str.contains(search_q, na=False)]

    # --- CANDIDATE CARDS ---
    for idx, row in team_df.iterrows():
        status = str(row['Status'])
        user_prefs = [row[c] for c in pref_cols if pd.notna(row[c])]
        
        is_live = status == "In Progress"
        is_done_here = f"Done:{team}" in status
        is_fully_done = all(f"Done:{p}" in status for p in user_prefs)

        # Header Badge
        badge = '<span class="status-badge status-waiting">WAITING</span>'
        if is_fully_done: badge = '<span class="status-badge status-completed">COMPLETED ✅</span>'
        elif is_live: badge = '<span class="status-badge status-in-progress">LIVE NOW 🔴</span>'

        with st.expander(f"{row['Full Name']} ({row['SAP ID']})"):
            st.markdown(badge, unsafe_allow_html=True)
            
            # Show Pref Tags (Green for Done, Yellow for Pending)
            tags = "".join([f'<span class="{"tag-done" if f"Done:{p}" in status else "tag-pending"}">{"✓ " if f"Done:{p}" in status else ""}{p}</span> ' for p in user_prefs])
            st.markdown(f"<div style='margin: 15px 0;'>{tags}</div>", unsafe_allow_html=True)

            if is_live: st.error(f"⏱️ Interview Started at: {row['Start Time']}")

            st.divider()
            b1, b2 = st.columns(2)
            
            # Start Button
            if b1.button("▶ START", key=f"start_{idx}", use_container_width=True, disabled=(is_live or is_done_here)):
                st.session_state.df.at[idx, 'Status'] = "In Progress"
                st.session_state.df.at[idx, 'Start Time'] = datetime.now().strftime("%H:%M:%S")
                st.rerun()
            
            # Stop Button
            if b2.button("⏹ STOP", key=f"stop_{idx}", use_container_width=True, disabled=not is_live):
                clean_stat = status.replace("In Progress", "").replace("Ready", "").strip(", ")
                st.session_state.df.at[idx, 'Status'] = f"{clean_stat}, Done:{team}".strip(", ")
                st.session_state.df.at[idx, 'End Time'] = datetime.now().strftime("%H:%M:%S")
                st.rerun()

    # --- SIDEBAR LOGOUT ---
    with st.sidebar:
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
