# Captain AI Setup Guide for Cursor

## Prerequisites
1. Python 3.8+ installed
2. Firebase project created
3. Google Gemini API key

## Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 2: Environment Configuration
Create a `.env` file in the project root with:
```
GEMINI_API_KEY=your_gemini_api_key_here
FIREBASE_DB_URL=https://your-project-id-default-rtdb.firebaseio.com/
FIREBASE_CREDENTIALS=backend/firebase-adminsdk.json
```

## Step 3: Firebase Setup
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing
3. Enable Realtime Database
4. Download service account key as `firebase-adminsdk.json`
5. Place it in the `backend/` folder

## Step 4: Gemini API Setup
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

## Step 5: Run the Application
1. Start backend: `cd backend && python main.py`
2. Open `frontend/index.html` in your browser
3. Start chatting with Captain AI!

## Troubleshooting
- Make sure all environment variables are set
- Check Firebase credentials file exists
- Ensure Python dependencies are installed
- Backend should run on http://localhost:5000
