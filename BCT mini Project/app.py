# app.py (Modern UI with enhanced visuals)
import streamlit as st
import time
import hashlib
import os
from typing import Dict, Any, List
import pandas as pd
import altair as alt
import random
from storage import load_json, save_json
from blockchain import SimpleBlockchain

# -----------------------
# file paths (reliable)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAND_PATH = os.path.join(BASE_DIR, "candidates.json")
VOTER_PATH = os.path.join(BASE_DIR, "voters.json")
CHAIN_PATH = os.path.join(BASE_DIR, "chain.json")

# -----------------------
# helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def normalize_chain_data(raw: Any) -> List[Dict]:
    if raw is None:
        return []
    if isinstance(raw, dict) and "chain" in raw and isinstance(raw["chain"], list):
        return raw["chain"]
    if isinstance(raw, list):
        return raw
    return []

def load_state():
    candidates = load_json(CAND_PATH, [])
    voters = load_json(VOTER_PATH, {})
    raw_chain = load_json(CHAIN_PATH, None)
    chain_list = normalize_chain_data(raw_chain)
    if not chain_list:
        bc = SimpleBlockchain()
        save_json(CHAIN_PATH, bc.to_dict())
        chain_list = bc.to_dict()
    blockchain = SimpleBlockchain(chain_list)
    return candidates, voters, blockchain

def persist(voters: Dict, blockchain: SimpleBlockchain):
    save_json(VOTER_PATH, voters)
    save_json(CHAIN_PATH, blockchain.to_dict())

def tally_votes_from_chain(blockchain: SimpleBlockchain, candidates: List[Dict]) -> Dict[str,int]:
    counts = {}
    for block in blockchain.chain:
        for v in block.votes:
            cid = v.get("candidate")
            if cid is None:
                continue
            counts[cid] = counts.get(cid, 0) + 1
    name_map = {c["id"]: c["name"] for c in candidates}
    pretty = { name_map.get(k, k): v for k,v in counts.items() }
    return pretty

# -----------------------
# session init
if "logged_in_vid" not in st.session_state:
    st.session_state["logged_in_vid"] = None
if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False

# -----------------------
# Load data
candidates, voters, blockchain = load_state()

# Generate consistent avatar colors for candidates
def generate_avatar_color(name):
    colors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
        "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"
    ]
    # Use hash of name to get consistent color
    hash_val = sum(ord(c) for c in name)
    return colors[hash_val % len(colors)]

# Generate avatar initials
def get_initials(name):
    parts = name.split()
    if len(parts) >= 2:
        return parts[0][0].upper() + parts[-1][0].upper()
    elif len(name) >= 2:
        return name[:2].upper()
    else:
        return name[0].upper() + "X"

# Assign avatar colors to candidates
for c in candidates:
    if "avatar_color" not in c:
        c["avatar_color"] = generate_avatar_color(c["name"])
    if "initials" not in c:
        c["initials"] = get_initials(c["name"])

