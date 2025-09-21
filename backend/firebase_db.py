import firebase_admin
from firebase_admin import credentials, db
from config import FIREBASE_DB_URL, FIREBASE_CREDENTIALS

def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})

def store_state(user, state):
    ref = db.reference(f'/users/{user}/state')
    ref.set(state)

def get_state(user):
    ref = db.reference(f'/users/{user}/state')
    return ref.get() or {}

def append_message(user, role, message):
    ref = db.reference(f'/users/{user}/messages')
    ref.push({"role": role, "content": message})

def get_messages(user):
    ref = db.reference(f'/users/{user}/messages')
    return ref.get() or {}
