import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SAE Recruitment Portal", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    .header-box { background: #1f242b; padding: 20px; border-radius: 10px; border-bottom: 3px solid #f1c40f; text-align: center; margin-bottom: 20px; }
    .status-badge { padding: 4px 12px; border-radius: 15px; font-size: 10px; font-weight: bold; }
    .status-in-progress { background-color: #da3633; color: white; }
    .status-done { background-color: #238636; color: white; }
    .tag-done { color: #2ecc71; border: 1px solid #2ecc71; padding: 2px 8px; border-radius: 5px; margin-right: 4px; font-size: 10px; }
    .tag-pending { color: #f1c40f; border: 1px solid #f1c40f; padding: 2px 8px; border-radius: 5px; margin-right: 4px; font-size: 10px; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_excel(FILE_NAME, sheet_name='Form Responses 1')
        creds = pd.read_excel(FILE_NAME, sheet_name='Credentials')
        if 'Status' not in df.columns: df['Status'] = "Ready"
        return df, creds
    except Exception as e:
        st.error(f"Error loading Excel: {e}")
        return None, None

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>SAE RECRUITMENT LOGIN</h2>", unsafe_allow_html=True)
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        df_all, cr = load_data()
        user_match = cr[(cr['Username'] == u) & (cr['Password'] == p)]
        if not user_match.empty:
            st.session_state.logged_in = True
            st.session_state.team = user_match.iloc[0]['Assigned Team']
            st.rerun()
else:
    team = st.session_state.team
    st.markdown(f'<div class="header-box"><h2>TEAM {team.upper()}</h2></div>', unsafe_allow_html=True)

    df_all, _ = load_data()
    pref_cols = [f'Team preference list [{i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"}]' for i in range(1, 12)]
    
    # Filter for candidates who chose THIS team in any of the 11 slots
    mask = df_all[pref_cols].apply(lambda x: x.str.contains(team, na=False, case=False)).any(axis=1)
    team_df = df_all[mask]

    search = st.text_input("🔍 Search Name or SAP ID")
    if search:
        team_df = team_df[team_df['Full Name'].str.contains(search, case=False, na=False) | team_df['SAP ID'].astype(str).str.contains(search, na=False)]

    for idx, row in team_df.iterrows():
        status = str(row['Status'])
        user_prefs = [row[c] for c in pref_cols if pd.notna(row[c])]
        
        with st.expander(f"{row['Full Name']} ({row['SAP ID']})"):
            # Show which teams have already finished with this candidate
            tags = ""
            for p in user_prefs:
                style = "tag-done" if f"Done:{p}" in status else "tag-pending"
                tags += f'<span class="{style}">{p}</span> '
            st.markdown(f"<div>{tags}</div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            if col1.button("▶ START", key=f"start_{idx}", use_container_width=True):
                # In a real app, you'd save back to Excel here. 
                # For now, we update the local state.
                st.success(f"Interview Started for {row['Full Name']}")
            if col2.button("⏹ COMPLETE", key=f"stop_{idx}", use_container_width=True):
                st.balloons()
                st.info(f"Interview Completed for {team}")
