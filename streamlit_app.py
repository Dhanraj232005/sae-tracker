import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SAE Interview Tracker", layout="wide")

# --- TEAMS LIST ---
TEAMS = ["Speedsters", "Karting", "Racing", "Miles", "Impulse", "Phoenix", "Skylark", "Kronos", "Astra", "Robocon", "Helios"]

st.title("🏎️ SAE Interview Dashboard")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    candidates = conn.read(worksheet="Candidates", ttl=0)
    creds = conn.read(worksheet="Credentials", ttl=0)
    return candidates, creds

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("login"):
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            _, creds = load_data()
            user_data = creds[(creds['Username'] == user) & (creds['Password'] == pw)]
            if not user_data.empty:
                st.session_state.logged_in = True
                st.session_state.role = user_data.iloc[0]['Role']
                st.session_state.team = user_data.iloc[0]['Assigned Team']
                st.rerun()
            else:
                st.error("Wrong credentials")
else:
    candidates, _ = load_data()
    st.sidebar.button("Refresh Data")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    if st.session_state.role == "GC":
        st.header("Admin Master View")
        search = st.text_input("Search Candidate by Name or Roll No")
        if search:
            candidates = candidates[candidates['Full Name'].str.contains(search, case=False) | candidates['Roll No'].astype(str).str.contains(search)]
        st.dataframe(candidates)
    
    else:
        team = st.session_state.team
        st.header(f"Team Room: {team}")
        
        # Filter for Top 4 Preferences
        mask = (candidates['Pref 1'] == team) | (candidates['Pref 2'] == team) | (candidates['Pref 3'] == team) | (candidates['Pref 4'] == team)
        team_df = candidates[mask]

        for idx, row in team_df.iterrows():
            with st.expander(f"{row['Full Name']} ({row['Roll No']}) - {row['Status']}"):
                c1, c2 = st.columns(2)
                if c1.button("START", key=f"s_{idx}"):
                    candidates.at[idx, 'Start Time'] = datetime.now().strftime("%H:%M:%S")
                    candidates.at[idx, 'Status'] = "In Progress"
                    conn.update(worksheet="Candidates", data=candidates)
                    st.rerun()
                if c2.button("STOP", key=f"p_{idx}"):
                    candidates.at[idx, 'End Time'] = datetime.now().strftime("%H:%M:%S")
                    candidates.at[idx, 'Status'] = "Completed"
                    conn.update(worksheet="Candidates", data=candidates)
                    st.rerun()
