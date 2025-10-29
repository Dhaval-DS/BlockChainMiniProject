# app.py — Modern UI + existing blockchain logic
import streamlit as st
import time
import hashlib
import os
from typing import Dict, Any, List
from storage import load_json, save_json
from blockchain import SimpleBlockchain

# -----------------------
# file paths (reliable)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAND_PATH = os.path.join(BASE_DIR, "candidates.json")
VOTER_PATH = os.path.join(BASE_DIR, "voters.json")
CHAIN_PATH = os.path.join(BASE_DIR, "chain.json")

# -----------------------
# helpers (same logic as before)
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
# session initialization
if "logged_in_vid" not in st.session_state:
    st.session_state["logged_in_vid"] = None
if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False

# -----------------------
# Load data
candidates, voters, blockchain = load_state()

# -----------------------
# Page layout + CSS for modern look
st.set_page_config(page_title="SmartVote+ — Blockchain E-Voting", layout="wide")

# Custom CSS: modern dark theme, cards, smooth transitions
st.markdown(
    """
<style>
/* Page background and fonts */
:root{
  --accent: #7c4dff;
  --card-bg: rgba(255,255,255,0.03);
  --muted: #9aa3b2;
}
body {
  background: linear-gradient(180deg, #0f1724 0%, #0b0f14 100%);
  color: #e6eef8;
  font-family: "Inter", "Segoe UI", Tahoma, sans-serif;
}

/* Header */
.header {
  display:flex;
  align-items:center;
  gap:16px;
  margin-bottom: 10px;
}
.logo {
  width:64px;
  height:64px;
  background: linear-gradient(135deg, rgba(124,77,255,1), rgba(29,199,212,1));
  border-radius:12px;
  display:flex;
  align-items:center;
  justify-content:center;
  box-shadow: 0 6px 20px rgba(124,77,255,0.12);
  font-weight:700;
  color: white;
  font-size:28px;
}
.title {
  font-size:28px;
  font-weight:700;
  letter-spacing: -0.5px;
}
.subtitle {
  color: var(--muted);
  margin-top:2px;
}

/* Card base */
.card {
  background: var(--card-bg);
  padding: 18px;
  border-radius: 12px;
  box-shadow: 0 6px 18px rgba(2,6,23,0.6);
  border: 1px solid rgba(255,255,255,0.03);
  transition: transform 220ms ease, box-shadow 220ms ease;
}
.card:hover { transform: translateY(-6px); box-shadow: 0 14px 40px rgba(2,6,23,0.65); }

/* Candidate tile */
.candidate {
  display:flex;
  align-items:center;
  gap:12px;
  padding:10px;
  border-radius:10px;
  transition: background 200ms ease, transform 200ms ease;
}
.candidate:hover { background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); transform: translateY(-4px); }
.candidate img { width:72px; height:72px; object-fit:cover; border-radius:8px; border:1px solid rgba(255,255,255,0.04); }
.candidate .meta { display:flex; flex-direction:column; }
.candidate .name { font-weight:700; font-size:16px; }
.candidate .id { font-size:12px; color: var(--muted); margin-top:4px; }

/* Buttons (styling Streamlit buttons) */
.stButton>button {
  background: linear-gradient(90deg, var(--accent), #1dd0d4) !important;
  border: none !important;
  color: white !important;
  padding: 8px 16px !important;
  border-radius: 10px !important;
  box-shadow: 0 8px 18px rgba(124,77,255,0.12) !important;
}
.stButton>button:hover { filter: brightness(1.04) !important; transform: translateY(-1px); }

/* Input fields */
.css-1adrfps input, .css-1adrfps textarea { background: rgba(255,255,255,0.02) !important; border-radius:8px !important; color: #e6eef8 !important; }

/* Tables and JSON box */
.stTable td, .stTable th { color: #e6eef8 !important; }
.stJson { background: rgba(255,255,255,0.02) !important; padding:12px; border-radius:8px; }

/* Responsive */
@media (max-width: 900px) {
  .logo { width:48px; height:48px; font-size:20px; }
  .title { font-size:20px; }
  .candidate img { width:56px; height:56px; }
}
</style>
""",
    unsafe_allow_html=True,
)

