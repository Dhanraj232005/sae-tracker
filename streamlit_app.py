import streamlit as st
import pandas as pd
import base64

st.set_page_config(page_title="SAE Recruitment Portal", layout="wide")

# --- AUDIO FUNCTION ---
def play_sound():
    # A short, professional 'complete' chime
    sound_file = "https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3"
    st.components.v1.html(
        f"""
        <audio autoplay>
            <source src="{sound_file}" type="audio/mp3">
        </audio>
        """,
        height=0,
    )

# --- UI STYLING ---
st.markdown("""
    <style>
    .header-box { background: #1f242b; padding: 20px; border-radius: 10px; border-bottom: 3px solid #f1c40f; text-align: center; margin-bottom: 20px; }
    .tag-done { background-color: #238636; color: white; padding: 2px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; font-weight: bold; }
    .tag-pending { color: #f1c40f; border: 1px solid #f1c40f; padding: 2px 10px; border-radius: 12px; margin-right: 5px; font-size: 11px; }
    .done-section { background-color: #1a1c23; padding: 15px; border-radius: 10px; border-left: 5px solid #238636; margin-top: 30px; }
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
    except: return None, None

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>SAE RECRUITMENT LOGIN</h2>", unsafe_allow_html=True)
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
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
    
    # Filter for candidates
    mask = df_all[pref_cols].apply(lambda x: x.str.contains(team, na=False, case=False)).any(axis=1)
    team_df = df_all[mask]

    # Split into Pending and Completed for this team
    completed_mask = team_df['Status'].str.contains(f"Done:{team}", na=False)
    pending_list = team_df[~completed_mask]
    done_list = team_df[completed_mask]

    # --- MAIN INTERVIEW LIST ---
    st.subheader("📋 Active Queue")
    search = st.text_input("🔍 Search Name/SAP ID")
    if search:
        pending_list = pending_list[pending_list['Full Name'].str.contains(search, case=False) | pending_list['SAP ID'].astype(str).str.contains(search)]

    for idx, row in pending_list.iterrows():
        status = str(row['Status']) if pd.notna(row['Status']) else ""
        user_prefs = [row[c] for c in pref_cols if pd.notna(row[c])]
        
        with st.expander(f"➔ {row['Full Name']} ({row['SAP ID']})"):
            tags_html = "".join([f'<span class="{"tag-done" if f"Done:{p}" in status else "tag-pending"}">{p}</span>' for p in user_prefs])
            st.markdown(f"<div style='margin-bottom:15px;'>{tags_html}</div>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            # Logic: Disable START if already DONE for this team
            is_done = f"Done:{team}" in status
            if c1.button("▶ START", key=f"s_{idx}", use_container_width=True, disabled=is_done):
                st.toast(f"Starting interview for {row['Full Name']}")
            
            if c2.button("✅ COMPLETE", key=f"c_{idx}", use_container_width=True):
                play_sound()
                st.balloons()
                st.success(f"Interview for {team} marked as DONE!")
            
            if c3.button("🔄 RESET", key=f"r_{idx}", use_container_width=True):
                st.warning("Resetting status...")

    # --- COMPLETED SECTION ---
    if not done_list.empty:
        st.markdown("<div class='done-section'>", unsafe_allow_html=True)
        st.subheader("✅ Recently Completed by Your Team")
        for idx, row in done_list.iterrows():
            st.write(f"✔️ {row['Full Name']} ({row['SAP ID']})")
        st.markdown("</div>", unsafe_allow_html=True)
