import streamlit as st
import pandas as pd

st.set_page_config(page_title="SAE Recruitment Portal", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stProgress > div > div > div > div { background-image: none; }
    
    .header-box { background: #1f242b; padding: 20px; border-radius: 10px; border-bottom: 3px solid #f1c40f; text-align: center; margin-bottom: 20px; }
    
    /* In Process Section Styling */
    .process-section { background-color: #1e3a5f; padding: 20px; border-radius: 10px; border: 2px solid #3498db; margin-bottom: 25px; }
    .process-name { color: #3498db; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    
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
    st.session_state.status_map = {} # Possible: 'In Process', 'Done', or 'Pending'
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

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
    
    # Filter by Team Preference
    mask = df_all[pref_cols].apply(lambda x: x.str.contains(team, na=False, case=False)).any(axis=1)
    team_df = df_all[mask]

    # --- CATEGORIZE CANDIDATES ---
    process_list, pending_list, done_list = [], [], []
    for _, row in team_df.iterrows():
        sid = str(row['SAP ID'])
        status = st.session_state.status_map.get(sid, "Pending")
        if status == "In Process": process_list.append(row)
        elif status == "Done": done_list.append(row)
        else: pending_list.append(row)

    # --- 1. INTERVIEW IN PROCESS SECTION ---
    if process_list:
        st.markdown('<div class="process-section">', unsafe_allow_html=True)
        st.subheader("🔵 Interview In Process")
        for row in process_list:
            sid = str(row['SAP ID'])
            st.markdown(f'<div class="process-name">{row["Full Name"]} ({sid})</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("✅ COMPLETE", key=f"comp_{sid}", use_container_width=True):
                st.session_state.status_map[sid] = "Done"
                st.balloons()
                st.rerun()
            if c2.button("🔙 MOVE TO QUEUE", key=f"back_{sid}", use_container_width=True):
                st.session_state.status_map[sid] = "Pending"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 2. ACTIVE QUEUE (PENDING) ---
    st.subheader(f"📋 Active Queue ({len(pending_list)})")
    query = st.text_input("🔍 Search Name/SAP ID")
    
    filtered_pending = []
    for row in pending_list:
        if query:
            if query.lower() in str(row['Full Name']).lower() or query.lower() in str(row['SAP ID']).lower():
                filtered_pending.append(row)
        else:
            filtered_pending.append(row)

    for row in filtered_pending:
        sid = str(row['SAP ID'])
        with st.expander(f"➔ {row['Full Name']} ({sid})"):
            tags = "".join([f'<span class="tag-pending">{row[c]}</span>' for c in pref_cols if pd.notna(row[c])])
            st.markdown(f"<div style='margin-bottom:15px;'>{tags}</div>", unsafe_allow_html=True)
            if st.button("▶ START INTERVIEW", key=f"s_{sid}", use_container_width=True):
                st.session_state.status_map[sid] = "In Process"
                st.rerun()

    # --- 3. FINISHED SECTION (DONE) ---
    if done_list:
        st.markdown("<div class='done-section'>", unsafe_allow_html=True)
        st.subheader("🏁 Finished Interviews")
        for row in done_list:
            sid = str(row['SAP ID'])
            col_a, col_b = st.columns([5, 1])
            col_a.write(f"✅ **{row['Full Name']}** ({sid})")
            if col_b.button("Reset", key=f"u_{sid}", use_container_width=True):
                st.session_state.status_map[sid] = "Pending"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
