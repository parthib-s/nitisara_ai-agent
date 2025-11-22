import firebase_admin
from firebase_admin import credentials, db
from config import FIREBASE_DB_URL, FIREBASE_CREDENTIALS
import os
import json

# Local JSON file for persistence in demo mode
LOCAL_DB_FILE = "local_db.json"

def _load_local_db():
    if os.path.exists(LOCAL_DB_FILE):
        try:
            with open(LOCAL_DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_local_db(data):
    with open(LOCAL_DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def init_firebase():
    # Skip Firebase initialization if credentials are not available
    if not os.path.exists(FIREBASE_CREDENTIALS):
        print(f"⚠️ Firebase credentials not found. Using local file '{LOCAL_DB_FILE}' for storage.")
        return
    
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS)
            firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})
        except Exception as e:
            print(f"Warning: Firebase initialization failed: {e}. Using local file storage.")

def store_state(user, state):
    if firebase_admin._apps:
        ref = db.reference(f'/users/{user}/state')
        ref.set(state)
    else:
        data = _load_local_db()
        data[f'{user}_state'] = state
        _save_local_db(data)

def get_state(user):
    if firebase_admin._apps:
        ref = db.reference(f'/users/{user}/state')
        return ref.get() or {}
    else:
        data = _load_local_db()
        return data.get(f'{user}_state', {})

def append_message(user, role, message):
    if firebase_admin._apps:
        ref = db.reference(f'/users/{user}/messages')
        ref.push({"role": role, "content": message})
    else:
        data = _load_local_db()
        key = f'{user}_messages'
        if key not in data:
            data[key] = []
        data[key].append({"role": role, "content": message})
        _save_local_db(data)

def get_messages(user):
    if firebase_admin._apps:
        ref = db.reference(f'/users/{user}/messages')
        return ref.get() or {}
    else:
        data = _load_local_db()
        messages = data.get(f'{user}_messages', [])
        # Return in format expected by frontend {id: msg, ...}
        return {str(i): msg for i, msg in enumerate(messages)}