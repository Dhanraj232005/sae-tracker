import streamlit as st
import pandas as pd

st.set_page_config(page_title="SAE Recruitment Portal", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    .header-box { background: #1f242b; padding: 20px; border-radius: 10px; border-bottom: 3px solid #f1c40f; text-align: center; margin-bottom: 20px; }
    /* Tag Styles */
    .tag-done { background-color: #238636; color: white; padding: 2px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; font-weight: bold; }
    .tag-pending { color: #f1c40f; border: 1px solid #f1c40f; padding: 2px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; }
    /* Sections */
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
    except Exception as e:
        st.error(f"Excel Error: Ensure tab names are 'Form Responses 1' and 'Credentials'. Details: {e}")
        return None, None

# --- STATE MANAGEMENT ---
if 'status_map' not in st.session_state:
    st.session_state.status_map = {} 
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
    
    # Filter by Team Preference
    mask = df_all[pref_cols].apply(lambda x: x.str.contains(team, na=False, case=False)).any(axis=1)
    team_df = df_all[mask]

    # Search and Export Header
    c_search, c_export = st.columns([3, 1])
    query = c_search.text_input("🔍 Search SAP ID or Name")
    csv = team_df.to_csv(index=False).encode('utf-8')
    c_export.download_button("📤 EXPORT CSV", csv, f"{team}_Recruitment_Data.csv", use_container_width=True)

    if query:
        team_df = team_df[team_df['Full Name'].str.contains(query, case=False, na=False) | team_df['SAP ID'].astype(str).str.contains(query, na=False)]

    pending_list, done_list = [], []
    for _, row in team_df.iterrows():
        sid = str(row['SAP ID'])
        if st.session_state.status_map.get(sid) == "Done": done_list.append(row)
        else: pending_list.append(row)

    # --- ACTIVE QUEUE ---
    st.subheader(f"📋 Active Queue ({len(pending_list)})")
    for row in pending_list:
        sid = str(row['SAP ID'])
        with st.expander(f"➔ {row['Full Name']} ({sid})"):
            tags = "".join([f'<span class="tag-pending">{row[c]}</span>' for c in pref_cols if pd.notna(row[c])])
            st.markdown(f"<div style='margin
