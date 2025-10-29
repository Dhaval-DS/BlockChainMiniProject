# app.py (fixed paths + admin form + safe candidates handling)
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
# helpers
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def normalize_chain_data(raw: Any) -> List[Dict]:
    """
    Accept either:
      - a list of blocks ( [{...}, {...}] )
      - or a dict with key "chain": { "chain": [ {...} ] }
    and always return a list of block dicts.
    """
    if raw is None:
        return []
    if isinstance(raw, dict) and "chain" in raw and isinstance(raw["chain"], list):
        return raw["chain"]
    if isinstance(raw, list):
        return raw
    # fallback: corrupt format -> return empty list
    return []

def load_state():
    # load candidates, voters
    candidates = load_json(CAND_PATH, [])
    voters = load_json(VOTER_PATH, {})

    # load chain file and normalize
    raw_chain = load_json(CHAIN_PATH, None)
    chain_list = normalize_chain_data(raw_chain)

    # If chain_list empty, create new blockchain (with genesis) and save it
    if not chain_list:
        bc = SimpleBlockchain()
        save_json(CHAIN_PATH, bc.to_dict())
        chain_list = bc.to_dict()

    # create blockchain object from chain_list
    blockchain = SimpleBlockchain(chain_list)
    return candidates, voters, blockchain

def persist(voters: Dict, blockchain: SimpleBlockchain):
    save_json(VOTER_PATH, voters)
    save_json(CHAIN_PATH, blockchain.to_dict())

def tally_votes_from_chain(blockchain: SimpleBlockchain, candidates: List[Dict]) -> Dict[str,int]:
    counts = {}
    for block in blockchain.chain:
        # each block has .votes list of vote dicts
        for v in block.votes:
            cid = v.get("candidate")
            if cid is None:
                continue
            counts[cid] = counts.get(cid, 0) + 1
    # map candidate ids to names
    name_map = {c["id"]: c["name"] for c in candidates}
    pretty = { name_map.get(k, k): v for k,v in counts.items() }
    return pretty

# -----------------------
# ensure session state keys exist
if "logged_in_vid" not in st.session_state:
    st.session_state["logged_in_vid"] = None
if "blockchain_loaded_len" not in st.session_state:
    st.session_state["blockchain_loaded_len"] = 0

# -----------------------
# UI config
st.set_page_config(page_title="SmartVote+ — Blockchain E-Voting", layout="wide")
st.title("🗳️ SmartVote+ — Blockchain E-Voting System")
st.markdown("**Demo — not for real elections**")

# load app state
candidates, voters, blockchain = load_state()

# Sidebar role selector
role = st.sidebar.selectbox("Choose Role", ["Voter", "Admin"])

# -----------------------
# Voter view
if role == "Voter":
    st.header("Voter Portal")
    col1, col2 = st.columns(2)

    with col1:
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
                save_json(VOTER_PATH, voters)
                st.success("Registered. Now login at right.")

    with col2:
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
                # store login state in session_state so it persists across reruns
                st.session_state["logged_in_vid"] = vid_login
                st.success(f"Welcome {voters[vid_login]['name']}! Now pick a candidate and cast your vote.")

        # If user is logged in within this session show voting UI
        if st.session_state.get("logged_in_vid"):
            logged_vid = st.session_state["logged_in_vid"]
            st.info(f"Logged in as: {logged_vid} — {voters[logged_vid]['name']}")
            # build choices only if candidates exist
            if not candidates:
                st.warning("No candidates available. Please ask admin to add candidates.json to the repo.")
            else:
                options = [f"{c['id']} - {c['name']}" for c in candidates]
                selected = st.selectbox("Select Candidate", options, key="vote_select")
                if st.button("Cast Vote"):
                    cand_id = selected.split(" - ")[0]
                    vote = {"voter_id": logged_vid, "candidate": cand_id, "timestamp": time.time()}
                    # create a new block with this vote and mine it
                    new_block = blockchain.new_votes_block([vote])
                    # mark voter as voted
                    voters[logged_vid]["voted"] = True
                    # persist immediately
                    persist(voters, blockchain)

                    st.success("Vote recorded and block mined ✅")
                    st.write("Latest block added (index, hash, votes):")
                    st.json({
                        "index": new_block.index,
                        "hash": new_block.hash,
                        "votes": new_block.votes
                    })
                    # reload blockchain from disk to be safe (handles format mismatch)
                    reloaded = normalize_chain_data(load_json(CHAIN_PATH, None))
                    blockchain = SimpleBlockchain(reloaded)
                    # update session variable chain for display
                    st.session_state["blockchain_loaded_len"] = len(blockchain.chain)

    st.markdown("---")
    st.subheader("Voting Results (live)")
    # compute results from current in-memory blockchain (after possible re-load)
    results = tally_votes_from_chain(blockchain, candidates)
    if results:
        st.write("Results table:")
        st.table([{ "Candidate": k, "Votes": v } for k,v in results.items()])
        st.bar_chart({ k: v for k,v in results.items() })
    else:
        st.info("No votes cast yet.")

# -----------------------
# Admin view (persist auth in session state)
elif role == "Admin":
    st.header("Admin Dashboard")

    # ensure admin_authenticated exists
    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False

    # If already authenticated, show admin UI directly
    if st.session_state["admin_authenticated"]:
        st.success("Admin authenticated")
        # Sign out option
        if st.button("Sign out"):
            st.session_state["admin_authenticated"] = False
            st.experimental_rerun()

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

        # Tally button
        if st.button("Tally Results (Admin)"):
            results = tally_votes_from_chain(blockchain, candidates)
            if results:
                st.table([{ "Candidate": k, "Votes": v } for k,v in results.items()])
                st.bar_chart({ k: v for k, v in results.items() })
            else:
                st.info("No votes recorded.")

        # Reset (danger)
        if st.button("Reset Data (Demo)"):
            save_json(VOTER_PATH, {})
            bc_new = SimpleBlockchain()
            save_json(CHAIN_PATH, bc_new.to_dict())
            st.warning("Demo data reset. Refresh the page.")
            # reload app state to reflect reset
            st.session_state["admin_authenticated"] = False
            st.experimental_rerun()

    else:
        # Not authenticated: show login form
        with st.form("admin_login_form"):
            admin_pw = st.text_input("Admin password", type="password")
            submit = st.form_submit_button("Sign in")
        if submit:
            if admin_pw in {"admin123", "admin@123"}:
                st.session_state["admin_authenticated"] = True
                st.experimental_rerun()
            else:
                st.error("Incorrect admin password (demo: admin123 or admin@123)")
        else:
            st.info("Enter admin password (demo: admin123 or admin@123)")


# Ensure final persist (in case someone edited voter dict directly)
persist(voters, blockchain)

