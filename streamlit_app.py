import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import os
from io import BytesIO

# --- CONFIG & ADMIN SETTINGS ---
st.set_page_config(page_title="DJS SAE Recruitment Portal", layout="wide")
MASTER_PASSWORD = "MilesAdmin2026" 

TEAM_LOGOS = {
    "Astra": "DJS Astra.jpg.jpg", "Helios": "DJS Helios.jpg.jpg",
    "Impulse": "DJS Impulse.jpg.jpg", "Karting": "DJS Karting.jpg.jpg",
    "Kronos": "DJS Kronos.jpg.jpg", "Miles": "DJS Miles.jpg.jpg",
    "Phoenix": "DJS Phoenix.jpg.jpg", "Racing": "DJS Racing.jpg.jpg",
    "Robocon": "DJS Robocon.jpg.jpg", "Skylark": "DJS Skylark.jpg.jpg",
    "Speedsters": "DJS Speedsters.jpg.jpg"
}

if 'dialog_active' not in st.session_state: st.session_state.dialog_active = False
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.dialog_active:
    st_autorefresh(interval=3000, limit=None, key="live_sync")

# --- UI STYLING (Light & Dark Theme Adaptive) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .header-box { background: rgba(128,128,128,0.1); padding: 20px; border-radius: 12px; border-bottom: 5px solid #f1c40f; text-align: center; margin-bottom: 20px; }
    .process-section { background: rgba(52,152,219,0.05); padding: 20px; border-radius: 12px; border: 2px solid #3498db; margin-bottom: 20px; }
    .hold-section { background: rgba(155,89,182,0.05); padding: 20px; border-radius: 12px; border: 2px solid #9b59b6; margin-bottom: 20px; }
    .done-section { background: rgba(35,134,54,0.05); padding: 15px; border-radius: 12px; border-left: 6px solid #238636; margin-top: 10px; margin-bottom: 10px; }
    
    .tag-done { background-color: #238636; color: white; padding: 5px 12px; border-radius: 15px; font-size: 13px; font-weight: 600; white-space: nowrap; }
    .tag-hold { background-color: #9b59b6; color: white; padding: 5px 12px; border-radius: 15px; font-size: 13px; font-weight: 600; white-space: nowrap; }
    .tag-process { background-color: #3498db; color: white; padding: 5px 12px; border-radius: 15px; font-size: 13px; font-weight: 600; white-space: nowrap; }
    .tag-pending { border: 1px solid #f1c40f; color: #f1c40f; padding: 5px 12px; border-radius: 15px; font-size: 13px; font-weight: 600; white-space: nowrap; }
    </style>
    """, unsafe_allow_html=True)

FILE_NAME = "SAE_Interview_Database.xlsx"

# --- GLOBAL DATABASE UPDATED ---
@st.cache_resource
def get_global_db(): 
    return {
        "status": {},      # { sap_id: { team_name: "Status" } }
        "approved": set(), # Set of SAP IDs allowed in by GC
        "walkins": []      # List of dynamically added walk-in dictionaries
    }
global_db = get_global_db()

@st.cache_data(ttl=5)
def load_data():
    try:
        df = pd.read_excel(FILE_NAME, sheet_name='Form Responses 1')
        creds = pd.read_excel(FILE_NAME, sheet_name='Credentials')
        return df, creds
    except: return None, None

def normalize_team(t_name):
    if pd.isna(t_name): return ""
    name = str(t_name).strip()
    if "Speedster" in name.title(): return "Speedsters"
    return name.title()

def get_occupying_team(sid):
    # Returns the team currently interviewing the candidate (if any)
    for t, s in global_db["status"].get(sid, {}).items():
        if s == "In Process": return t
    return None

@st.dialog("⚠️ MASTER AUTHORIZATION")
def master_reset_dialog(action_type, sap_id=None, current_team=None):
    st.session_state.dialog_active = True
    pwd = st.text_input("Enter Admin Password", type="password")
    if st.button("Confirm", use_container_width=True):
        if pwd == MASTER_PASSWORD:
            if action_type == "all": 
                global_db["status"].clear()
                global_db["approved"].clear()
                global_db["walkins"].clear()
            else: global_db["status"].setdefault(sap_id, {})[current_team] = "Pending"
            st.session_state.dialog_active = False
            st.rerun()
        else: st.error("Invalid Password.")

# --- LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>SAE RECRUITMENT</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u, p = st.text_input("Username"), st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if u.upper() == "GC" and p == MASTER_PASSWORD:
                st.session_state.logged_in, st.session_state.team = True, "GC"
                st.rerun()
            else:
                df_all, cr = load_data()
                if df_all is not None:
                    match = cr[(cr['Username'] == u) & (cr['Password'] == p)]
                    if not match.empty:
                        st.session_state.logged_in, st.session_state.team = True, normalize_team(match.iloc[0]['Assigned Team'])
                        st.rerun()
                    else: st.error("Invalid credentials.")
else:
    team = st.session_state.team
    df_excel, _ = load_data()
    pref_cols = [f'Team preference list [{i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"}]' for i in range(1, 12)]
    
    # Merge Walk-ins with Excel Data
    if global_db["walkins"]:
        df_walkins = pd.DataFrame(global_db["walkins"])
        df_all = pd.concat([df_excel, df_walkins], ignore_index=True)
    else:
        df_all = df_excel

    def draw_combined_row(row, sid):
        tags_html = ""
        for c in pref_cols:
            if c not in row: continue
            t = normalize_team(row[c])
            if t:
                s = global_db["status"].get(sid, {}).get(t, "Pending")
                cls = "tag-done" if s=="Done" else "tag-hold" if s=="Hold" else "tag-process" if s=="In Process" else "tag-pending"
                tags_html += f'<span class="{cls}">{t} {s.upper()}</span>'
        return f'<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 12px; flex-wrap: wrap;"><span style="font-size: 1.1rem; font-weight: bold; white-space: nowrap;">{row["Full Name"]} ({sid})</span><div style="display: flex; gap: 8px; flex-wrap: wrap;">{tags_html}</div></div>'

    # ==========================================
    #             GC DASHBOARD
    # ==========================================
    if team == "GC":
        st.markdown('<div class="header-box"><h1>👔 GROUP COORDINATOR</h1></div>', unsafe_allow_html=True)
        
        with st.expander("➕ Register New Walk-in Candidate"):
            with st.form("walkin_form"):
                w_name = st.text_input("Candidate Full Name")
                w_sap = st.text_input("SAP ID")
                w_prefs = st.multiselect("Select Team Preferences (In Order)", list(TEAM_LOGOS.keys()))
                if st.form_submit_button("Register & Allow Entry"):
                    if w_name and w_sap and w_prefs:
                        row_data = {"Full Name": w_name, "SAP ID": w_sap}
                        for i, p in enumerate(w_prefs, 1):
                            idx = f"{i}st" if i==1 else f"{i}nd" if i==2 else f"{i}rd" if i==3 else f"{i}th"
                            row_data[f'Team preference list [{idx}]'] = p
                        global_db["walkins"].append(row_data)
                        global_db["approved"].add(str(w_sap))
                        st.success("Registered and Allowed!")
                        st.rerun()

        st.subheader("🛂 Arrival Management")
        search = st.text_input("🔍 Search Name or SAP ID to approve entry")
        
        to_display = df_all
        if search:
            to_display = to_display[to_display['Full Name'].astype(str).str.contains(search, case=False) | to_display['SAP ID'].astype(str).str.contains(search)]
        else:
            to_display = to_display.head(50)
            st.caption("Showing top 50 candidates. Use search to find specific people.")

        for _, r in to_display.iterrows():
            sid = str(r['SAP ID'])
            is_app = sid in global_db["approved"]
            
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{r['Full Name']}** | SAP: {sid}")
            if is_app:
                c2.success("✅ Inside")
            else:
                if c2.button("Allow Entry", key=f"allow_{sid}", use_container_width=True):
                    global_db["approved"].add(sid)
                    st.rerun()

    # ==========================================
    #             TEAM DASHBOARD
    # ==========================================
    else:
        col_logo, col_title = st.columns([1, 5])
        logo_path = TEAM_LOGOS.get(team)
        if logo_path and os.path.exists(logo_path): col_logo.image(logo_path, width=110)
        st.markdown(f'<div class="header-box"><h1>{team.upper()}</h1></div>', unsafe_allow_html=True)

        # Ensure RCs only see GC-Approved candidates
        mask_team = df_all[pref_cols].apply(lambda x: x.astype(str).str.contains("Speedster" if team == "Speedsters" else team, case=False)).any(axis=1)
        team_df = df_all[mask_team]
        team_df = team_df[team_df['SAP ID'].astype(str).isin(global_db["approved"])]

        search = st.text_input("🔍 Search Approved Candidates")
        if search:
            team_df = team_df[team_df['Full Name'].astype(str).str.contains(search, case=False) | team_df['SAP ID'].astype(str).str.contains(search)]

        proc, hold, pend, done = [], [], [], []
        for _, row in team_df.iterrows():
            sid = str(row['SAP ID'])
            stat = global_db["status"].get(sid, {}).get(team, "Pending")
            if stat == "In Process": proc.append(row)
            elif stat == "Hold": hold.append(row)
            elif stat == "Done": done.append(row)
            else: pend.append(row)

        if proc:
            st.markdown('<div class="process-section"><h3>🔵 Currently Interviewing</h3>', unsafe_allow_html=True)
            for r in proc:
                sid = str(r['SAP ID'])
                st.markdown(draw_combined_row(r, sid), unsafe_allow_html=True)
                c = st.columns(3)
                if c[0].button("✅ COMPLETE", key=f"d_{sid}"): global_db["status"].setdefault(sid, {})[team] = "Done"; st.rerun()
                if c[1].button("⏸️ HOLD", key=f"h_{sid}"): global_db["status"].setdefault(sid, {})[team] = "Hold"; st.rerun()
                if c[2].button("🔙 QUEUE", key=f"q_{sid}"): global_db["status"].setdefault(sid, {})[team] = "Pending"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if hold:
            st.markdown('<div class="hold-section"><h3>🟣 On Hold</h3>', unsafe_allow_html=True)
            for r in hold:
                sid = str(r['SAP ID'])
                st.markdown(draw_combined_row(r, sid), unsafe_allow_html=True)
                c = st.columns(2)
                
                # Check Lock before Resuming from Hold
                occ = get_occupying_team(sid)
                if occ and occ != team:
                    st.error(f"🔒 Cannot Resume: Candidate currently occupied by {occ.upper()}")
                else:
                    if c[0].button("▶ RESUME", key=f"re_{sid}", use_container_width=True): global_db["status"].setdefault(sid, {})[team] = "In Process"; st.rerun()
                if c[1].button("🔙 QUEUE", key=f"q2_{sid}", use_container_width=True): global_db["status"].setdefault(sid, {})[team] = "Pending"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.subheader(f"📋 Waiting List ({len(pend)})")
        for r in pend:
            sid = str(r['SAP ID'])
            occ = get_occupying_team(sid)
            with st.expander(f"➔ {r['Full Name']} ({sid})"):
                st.markdown(draw_combined_row(r, sid), unsafe_allow_html=True)
                
                # MUTUAL EXCLUSION LOCK
                if occ and occ != team:
                    st.error(f"🔒 Candidate is currently in an interview with {occ.upper()}")
                    st.button("▶ START INTERVIEW", key=f"s_{sid}", disabled=True, use_container_width=True)
                else:
                    if st.button("▶ START INTERVIEW", key=f"s_{sid}", use_container_width=True):
                        global_db["status"].setdefault(sid, {})[team] = "In Process"; st.rerun()

        if done:
            st.markdown("<div class='done-section'><h3>🏁 Finished</h3>", unsafe_allow_html=True)
            for r in done:
                sid = str(r['SAP ID'])
                cols = st.columns([4, 1])
                with cols[0]: st.markdown(draw_combined_row(r, sid), unsafe_allow_html=True)
                with cols[1]: 
                    if st.button("Reset 🔒", key=f"u_{sid}"): master_reset_dialog("single", sid, team)
            st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    #             GLOBAL EXPORT & FOOTER
    # ==========================================
    st.write("---")
    master_rows = []
    for _, row in df_all.iterrows():
        sid = str(row['SAP ID'])
        student_entry = {"Full Name": row['Full Name'], "SAP ID": sid}
        student_entry["GC Status"] = "✅ Allowed" if sid in global_db["approved"] else "⏳ Not Arrived"
        
        for i, col_name in enumerate(pref_cols, 1):
            target_team = normalize_team(row[col_name]) if col_name in row else ""
            if target_team:
                current_stat = global_db["status"].get(sid, {}).get(target_team, "Pending")
                student_entry[f"Preference {i}"] = f"{target_team}: {current_stat.upper()}"
            else:
                student_entry[f"Preference {i}"] = "-"
        
        master_rows.append(student_entry)

    towrite = BytesIO()
    pd.DataFrame(master_rows).to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)

    f1, f2, f3 = st.columns(3)
    f1.download_button("📥 Master Report (11 Cols)", data=towrite, file_name="SAE_Master_Recruitment.xlsx", use_container_width=True)
    if f2.button("🚨 CLEAR ALL", use_container_width=True): master_reset_dialog("all")
    if f3.button("Logout", use_container_width=True): st.session_state.logged_in = False; st.rerun()
