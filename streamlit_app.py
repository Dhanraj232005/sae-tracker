import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SAE Interview Tracker", layout="wide")

# --- LOAD LOCAL EXCEL FILE ---
FILE_NAME = "SAE_Interview_Database.xlsx"

@st.cache_data
def load_data():
    # Reading the two tabs from your uploaded Excel
    candidates = pd.read_excel(FILE_NAME, sheet_name='Candidates')
    creds = pd.read_excel(FILE_NAME, sheet_name='Credentials')
    return candidates, creds

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'df' not in st.session_state:
    candidates, _ = load_data()
    st.session_state.df = candidates

# --- LOGIN LOGIC ---
if not st.session_state.logged_in:
    with st.form("login"):
        st.header("🏎️ SAE Coordinator Login")
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
                st.error("Invalid Username/Password")
else:
    # --- APP CONTENT ---
    st.sidebar.title(f"Team: {st.session_state.team}")
    
    # Download Button (Essential for Option B)
    csv = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Download Final Data", csv, "interview_results.csv", "text/csv")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    df = st.session_state.df

    if st.session_state.role == "GC":
        st.header("Admin Master Dashboard")
        st.dataframe(df)
    else:
        team = st.session_state.team
        st.header(f"Interviewing for: {team}")
        
        # Filter logic
        mask = (df['Pref 1'] == team) | (df['Pref 2'] == team) | (df['Pref 3'] == team) | (df['Pref 4'] == team)
        team_df = df[mask]

        for idx, row in team_df.iterrows():
            with st.expander(f"{row['Full Name']} ({row['Roll No']}) - {row['Status']}"):
                c1, c2 = st.columns(2)
                if c1.button("START TIMER", key=f"s_{idx}"):
                    st.session_state.df.at[idx, 'Start Time'] = datetime.now().strftime("%H:%M:%S")
                    st.session_state.df.at[idx, 'Status'] = "In Progress"
                    st.rerun()
                if c2.button("STOP TIMER", key=f"p_{idx}"):
                    st.session_state.df.at[idx, 'End Time'] = datetime.now().strftime("%H:%M:%S")
                    st.session_state.df.at[idx, 'Status'] = "Completed"
                    st.rerun()
