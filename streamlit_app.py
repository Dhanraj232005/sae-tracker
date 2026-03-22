import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SAE Interview Tracker", layout="wide", initial_sidebar_state="collapsed")

# --- PRO AESTHETIC CSS ---
st.markdown("""
    <style>
    .status-badge { padding: 4px 12px; border-radius: 15px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    .status-completed { background-color: #238636; color: white; } /* Green */
    .status-incomplete { background-color: #30363d; color: #adbac7; border: 1px solid #444c56; }
    .status-in-progress { background-color: #da3633; color: white; animation: pulse 2s infinite; } /* Red Pulse */
    
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    
    .team-highlight { color: #f1c40f; font-weight: bold; border: 1px solid #f1c40f; padding: 2px 6px; border-radius: 5px; margin-right: 5px; font-size: 10px; }
    .timer-text { font-family: monospace; color: #768390; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

@st.cache_data(ttl=2)
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
    st.title("🏎️ SAE RECRUITMENT")
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
    st.markdown(f"<h2 style='text-align: center;'>Room: {team}</h2>", unsafe_allow_html=True)

    with st.sidebar:
        st.header("Admin Tools")
        csv = st.session_state.df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DOWNLOAD DATA", csv, "SAE_Tracker_Final.csv", use_container_width=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    df = st.session_state.df
    mask = (df['Pref 1'] == team) | (df['Pref 2'] == team) | (df['Pref 3'] == team) | (df['Pref 4'] == team)
    display_df = df[mask]

    for idx, row in display_df.iterrows():
        current_status = str(row['Status'])
        prefs = [row['Pref 1'], row['Pref 2'], row['Pref 3'], row['Pref 4']]
        
        # Checking logic
        finished_this_team = f"Done:{team}" in current_status
        all_finished = all(f"Done:{p}" in current_status for p in prefs)
        is_interviewing = current_status == "In Progress"
        
        # Color Logic
        badge_html = ""
        if all_finished:
            badge_html = '<span class="status-badge status-completed">✅ ALL DONE</span>'
        elif is_interviewing:
            badge_html = '<span class="status-badge status-in-progress">🔴 INTERVIEWING NOW...</span>'
        else:
            badge_html = '<span class="status-badge status-incomplete">⏳ WAITING</span>'

        with st.expander(f"{row['Full Name']} ({row['Roll No']})"):
            st.markdown(badge_html, unsafe_allow_html=True)
            
            # Show missing teams
            missing = [p for p in prefs if f"Done:{p}" not in current_status]
            if not all_finished and not is_interviewing:
                st.write("Remaining:")
                st.markdown(" ".join([f'<span class="team-highlight">{t}</span>' for t in missing]), unsafe_allow_html=True)

            # Timer Info
            if row.get('Start Time') and not pd.isna(row['Start Time']):
                st.markdown(f"<p class='timer-text'>Started at: {row['Start Time']}</p>", unsafe_allow_html=True)

            st.divider()
            c1, c2 = st.columns(2)
            
            # START BUTTON (Only show if not currently interviewing or finished)
            if c1.button("▶ START", key=f"start_{idx}", use_container_width=True, disabled=(is_interviewing or finished_this_team)):
                st.session_state.df.at[idx, 'Status'] = "In Progress"
                st.session_state.df.at[idx, 'Start Time'] = datetime.now().strftime("%H:%M:%S")
                st.rerun()
            
            # STOP BUTTON (Only show if currently interviewing)
            if c2.button("⏹ STOP", key=f"stop_{idx}", use_container_width=True, disabled=not is_interviewing):
                updated_status = f"{current_status}, Done:{team}".replace("Ready, ", "").replace("In Progress, ", "").replace("In Progress", f"Done:{team}")
                st.session_state.df.at[idx, 'Status'] = updated_status
                st.session_state.df.at[idx, 'End Time'] = datetime.now().strftime("%H:%M:%S")
                st.rerun()