# -----------------------
# Modern UI with enhanced styling
st.set_page_config(page_title="SmartVote+ — Blockchain E-Voting", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for modern UI with smooth transitions
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #0c0f1e 0%, #1a1f3a 100%);
        color: #e6eef8;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0c0f1e 0%, #1a1f3a 100%);
    }
    
    .header-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }
    
    .card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .candidate-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .candidate-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        background: rgba(255, 255, 255, 0.08);
    }
    
    .avatar {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 1.2rem;
        color: white;
        flex-shrink: 0;
    }
    
    .vote-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .vote-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .login-button {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .login-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
    }
    
    .register-button {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .register-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
    }
    
    .admin-button {
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .admin-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 152, 0, 0.4);
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: white;
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: white;
    }
    
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 600;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #9aa3b2;
    }
    
    .blockchain-badge {
        display: inline-block;
        background: rgba(76, 175, 80, 0.2);
        color: #4CAF50;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-left: 0.5rem;
    }
    
    .success-message {
        background: rgba(76, 175, 80, 0.1);
        border: 1px solid rgba(76, 175, 80, 0.3);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: rgba(255, 152, 0, 0.1);
        border: 1px solid rgba(255, 152, 0, 0.3);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-message {
        background: rgba(244, 67, 54, 0.1);
        border: 1px solid rgba(244, 67, 54, 0.3);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header with gradient
st.markdown("""
<div class="header-container">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
            <h1 style="margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🗳️ SmartVote+</h1>
            <p style="margin: 0; color: #9aa3b2; font-size: 1.1rem;">Blockchain-Powered Secure E-Voting Platform</p>
        </div>
        <div style="display: flex; gap: 1rem;">
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Candidates</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Voters</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Blocks</div>
            </div>
        </div>
    </div>
</div>
""".format(len(candidates), len(voters), len(blockchain.chain)), unsafe_allow_html=True)

# Role selection in sidebar
st.sidebar.markdown("""
<div style="padding: 1rem; background: rgba(255, 255, 255, 0.05); border-radius: 12px; margin-bottom: 1.5rem;">
    <h3 style="margin-top: 0; color: white;">Select Your Role</h3>
</div>
""", unsafe_allow_html=True)

role = st.sidebar.radio("", ["Voter", "Admin"], label_visibility="collapsed")

# -----------------------
# Voter UI
if role == "Voter":
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        # Registration Card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("👤 Register New Voter")
        
        with st.form("registration_form"):
            vid_reg = st.text_input("Voter ID (unique)", key="reg_vid", placeholder="Enter your unique voter ID")
            name_reg = st.text_input("Full Name", key="reg_name", placeholder="Enter your full name")
            pwd_reg = st.text_input("Password", type="password", key="reg_pwd", placeholder="Create a secure password")
            
            reg_submit = st.form_submit_button("Register", use_container_width=True)
            
            if reg_submit:
                if not vid_reg or not name_reg or not pwd_reg:
                    st.markdown('<div class="error-message">Please fill all fields</div>', unsafe_allow_html=True)
                elif vid_reg in voters:
                    st.markdown('<div class="error-message">Voter ID already exists</div>', unsafe_allow_html=True)
                else:
                    voters[vid_reg] = {"name": name_reg, "password_hash": hash_password(pwd_reg), "voted": False}
                    persist(voters, blockchain)
                    st.markdown('<div class="success-message">Registration successful! You can now login.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Candidates Card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🏆 Candidates")
        
        if not candidates:
            st.markdown('<div class="warning-message">No candidates available. Add candidates.json to the repository.</div>', unsafe_allow_html=True)
        else:
            for c in candidates:
                st.markdown(f"""
                <div class="candidate-card">
                    <div class="avatar" style="background: {c['avatar_color']};">
                        {c['initials']}
                    </div>
                    <div style="flex-grow: 1;">
                        <h4 style="margin: 0; color: white;">{c.get('name','')}</h4>
                        <p style="margin: 0; color: #9aa3b2; font-size: 0.9rem;">ID: {c.get('id','')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Login & Vote Card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🔐 Login & Vote")
        
        with st.form("login_form"):
            vid_login = st.text_input("Voter ID", key="login_vid", placeholder="Enter your voter ID")
            pwd_login = st.text_input("Password", type="password", key="login_pwd", placeholder="Enter your password")
            
            login_submit = st.form_submit_button("Login", use_container_width=True)
            
            if login_submit:
                if vid_login not in voters:
                    st.markdown('<div class="error-message">Voter not registered</div>', unsafe_allow_html=True)
                elif voters[vid_login]["password_hash"] != hash_password(pwd_login):
                    st.markdown('<div class="error-message">Incorrect password</div>', unsafe_allow_html=True)
                elif voters[vid_login].get("voted"):
                    st.markdown('<div class="warning-message">You have already voted.</div>', unsafe_allow_html=True)
                else:
                    st.session_state["logged_in_vid"] = vid_login
                    st.markdown(f'<div class="success-message">Welcome {voters[vid_login]["name"]}! Now pick a candidate and cast your vote.</div>', unsafe_allow_html=True)

        # Voting section (only if logged in)
        if st.session_state.get("logged_in_vid"):
            logged_vid = st.session_state["logged_in_vid"]
            st.markdown(f"""
            <div style="background: rgba(76, 175, 80, 0.1); border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                <p style="margin: 0; color: #4CAF50; font-weight: 500;">
                    ✅ Logged in as: <strong>{logged_vid}</strong> — {voters[logged_vid]['name']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if not candidates:
                st.markdown('<div class="warning-message">No candidates to vote for.</div>', unsafe_allow_html=True)
            else:
                options = [f"{c['id']} - {c['name']}" for c in candidates]
                selected = st.selectbox("Select Candidate", options, key="vote_select")
                
                if st.button("Cast Your Vote 🗳️", use_container_width=True, type="primary"):
                    cand_id = selected.split(" - ")[0]
                    vote = {"voter_id": logged_vid, "candidate": cand_id, "timestamp": time.time()}
                    
                    # Show progress while mining block
                    with st.spinner("Mining block and recording your vote..."):
                        progress_bar = st.progress(0)
                        for i in range(100):
                            time.sleep(0.01)
                            progress_bar.progress(i + 1)
                        
                        new_block = blockchain.new_votes_block([vote])
                        voters[logged_vid]["voted"] = True
                        persist(voters, blockchain)
                    
                    st.markdown(f"""
                    <div class="success-message">
                        <h4 style="margin-top: 0;">Vote Recorded Successfully! ✅</h4>
                        <p>Your vote has been recorded in block #{new_block.index} and added to the blockchain.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show block details
                    with st.expander("Block Details"):
                        st.json({
                            "index": new_block.index,
                            "timestamp": new_block.timestamp,
                            "hash": new_block.hash,
                            "previous_hash": new_block.previous_hash,
                            "votes": new_block.votes
                        })
                    
                    # Reload blockchain data
                    reloaded = normalize_chain_data(load_json(CHAIN_PATH, None))
                    blockchain = SimpleBlockchain(reloaded)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # -----------------------
    # Voting Results with enhanced visualization
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Live Voting Results")
    
    results = tally_votes_from_chain(blockchain, candidates)
    if results:
        # Create dataframe for visualization
        df = pd.DataFrame(list(results.items()), columns=["candidate", "votes"])
        df = df.sort_values("votes", ascending=False)
        
        # Display metrics
        total_votes = df["votes"].sum()
        leading_candidate = df.iloc[0]["candidate"] if not df.empty else "None"
        leading_votes = df.iloc[0]["votes"] if not df.empty else 0
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_votes}</div>
                <div class="metric-label">Total Votes</div>
            </div>
            """, unsafe_allow_html=True)
        with metric_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{leading_candidate[:15]}{'...' if len(leading_candidate) > 15 else ''}</div>
                <div class="metric-label">Current Leader</div>
            </div>
            """, unsafe_allow_html=True)
        with metric_col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{leading_votes}</div>
                <div class="metric-label">Leading Votes</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Create visualization
        chart_height = max(300, 50 * len(df))
        
        # Bar chart
        bar_chart = alt.Chart(df).mark_bar(
            cornerRadius=6,
            opacity=0.8
        ).encode(
            x=alt.X("votes:Q", title="Votes", axis=alt.Axis(grid=True)),
            y=alt.Y("candidate:N", 
                   sort=alt.EncodingSortField(field="votes", op="sum", order="descending"), 
                   title="",
                   axis=alt.Axis(labelLimit=200)),
            color=alt.Color("candidate:N", legend=None,
                           scale=alt.Scale(scheme="purpleblue")),
            tooltip=["candidate", "votes"]
        ).properties(
            height=chart_height,
            title="Vote Distribution"
        ).configure_axis(
            gridColor="rgba(255,255,255,0.1)",
            domainColor="rgba(255,255,255,0.5)",
            labelColor="rgba(255,255,255,0.8)",
            titleColor="rgba(255,255,255,0.8)"
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(bar_chart, use_container_width=True)
        
        # Results table
        st.markdown("#### Detailed Results")
        st.dataframe(
            df.reset_index(drop=True).rename(columns={"candidate": "Candidate", "votes": "Votes"}),
            use_container_width=True
        )
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h3 style="color: #9aa3b2;">No votes cast yet</h3>
            <p style="color: #9aa3b2;">Be the first to cast a vote!</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# Admin UI
elif role == "Admin":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("🔧 Admin Dashboard")
    
    if not st.session_state.get("admin_authenticated"):
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h3>Admin Authentication Required</h3>
            <p style="color: #9aa3b2;">Please enter the admin password to access the dashboard.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("admin_auth"):
            admin_pw = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
            auth_submit = st.form_submit_button("Authenticate", use_container_width=True)
            
            if auth_submit:
                if admin_pw in {"admin123", "admin@123"}:
                    st.session_state["admin_authenticated"] = True
                    st.success("Admin authenticated successfully!")
                    st.rerun()
                else:
                    st.error("Incorrect admin password. Demo passwords: 'admin123' or 'admin@123'")
    
    else:
        # Admin is authenticated
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <div>
                <h3 style="margin: 0;">Admin Controls</h3>
                <p style="margin: 0; color: #9aa3b2;">Manage the voting system and view analytics</p>
            </div>
            <div>
                <button onclick="window.location.reload()" class="admin-button" style="background: rgba(244, 67, 54, 0.2); color: #f44336; border: 1px solid rgba(244, 67, 54, 0.3);">
                    Sign Out
                </button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Sign Out", use_container_width=True):
            st.session_state["admin_authenticated"] = False
            st.success("Signed out successfully!")
            st.rerun()
        
        # Voter management
        st.subheader("👥 Registered Voters")
        if voters:
            voter_data = []
            for vid, info in voters.items():
                voter_data.append({
                    "Voter ID": vid,
                    "Name": info.get("name", "Unknown"),
                    "Voted": "✅" if info.get("voted") else "❌"
                })
            
            voter_df = pd.DataFrame(voter_data)
            st.dataframe(voter_df, use_container_width=True)
            
            # Voter statistics
            voted_count = sum(1 for v in voters.values() if v.get("voted"))
            not_voted_count = len(voters) - voted_count
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{voted_count}</div>
                    <div class="metric-label">Voters Who Voted</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{not_voted_count}</div>
                    <div class="metric-label">Voters Yet to Vote</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No voters registered yet.")
        
        # Blockchain information
        st.subheader("⛓️ Blockchain Ledger")
        st.json(blockchain.to_dict())
        
        col_valid, col_blocks = st.columns(2)
        with col_valid:
            is_valid = blockchain.is_chain_valid()
            status_color = "#4CAF50" if is_valid else "#f44336"
            status_text = "Valid" if is_valid else "Invalid"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {status_color};">{status_text}</div>
                <div class="metric-label">Chain Status</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_blocks:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(blockchain.chain)}</div>
                <div class="metric-label">Blocks in Chain</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Admin actions
        st.subheader("🛠️ Admin Actions")
        action_col1, action_col2 = st.columns(2)
        
        with action_col1:
            if st.button("📈 Tally Results", use_container_width=True):
                results = tally_votes_from_chain(blockchain, candidates)
                if results:
                    df = pd.DataFrame(list(results.items()), columns=["Candidate", "Votes"])
                    df = df.sort_values("Votes", ascending=False).reset_index(drop=True)
                    
                    st.markdown("#### Final Tally Results")
                    st.dataframe(df, use_container_width=True)
                    
                    # Visualization for admin
                    chart_height = max(300, 50 * len(df))
                    bar_chart = alt.Chart(df).mark_bar(
                        cornerRadius=6
                    ).encode(
                        x=alt.X("Votes:Q", title="Votes"),
                        y=alt.Y("Candidate:N", sort=alt.EncodingSortField(field="Votes", op="sum", order="descending"), title=""),
                        color=alt.Color("Candidate:N", legend=None, scale=alt.Scale(scheme="redyellowblue")),
                        tooltip=["Candidate", "Votes"]
                    ).properties(height=chart_height, title="Final Vote Tally")
                    
                    st.altair_chart(bar_chart, use_container_width=True)
                else:
                    st.info("No votes recorded yet.")
        
        with action_col2:
            if st.button("🔄 Reset Data (Demo)", use_container_width=True):
                st.warning("This will reset all data for demo purposes. This action cannot be undone.")
                confirm = st.checkbox("I understand this will delete all votes and voter data")
                
                if confirm and st.button("Confirm Reset", type="primary"):
                    voters = {}
                    bc_new = SimpleBlockchain()
                    save_json(VOTER_PATH, voters)
                    save_json(CHAIN_PATH, bc_new.to_dict())
                    blockchain = bc_new
                    st.success("Demo data reset successfully! All voters cleared and blockchain recreated.")
                    st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Persist final state
persist(voters, blockchain)
