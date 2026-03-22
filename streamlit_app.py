import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SAE Interview Tracker", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS FOR SMART STATUS ---
st.markdown("""
    <style>
    .status-badge { padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    .status-completed { background-color: #238636; color: white; } /* Green */
    .status-incomplete { background-color: #da3633; color: white; } /* Red */
    .team-highlight { color: #f1c40f; font-weight: bold; border: 1px solid #f1c40f; padding: 2px 5px; border-radius: 5px; margin-right: 5px;}
    .card-info { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

@st.cache_data(ttl=5) # Ultra-fast 5s refresh
def load_data():
    try:
        c = pd.read_excel(FILE_NAME, sheet_name='Candidates')
        cr = pd.read_excel(FILE_NAME, sheet_name='Credentials')
        return c, cr
    except:
        return None, None

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'df' not in st.session_state:
    c, _ = load_data()
    st.session_state.df = c

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title("🏎️ SAE Dashboard")
    user = st.text_input("Username")
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
    st.header(f"Interviewing for: {team}")

    # Sidebar
    with st.sidebar:
        st.write(f"Room: {team}")
        csv = st.session_state.df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Export Results", csv, "sae_final.csv", use_container_width=True)
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    df = st.session_state.df

    # Logic to filter candidates for the current team
    mask = (df['Pref 1'] == team) | (df['Pref 2'] == team) | (df['Pref 3'] == team) | (df['Pref 4'] == team)
    display_df = df[mask]

    for idx, row in display_df.iterrows():
        # --- TRACKING LOGIC ---
        # We check if the 'Status' column contains the names of the teams they've finished
        current_status = str(row['Status'])
        prefs = [row['Pref 1'], row['Pref 2'], row['Pref 3'], row['Pref 4']]
        
        # Check which teams are missing
        # This assumes 'Status' gets updated to something like "Completed (Miles), Completed (Racing)"
        completed_teams = [p for p in prefs if p in current_status]
        missing_teams = [p for p in prefs if p not in current_status]

        is_done = len(missing_teams) == 0
        
        # --- CARD UI ---
        with st.expander(f"{row['Full Name']} ({row['Roll No']})"):
            if is_done:
                st.markdown('<span class="status-badge status-completed">✅ ALL INTERVIEWS COMPLETED</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-badge status-incomplete">⚠️ INCOMPLETE</span>', unsafe_allow_html=True)
                st.write("Pending Interviews:")
                highlighted_teams = "".join([f'<span class="team-highlight">{t}</span>' for t in missing_teams])
                st.markdown(highlighted_teams, unsafe_allow_html=True)

            st.divider()
            
            c1, c2 = st.columns(2)
            if c1.button("▶ START", key=f"start_{idx}", use_container_width=True):
                st.session_state.df.at[idx, 'Status'] = "In Progress"
                st.rerun()
            
            if c2.button("⏹ STOP", key=f"stop_{idx}", use_container_width=True):
                # We append the team name to the status so we know they finished THIS team
                new_status = f"{current_status}, {team}".replace("Ready, ", "").replace("nan, ", "")
                st.session_state.df.at[idx, 'Status'] = new_status
                st.session_state.df.at[idx, 'End Time'] = datetime.now().strftime("%H:%M")
                st.rerun()
