import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SAE Interview Tracker", layout="wide", initial_sidebar_state="collapsed")

# --- PRO UI STYLING ---
st.markdown("""
    <style>
    .status-badge { padding: 4px 12px; border-radius: 15px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    .status-completed { background-color: #238636; color: white; }
    .status-in-progress { background-color: #da3633; color: white; animation: pulse 1.5s infinite; }
    .status-waiting { background-color: #30363d; color: #adbac7; border: 1px solid #444c56; }
    
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    
    /* Green for Done, Yellow for Pending */
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
    st.title("🏎️ SAE RECRUITMENT")
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
    st.markdown(f"<h1 style='text-align: center;'>Room: {team}</h1>", unsafe_allow_html=True)

    # Search Bar
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

        # UI Header
        header = f"{row['Full Name']} - {row['Roll No']}"
        badge = '<span class="status-badge status-waiting">WAITING</span>'
        if all_done: badge = '<span class="status-badge status-completed">ALL DONE ✅</span>'
        elif is_interviewing: badge = '<span class="status-badge status-in-progress">LIVE NOW 🔴</span>'

        with st.expander(header):
            st.markdown(badge, unsafe_allow_html=True)
            
            # --- SHOW ALL PREFERENCES WITH COLOR CODING ---
            st.write("Interview Status:")
            tags_html = ""
            for p in prefs:
                if f"Done:{p}" in status:
                    tags_html += f'<span class="tag-done">✓ {p}</span> '
                else:
                    tags_html += f'<span class="tag-pending">{p}</span> '
            st.markdown(tags_html, unsafe_allow_html=True)

            if is_interviewing:
                st.write(f"Started at: {row['Start Time']}")

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
