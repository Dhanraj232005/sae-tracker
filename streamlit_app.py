import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SAE Interview Tracker", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS FOR AESTHETICS & COLORS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stExpander"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        margin-bottom: 15px;
        padding: 5px;
    }
    .status-badge {
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        display: inline-block;
        margin-top: 5px;
    }
    .status-ready { background-color: #238636; color: white; } /* Green */
    .status-progress { background-color: #f1c40f; color: black; } /* Yellow */
    .status-completed { background-color: #e74c3c; color: white; } /* Red */
    
    .card-text { font-size: 0.9rem; color: #adbac7; line-height: 1.6; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

# --- FAST DATA LOADING (Refreshes every 60s) ---
@st.cache_data(ttl=60)
def load_data():
    try:
        candidates = pd.read_excel(FILE_NAME, sheet_name='Candidates')
        creds = pd.read_excel(FILE_NAME, sheet_name='Credentials')
        return candidates, creds
    except Exception as e:
        st.error(f"Error: Ensure {FILE_NAME} is in your GitHub!")
        return pd.DataFrame(), pd.DataFrame()

# Initialize Session States
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'df' not in st.session_state:
    candidates, _ = load_data()
    st.session_state.df = candidates

# --- LOGIN INTERFACE ---
if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown("<h1 style='text-align: center; color: white;'>🏎️ SAE RECRUITMENT</h1>", unsafe_allow_html=True)
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
                else: st
