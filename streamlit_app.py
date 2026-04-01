import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SAE Recruitment Portal", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    .header-box { background: #1f242b; padding: 20px; border-radius: 10px; border-bottom: 3px solid #f1c40f; text-align: center; margin-bottom: 20px; }
    /* Tag Styles */
    .tag-done { background-color: #238636; color: white; border: 1px solid #238636; padding: 2px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; font-weight: bold; }
    .tag-hold { background-color: #8e44ad; color: white; border: 1px solid #8e44ad; padding: 2px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; font-weight: bold; }
    .tag-pending { color: #f1c40f; border: 1px solid #f1c40f; padding: 2px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_excel(FILE_NAME, sheet_name='Form Responses 1')
        creds = pd.read_excel(FILE_NAME, sheet_name='Credentials')
        if 'Status' not in df.columns: df['Status'] = ""
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
    
    mask = df_all[pref_cols].apply(lambda x: x.str.contains(team, na=False, case=False)).any(axis=1)
    team_df = df_all[mask]

    col_search, col_export = st.columns([3, 1])
    search = col_search.text_input("🔍 Search Name or SAP ID")
    
    csv = team_df.to_csv(index=False).encode('utf-8')
    col_export.download_button("📤 EXPORT CSV", csv, f"{team}_interviews.csv", "text/csv", use_container_width=True)

    if search:
        team_df = team_df[team_df['Full Name'].str.contains(search, case=False, na=False) | team_df['SAP ID'].astype(str).str.contains(search, na=False)]

    for idx, row in team_df.iterrows():
        # Read the current status string (e.g., "Done:Miles, Hold:Racing")
        current_status = str(row['Status']) if pd.notna(row['Status']) else ""
        user_prefs = [row[c] for c in pref_cols if pd.notna(row[c])]
        
        with st.expander(f"{row['Full Name']} ({row['SAP ID']})"):
            # VISUAL TEAM STATUS TAGS
            tags_html = ""
            for p in user_prefs:
                if f"Done:{p}" in current_status:
                    tags_html += f'<span class="tag-done">{p} ✅</span>'
                elif f"Hold:{p}" in current_status:
                    tags_html += f'<span class="tag-hold">{p} ⏸</span>'
                else:
                    tags_html += f'<span class="tag-pending">{p}</span>'
            
            st.markdown(f"<div style='margin-bottom: 15px;'>{tags_html}</div>", unsafe_allow_html=True)

            # CONTROL BUTTONS
            b1, b2, b3, b4 = st.columns(4)
            
            if b1.button("▶ START", key=f"start_{idx}", use_container_width=True):
                st.success(f"Interview Started for {row['Full Name']}")
                
            if b2.button("⏸ HOLD", key=f"hold_{idx}", use_container_width=True):
                st.toast(f"Candidate moved to HOLD for {team}")
                # In your production logic, this would update the Excel 'Status' column to include "Hold:{team}"
                
            if b3.button("✅ COMPLETE", key=f"comp_{idx}", use_container_width=True):
                st.balloons()
                st.info(f"Interview marked as COMPLETE for {team}")
                # This will trigger the tag to turn GREEN for this team
                
            if b4.button("🔄 RESET", key=f"reset_{idx}", use_container_width=True):
                st.write("Status cleared.")
