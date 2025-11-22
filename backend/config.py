import os
from dotenv import load_dotenv

# Try to load .env file, but don't fail if it doesn't exist
try:
    load_dotenv()
except:
    pass

# Use environment variables with fallback defaults for demo mode
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "demo_key")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "https://demo-project-default-rtdb.firebaseio.com/")
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "backend/firebase-adminsdk.json")
