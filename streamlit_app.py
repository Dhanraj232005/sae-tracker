import streamlit as st
import pandas as pd

st.set_page_config(page_title="SAE Recruitment Portal", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    .header-box { background: #1f242b; padding: 20px; border-radius: 10px; border-bottom: 3px solid #f1c40f; text-align: center; margin-bottom: 20px; }
    .tag-done { background-color: #238636; color: white; padding: 2px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; font-weight: bold; }
    .tag-pending { color: #f1c40f; border: 1px solid #f1c40f; padding: 2px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; }
    .done-section { background-color: #1a1c23; padding: 15px; border-radius: 10px; border-left: 5px solid #238636; margin-top: 30px; }
    .stButton>button { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

@st.cache_data(ttl=1)
def load_data():
    try:
        # Load the candidate list and credentials from the Excel file
        df = pd.read_excel(FILE_NAME, sheet_name='Form Responses 1')
        creds = pd.read_excel(FILE_NAME, sheet_name='Credentials')
        return df, creds
    except Exception as e:
        st.error("Check Excel: Tab names must be 'Form Responses 1' and 'Credentials'")
        return None, None

# --- STATE MANAGEMENT ---
# Using session_state to track progress live during the session
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
    # Preference columns based on the 11-team structure
    pref_cols = [f'Team preference list [{i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"}]' for i in range(1, 12)]
    
    # Filter students who have this team in their preference list
    mask = df_all[pref_cols].apply(lambda x: x.str.contains(team, na=False, case=False)).any(axis=1)
    team_df = df_all[mask]

    # Search and Export Section
    c_search, c_export = st.columns([3, 1])
    query = c_search.text_input("🔍 Search SAP ID or Name")
    csv = team_df.to_csv(index=False).encode('utf-8')
    c_export.download_button("📤 EXPORT CSV", csv, f"{team}_Recruitment_Data.csv", use_container_width=True)

    if query:
        team_df = team_df[team_df['Full Name'].str.contains(query, case=False, na=False) | team_df['SAP ID'].astype(str).str.contains(query, na=False)]

    pending_list, done_list = [], []
    for _, row in team_df.iterrows():
        sid = str(row['SAP ID'])
        # Sort candidates into Completed and Pending based on session status
        if st.session_state.status_map.get(sid) == "Done":
            done_list.append(row)
        else:
            pending_list.append(row)

    # --- ACTIVE QUEUE (NON-COMPLETED) ---
    st.subheader(f"📋 Active Queue ({len(pending_list)})")
    for row in pending_list:
        sid = str(row['SAP ID'])
        with st.expander(f"➔ {row['Full Name']} ({sid})"):
            # Display preference tags
            tags = "".join([f'<span class="tag-pending">{row[c]}</span>' for c in pref_cols if pd.notna(row[c])])
            st.markdown(f"<div style='margin-bottom:15px;'>{tags}</div>", unsafe_allow_html=True)
            
            b1, b2, b3 = st.columns(3)
            # START is active here because they are not yet completed
            if b1.button("▶ START", key=f"s_{sid}", use_container_width=True):
                st.toast(f"Interviewing {row['Full Name']}...")
            
            if b2.button("✅ COMPLETE", key=f"c_{sid}", use_container_width=True):
                st.session_state.status_map[sid] = "Done"
                st.balloons()
                st.rerun() # Refresh to move the student to the Finished section
            
            if b3.button("🔄 RESET", key=f"r_{sid}", use_container_width=True):
                st.session_state.status_map[sid] = "Pending"
                st.rerun()

    # --- FINISHED SECTION (COMPLETED) ---
    if done_list:
        st.markdown("<div class='done-section'>", unsafe_allow_html=True)
        st.subheader("🏁 Finished Interviews")
        for row in done_list:
            sid = str(row['SAP ID'])
            col_a, col_b = st.columns([5, 1])
            col_a.write(f"✅ **{row['Full Name']}** ({sid})")
            
            # Reset button to move them back to the Active Queue and re-enable START
            if col_b.button("Reset / Undo", key=f"u_{sid}", use_container_width=True):
                st.session_state.status_map[sid] = "Pending"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
