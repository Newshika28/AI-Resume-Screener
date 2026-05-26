import json
import os
import hashlib

USERS_FILE = "users.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def create_account(username, password, role):
    """
    Returns (True, message) on success
    Returns (False, message) on failure
    """
    users = load_users()
    if username.lower() in users:
        return False, "❌ Username already exists. Please choose another."
    users[username.lower()] = {
        "password": hash_password(password),
        "role": role,
        "icon": "👤" if role == "Job Seeker" else "🏢"
    }
    save_users(users)
    return True, f"✅ Account created! You can now log in as {role}."

def authenticate(username, password):
    """
    Returns (True, role, icon) on success
    Returns (False, None, None) on failure
    """
    users = load_users()
    user = users.get(username.lower())
    if user and user["password"] == hash_password(password):
        return True, user["role"], user["icon"]
    return False, None, None