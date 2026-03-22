import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SAE Interview Tracker", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS FOR AESTHETICS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stExpander"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .status-badge {
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .status-ready { background-color: #238636; color: white; }
    .status-progress { background-color: #d29922; color: black; }
    .status-completed { background-color: #da3633; color: white; }
    
    /* Fix for mobile text */
    .candidate-name { font-size: 1.1rem; font-weight: 600; color: #adbac7; }
    .candidate-info { font-size: 0.85rem; color: #768390; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

@st.cache_data
def load_data():
    try:
        candidates = pd.read_excel(FILE_NAME, sheet_name='Candidates')
        creds = pd.read_excel(FILE_NAME, sheet_name='Credentials')
        return candidates, creds
    except:
        st.error("Excel file not found in GitHub!")
        return pd.DataFrame(), pd.DataFrame()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'df' not in st.session_state:
    candidates, _ = load_data()
    st.session_state.df = candidates

if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown("<h1 style='text-align: center;'>🏎️ SAE RECRUITMENT</h1>", unsafe_allow_html=True)
        with st.container(border=True):
            user = st.text_input("Coordinator ID")
            pw = st.text_input("Password", type="password")
            if st.button("Access Dashboard", use_container_width=True):
                _, creds = load_data()
                user_data = creds[(creds['Username'] == user) & (creds['Password'] == pw)]
                if not user_data.empty:
                    st.session_state.logged_in = True
                    st.session_state.role = user_data.iloc[0]['Role']
                    st.session_state.team = user_data.iloc[0]['Assigned Team']
                    st.rerun()
                else: st.error("Access Denied")
else:
    # --- HEADER ---
    st.markdown(f"<h2 style='text-align: center;'>Room: {st.session_state.team}</h2>", unsafe_allow_html=True)
    
    # --- SIDEBAR TOOLS ---
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/formula-1.png")
        st.write(f"User: **{st.session_state.role}**")
        csv = st.session_state.df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Export Results (CSV)", csv, "SAE_Results.csv", use_container_width=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    df = st.session_state.df

    if st.session_state.role == "GC":
        st.dataframe(df, use_container_width=True)
    else:
        team = st.session_state.team
        mask = (df['Pref 1'] == team) | (df['Pref 2'] == team) | (df['Pref 3'] == team) | (df['Pref 4'] == team)
        team_df = df[mask]

        if team_df.empty:
            st.info("No candidates found for this team yet.")
        
        for idx, row in team_df.iterrows():
            status = str(row['Status'])
            
            # --- DYNAMIC COLOR LOGIC ---
            badge_class = "status-ready"
            if status == "In Progress": badge_class = "status-progress"
            elif "Completed" in status: badge_class = "status-completed"
            
            # --- CARD UI ---
            header_label = f"{row['Full Name']} | {row['Roll No']}"
            
            with st.expander(header_label):
                st.markdown(f"""
                    <div class='candidate-info'>
                        <b>Year:</b> {row['Year']} | <b>Class:</b> {row['Class']} | <b>Div:</b> {row['Division']}<br>
                        <span class='status-badge {badge_class}'>{status}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.write("") # Spacer
                btn_cols = st.columns(2)
                
                if btn_cols[0].button("▶️ START", key=f"s_{idx}", use_container_width=True):
                    st.session_state.df.at[idx, 'Start Time'] = datetime.now().strftime("%H:%M:%S")
                    st.session_state.df.at[idx, 'Status'] = "In Progress"
                    st.rerun()
                
                if btn_cols[1].button("⏹️ STOP", key=f"p_{idx}", use_container_width=True):
                    st.session_state.df.at[idx, 'End Time'] = datetime.now().strftime("%H:%M:%S")
                    st.session_state.df.at[idx, 'Status'] = f"Completed ({team})"
                    st.rerun()
