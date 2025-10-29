# app.py (fixed Altair properties: removed width=None)
import streamlit as st
import time
import hashlib
import os
from typing import Dict, Any, List
import pandas as pd
import altair as alt
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

# Provide demo images when candidate image is empty
DEFAULT_AVATAR_BASE = "https://i.pravatar.cc/150?img="
for idx, c in enumerate(candidates):
    if not c.get("image"):
        img_no = (idx % 70) + 1
        c["image"] = DEFAULT_AVATAR_BASE + str(img_no)

# -----------------------
# UI layout & CSS (kept minimal)
st.set_page_config(page_title="SmartVote+ — Blockchain E-Voting", layout="wide")
st.markdown("""
<style>
body { background:#081019; color:#e6eef8; font-family: Inter, sans-serif }
.card { background: rgba(255,255,255,0.02); padding:14px; border-radius:12px; }
.candidate-tile { display:flex; align-items:center; gap:12px; padding:8px; border-radius:10px; }
</style>
""", unsafe_allow_html=True)

st.title("🗳️ SmartVote+ — Blockchain E-Voting (Improved Chart + Demo Images)")

role = st.sidebar.selectbox("Choose Role", ["Voter", "Admin"])

# -----------------------
# Voter UI
if role == "Voter":
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Register New Voter")
        vid_reg = st.text_input("Voter ID (unique)", key="reg_vid")
        name_reg = st.text_input("Full Name", key="reg_name")
        pwd_reg = st.text_input("Password", type="password", key="reg_pwd")
        if st.button("Register"):
            if not vid_reg or not name_reg or not pwd_reg:
                st.error("Fill all fields")
            elif vid_reg in voters:
                st.error("Voter ID already exists")
            else:
                voters[vid_reg] = {"name": name_reg, "password_hash": hash_password(pwd_reg), "voted": False}
                persist(voters, blockchain)
                st.success("Registered. Now login on the right.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Candidates")
        if not candidates:
            st.info("No candidates available. Add candidates.json to the repo.")
        else:
            for c in candidates:
                cols = st.columns([0.14, 1])
                with cols[0]:
                    img_path = c.get("image", "")
                    try:
                        st.image(img_path, width=72)
                    except Exception:
                        st.image(None, width=72)
                with cols[1]:
                    st.markdown(f"**{c.get('name','')}**  \n<small style='color:#9aa3b2'>{c.get('id','')}</small>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Login & Vote")
        vid_login = st.text_input("Voter ID", key="login_vid")
        pwd_login = st.text_input("Password", type="password", key="login_pwd")
        if st.button("Login"):
            if vid_login not in voters:
                st.error("Voter not registered")
            elif voters[vid_login]["password_hash"] != hash_password(pwd_login):
                st.error("Incorrect password")
            elif voters[vid_login].get("voted"):
                st.warning("You have already voted.")
            else:
                st.session_state["logged_in_vid"] = vid_login
                st.success(f"Welcome {voters[vid_login]['name']}! Now pick a candidate and cast your vote.")

        if st.session_state.get("logged_in_vid"):
            logged_vid = st.session_state["logged_in_vid"]
            st.info(f"Logged in as: {logged_vid} — {voters[logged_vid]['name']}")
            if not candidates:
                st.warning("No candidates to vote for.")
            else:
                options = [f"{c['id']} - {c['name']}" for c in candidates]
                selected = st.selectbox("Select Candidate", options, key="vote_select")
                if st.button("Cast Vote"):
                    cand_id = selected.split(" - ")[0]
                    vote = {"voter_id": logged_vid, "candidate": cand_id, "timestamp": time.time()}
                    new_block = blockchain.new_votes_block([vote])
                    voters[logged_vid]["voted"] = True
                    persist(voters, blockchain)
                    st.success("Vote recorded and block mined ✅")
                    st.json({"index": new_block.index, "hash": new_block.hash, "votes": new_block.votes})
                    reloaded = normalize_chain_data(load_json(CHAIN_PATH, None))
                    blockchain = SimpleBlockchain(reloaded)
        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------
    # Voting Results — improved chart (fixed .properties)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Voting Results (Live)")

    results = tally_votes_from_chain(blockchain, candidates)
    if results:
        df = pd.DataFrame(list(results.items()), columns=["candidate", "votes"])
        df = df.sort_values("votes", ascending=True)
        chart_height = max(200, 70 * len(df))
        alt_chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("votes:Q", title="Votes"),
            y=alt.Y("candidate:N", sort=alt.EncodingSortField(field="votes", op="sum", order="descending"), title=""),
            tooltip=["candidate", "votes"]
        ).properties(height=chart_height)
        st.altair_chart(alt_chart, use_container_width=True)

        st.table(df.sort_values("votes", ascending=False).reset_index(drop=True).rename(columns={"candidate":"Candidate","votes":"Votes"}))
    else:
        st.info("No votes cast yet.")
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# Admin UI
elif role == "Admin":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("Admin Dashboard")
    if st.session_state.get("admin_authenticated"):
        if st.button("Sign out"):
            st.session_state["admin_authenticated"] = False
            st.success("Signed out")
        st.subheader("Registered Voters")
        if voters:
            rows = []
            for vid, info in voters.items():
                rows.append({"Voter ID": vid, "name": info.get("name"), "voted": info.get("voted")})
            st.table(rows)
        else:
            st.info("No voters registered.")
        st.subheader("Blockchain Ledger")
        st.json({"chain": blockchain.to_dict()})
        st.write("Chain valid:", blockchain.is_chain_valid())
        colA, colB = st.columns(2)
        with colA:
            if st.button("Tally Results"):
                results = tally_votes_from_chain(blockchain, candidates)
                if results:
                    df = pd.DataFrame(list(results.items()), columns=["candidate","votes"]).sort_values("votes", ascending=False).reset_index(drop=True)
                    st.table(df.rename(columns={"candidate":"Candidate","votes":"Votes"}))
                    chart_height = max(200, 70 * len(df))
                    alt_chart = alt.Chart(df).mark_bar().encode(
                        x=alt.X("votes:Q", title="Votes"),
                        y=alt.Y("candidate:N", sort=alt.EncodingSortField(field="votes", op="sum", order="descending"), title=""),
                        tooltip=["candidate","votes"]
                    ).properties(height=chart_height)
                    st.altair_chart(alt_chart, use_container_width=True)
                else:
                    st.info("No votes recorded.")
        with colB:
            if st.button("Reset Data (Demo)"):
                voters = {}
                bc_new = SimpleBlockchain()
                save_json(VOTER_PATH, voters)
                save_json(CHAIN_PATH, bc_new.to_dict())
                blockchain = bc_new
                st.warning("Demo data reset. Voters cleared and chain recreated.")
    else:
        with st.form("adminform"):
            admin_pw = st.text_input("Admin password", type="password")
            submit = st.form_submit_button("Sign in")
        if submit:
            if admin_pw in {"admin123", "admin@123"}:
                st.session_state["admin_authenticated"] = True
                st.success("Admin authenticated.")
            else:
                st.error("Incorrect admin password (demo: admin123 or admin@123)")
    st.markdown("</div>", unsafe_allow_html=True)

# persist final state
persist(voters, blockchain)
