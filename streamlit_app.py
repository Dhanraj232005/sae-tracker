import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SAE Interview Tracker", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS: PRO AESTHETICS & LIVE COLORS ---
st.markdown("""
    <style>
    .status-badge { padding: 4px 12px; border-radius: 15px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    .status-completed { background-color: #238636; color: white; } /* Green */
    .status-in-progress { background-color: #da3633; color: white; animation: pulse 1.5s infinite; } /* Red Pulse */
    .status-waiting { background-color: #30363d; color: #adbac7; border: 1px solid #444c56; }
    
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
    
    .timer-live { color: #f1c40f; font-weight: bold; font-family: monospace; font-size: 1rem; }
    .team-tag { background: #1f242b; color: #f1c40f; border: 1px solid #f1c40f; padding: 2px 8px; border-radius: 5px; margin-right: 5px; font-size: 10px; }
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
    st.markdown(f"<h1 style='text-align: center;'>Room: {team}</h1>", unsafe_allow_html=True)

    # --- SEARCH & COUNTER ---
    search_col, count_col = st.columns([3, 1])
    search_query = search_col.text_input("🔍 Search 200+ Candidates (Name or Roll No)")
    
    # --- DATA PROCESSING ---
    df = st.session_state.df
    mask = (df['Pref 1'] == team) | (df['Pref 2'] == team) | (df['Pref 3'] == team) | (df['Pref 4'] == team)
    team_df = df[mask]
    
    if search_query:
        team_df = team_df[team_df['Full Name'].str.contains(search_query, case=False) | team_df['Roll No'].astype(str).str.contains(search_query)]

    done_count = len(df[df['Status'].str.contains("Done", na=False)])
    count_col.metric("Total Interviews Done", done_count)

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("Coordinator Tools")
        csv = st.session_state.df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DOWNLOAD DATA", csv, "SAE_Final_Results.csv", use_container_width=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- CANDIDATE LIST ---
    for idx, row in team_df.iterrows():
        status = str(row['Status'])
        prefs = [row['Pref 1'], row['Pref 2'], row['Pref 3'], row['Pref 4']]
        
        is_interviewing = status == "In Progress"
        finished_this_team = f"Done:{team}" in status
        all_done = all(f"Done:{p}" in status for p in prefs)

        # UI Header Logic
        if all_done:
            header = f"✅ {row['Full Name']} - {row['Roll No']}"
            badge = '<span class="status-badge status-completed">COMPLETED</span>'
        elif is_interviewing:
            header = f"🔴 {row['Full Name']} - {row['Roll No']}"
            badge = '<span class="status-badge status-in-progress">INTERVIEWING...</span>'
        else:
            header = f"⏳ {row['Full Name']} - {row['Roll No']}"
            badge = '<span class="status-badge status-waiting">WAITING</span>'

        with st.expander(header):
            st.markdown(badge, unsafe_allow_html=True)
            
            # Show Pending Teams
            if not all_done:
                missing = [p for p in prefs if f"Done:{p}" not in status]
                st.markdown("Remaining: " + "".join([f'<span class="team-tag">{t}</span>' for t in missing]), unsafe_allow_html=True)

            # --- LIVE TIMER DISPLAY ---
            if is_interviewing:
                st.markdown(f"Started at: <span class='timer-live'>{row['Start Time']}</span>", unsafe_allow_html=True)
            elif finished_this_team:
                st.write(f"Done at: {row['End Time']}")

            st.divider()
            c1, c2 = st.columns(2)
            
            if c1.button("▶ START", key=f"start_{idx}", use_container_width=True, disabled=(is_interviewing or finished_this_team)):
                st.session_state.df.at[idx, 'Status'] = "In Progress"
                st.session_state.df.at[idx, 'Start Time'] = datetime.now().strftime("%H:%M:%S")
                st.rerun()
            
            if c2.button("⏹ STOP", key=f"stop_{idx}", use_container_width=True, disabled=not is_interviewing):
                clean_status = status.replace("In Progress", "").replace("Ready", "").strip(", ")
                st.session_state.df.at[idx, 'Status'] = f"{clean_status}, Done:{team}".strip(", ")
                st.session_state.df.at[idx, 'End Time'] = datetime.now().strftime("%H:%M:%S")
                st.rerun()
