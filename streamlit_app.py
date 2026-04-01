import streamlit as st
import pandas as pd

st.set_page_config(page_title="SAE Recruitment Portal", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    /* Hide Streamlit Loading Bar and Menu */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stProgress > div > div > div > div { background-image: none; }
    
    .header-box { background: #1f242b; padding: 20px; border-radius: 10px; border-bottom: 3px solid #f1c40f; text-align: center; margin-bottom: 20px; }
    
    /* Live Interview Section Styling */
    .live-section { background-color: #0e2a1a; padding: 20px; border-radius: 10px; border: 2px solid #238636; margin-bottom: 25px; }
    .live-name { color: #2ecc71; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    
    /* Tag Styles */
    .tag-pending { color: #f1c40f; border: 1px solid #f1c40f; padding: 2px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; }
    
    /* Finished Section Styling */
    .done-section { background-color: #1a1c23; padding: 15px; border-radius: 10px; border-left: 5px solid #238636; margin-top: 30px; }
    
    .stButton>button { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_excel(FILE_NAME, sheet_name='Form Responses 1')
        creds = pd.read_excel(FILE_NAME, sheet_name='Credentials')
        return df, creds
    except:
        return None, None

# --- STATE MANAGEMENT ---
if 'status_map' not in st.session_state:
    st.session_state.status_map = {} # Tracks: 'Started', 'Done', or 'Pending'
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

# --- LOGIN ---
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
                    st.session_state.team = user_match.iloc[0]['Assigned Team']
                    st.rerun()
                else: st.error("Invalid Credentials")
else:
    team = st.session_state.team
    st.markdown(f'<div class="header-box"><h1>TEAM {team.upper()}</h1></div>', unsafe_allow_html=True)

    df_all, _ = load_data()
    pref_cols = [f'Team preference list [{i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"}]' for i in range(1, 12)]
    
    mask = df_all[pref_cols].apply(lambda x: x.str.contains(team, na=False, case=False)).any(axis=1)
    team_df = df_all[mask]

    # --- LIVE INTERVIEW SECTION (STARTED) ---
    live_student = None
    for _, row in team_df.iterrows():
        if st.session_state.status_map.get(str(row['SAP ID'])) == "Started":
            live_student = row
            break

    if live_student is not None:
        sid = str(live_student['SAP ID'])
        st.markdown(f"""
            <div class="live-section">
                <div style="color: #2ecc71; font-weight: bold;">⚡ CURRENTLY INTERVIEWING</div>
                <div class="live-name">{live_student['Full Name']} ({sid})</div>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("✅ MARK AS COMPLETE", key=f"finish_{sid}", use_container_width=True):
            st.session_state.status_map[sid] = "Done"
            st.balloons()
            st.rerun()
        if c2.button("🔙 MOVE BACK TO QUEUE", key=f"back_{sid}", use_container_width=True):
            st.session_state.status_map[sid] = "Pending"
            st.rerun()
        st.markdown("---")

    # --- SEARCH & QUEUES ---
    query = st.text_input("🔍 Search SAP ID or Name")
    if query:
        team_df = team_df[team_df['Full Name'].str.contains(query, case=False, na=False) | team_df['SAP ID'].astype(str).str.contains(query, na=False)]

    pending_list, done_list = [], []
    for _, row in team_df.iterrows():
        status = st.session_state.status_map.get(str(row['SAP ID']), "Pending")
        if status == "Done": done_list.append(row)
        elif status == "Pending": pending_list.append(row)

    # --- ACTIVE QUEUE ---
    st.subheader(f"📋 Waiting List ({len(pending_list)})")
    for row in pending_list:
        sid = str(row['SAP ID'])
        with st.expander(f"➔ {row['Full Name']} ({sid})"):
            tags = "".join([f'<span class="tag-pending">{row[c]}</span>' for c in pref_cols
