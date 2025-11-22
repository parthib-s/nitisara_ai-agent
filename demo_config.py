# Demo configuration for Captain AI
# This file provides default values when .env is not available

import os

# Default values for demo mode
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "demo_key")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "https://demo-project-default-rtdb.firebaseio.com/")
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "backend/firebase-adminsdk.json")
