# Blockchain E-Voting System (BCT Mini Project)

This project is a simple, decentralized e-voting application built with Python. It uses a custom-built, **Proof-of-Work (PoW) blockchain** to ensure that all votes are recorded as immutable, secure, and verifiable transactions. The user interface is created with **Streamlit**, providing a simple web-based dashboard for voters and administrators.

---
## Features 🗳️

* **User Roles**: The application supports two distinct roles: **Voter** and **Admin**.
* **Voter Registration & Login**: Voters can create an account with a unique Voter ID and password. Passwords are securely stored using **SHA-256 hashing**.
* **Secure Voting**: Once logged in, a voter can cast a single vote for their preferred candidate. The system checks to ensure a voter cannot vote more than once.
* **Blockchain Ledger**: Every cast vote is bundled into a new **Block**, which is then "mined" using a Proof-of-Work algorithm and added to the blockchain. This makes the voting record transparent and tamper-proof.
* **Admin Dashboard**: A secure, password-protected area ("admin123") where the administrator can:
    * View all registered voters and their voting status.
    * Inspect the entire, unencrypted blockchain ledger block by block.
    * Run a **vote tally** that securely counts the votes from the blockchain.
    * Validate the integrity of the blockchain.

---
## Core Components ⚙️

### 1. `app.py` (The Front-End)
This is the main application file that runs the Streamlit web server. It handles all UI logic, user authentication, and state management. It orchestrates the interactions between the user, the `blockchain.py` logic, and the `storage.py` file handlers.

### 2. `blockchain.py` (The Back-End Logic)
This file defines the core mechanics of the blockchain:
* **`Block` Class**: Defines the structure of a block, including its index, timestamp, data (the votes), previous hash, and nonce.
* **`SimpleBlockchain` Class**: Manages the chain of blocks. It includes methods for creating new blocks (`new_votes_block`), implementing the **Proof-of-Work (`proof_of_work`)**, and validating the chain's integrity (`is_chain_valid`).

### 3. `storage.py` (Data Persistence)
A simple utility module with `load_json` and `save_json` functions. It is responsible for reading from and writing the application's state (voters, candidates, and the chain) to JSON files, ensuring data persists between sessions.

### 4. Data Files (`.json`)
* **`candidates.json`**: A list of all candidates in the election.
* **`voters.json`**: A database of registered voters, storing their hashed passwords and "voted" status.
* **`chain.json`**: The blockchain itself, saved as a JSON list of blocks. This file represents the immutable ledger of all cast votes.

---
## Technologies Used 💻
* **Python**
* **Streamlit**: For the web-based user interface.
* **hashlib**: For password hashing.

---
## How to Run the Project

1.  Ensure you have Python and the required libraries installed:
    ```bash
    pip install streamlit
    ```
2.  Navigate to the project directory in your terminal:
    ```bash
    cd "BCT mini Project"
    ```
3.  Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```
4.  The application will open in your default web browser.
