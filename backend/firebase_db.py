import firebase_admin
from firebase_admin import credentials, db
from config import FIREBASE_DB_URL, FIREBASE_CREDENTIALS

def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})
        print("Firebase initialized")

def store_state(user, new_state: dict):
    """Merge new state with existing state"""
    old_state = get_state(user)
    merged = {**old_state, **new_state}
    ref = db.reference(f'/users/{user}/state')
    ref.set(merged)

def get_state(user):
    try:
        ref = db.reference(f'/users/{user}/state')
        state = ref.get()
        if not state:
            state = {}
        return state
    except Exception as e:
        print(f"Firebase get_state error: {e}")
        return {}

def append_message(user, role, message):
    ref = db.reference(f'/users/{user}/messages')
    ref.push({"role": role, "content": message})

def get_messages(user):
    try:
        ref = db.reference(f'/users/{user}/messages')
        return ref.get() or {}
    except Exception as e:
        print(f"Firebase get_messages error: {e}")
        return {}