# Header content
st.markdown(
    """
<div class="header">
  <div class="logo">SV</div>
  <div>
    <div class="title">SmartVote+ — Blockchain E-Voting</div>
    <div class="subtitle">Secure demo dApp • Not for real elections</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Top-level controls: role on left via sidebar
role = st.sidebar.selectbox("Choose Role", ["Voter", "Admin"])

# Main content area container
main = st.container()

with main:
    if role == "Voter":
        # Two-column card layout
        left, right = st.columns([1.1, 1])
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

            # Candidate tiles in a card
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Candidates")
            if not candidates:
                st.info("No candidates available. Add candidates.json to the repo.")
            else:
                # show candidates as tiles
                for c in candidates:
                    img_path = os.path.join(BASE_DIR, c.get("image", "") or "")
                    # build HTML tile
                    img_html = f'<img src="file://{img_path}" />' if (c.get("image") and os.path.exists(img_path)) else '<div style="width:72px;height:72px;border-radius:8px;background:linear-gradient(90deg,#7c4dff,#1dd0d4)"></div>'
                    tile_html = f"""
                    <div class="candidate" style="margin-bottom:8px">
                      {img_html}
                      <div class="meta">
                        <div class="name">{c.get('name','')}</div>
                        <div class="id">{c.get('id','')}</div>
                      </div>
                    </div>
                    """
                    st.markdown(tile_html, unsafe_allow_html=True)
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

            # Voting card (if logged in)
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
                        # update local blockchain variable (reload)
                        reloaded = normalize_chain_data(load_json(CHAIN_PATH, None))
                        blockchain = SimpleBlockchain(reloaded)

            st.markdown("</div>", unsafe_allow_html=True)

        # Results row
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Voting Results (Live)")
        results = tally_votes_from_chain(blockchain, candidates)
        if results:
            # show chart and table side-by-side
            c1, c2 = st.columns([1.4, 1])
            with c1:
                names = list(results.keys())
                vals = list(results.values())
                st.bar_chart({ "votes": vals, "candidates": names })  # Streamlit smart chart
            with c2:
                st.table([{ "Candidate": k, "Votes": v } for k, v in results.items()])
        else:
            st.info("No votes cast yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    else:  # Admin view
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("Admin Dashboard")
        # persistent admin auth
        if st.session_state.get("admin_authenticated"):
            st.success("Authenticated as Admin")
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

            # Tally and Reset buttons
            colA, colB = st.columns(2)
            with colA:
                if st.button("Tally Results"):
                    results = tally_votes_from_chain(blockchain, candidates)
                    if results:
                        st.table([{ "Candidate": k, "Votes": v } for k,v in results.items()])
                        st.bar_chart({ k: v for k,v in results.items() })
                    else:
                        st.info("No votes recorded.")
            with colB:
                if st.button("Reset Data (Demo)"):
                    voters = {}  # reset in-memory
                    bc_new = SimpleBlockchain()
                    save_json(VOTER_PATH, voters)
                    save_json(CHAIN_PATH, bc_new.to_dict())
                    blockchain = bc_new  # update in-memory
                    st.warning("Demo data reset. Voters cleared and chain recreated.")

        else:
            # login form (pressing Enter works)
            with st.form("adminform"):
                admin_pw = st.text_input("Admin password", type="password")
                submit = st.form_submit_button("Sign in")
            if submit:
                if admin_pw in {"admin123", "admin@123"}:
                    st.session_state["admin_authenticated"] = True
                    st.success("Admin authenticated. Reopen Admin view to manage.")
                else:
                    st.error("Incorrect admin password (demo: admin123 or admin@123)")
        st.markdown("</div>", unsafe_allow_html=True)

# Persist state at the end of script
persist(voters, blockchain)
