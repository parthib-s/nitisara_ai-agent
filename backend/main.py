from flask import Flask, request, jsonify
from firebase_db import init_firebase, get_messages
from captain_agent import captain_conversation
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

init_firebase()

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user = data.get("user", "demo")
    message = data["message"]
    reply = captain_conversation(user, message)
    return jsonify({"reply": reply})

@app.route("/api/history", methods=["GET"])
def history():
    user = request.args.get("user", "demo")
    hist = get_messages(user)
    # Convert to flat for easy frontend display
    res = [{"role": m["role"], "content": m["content"]} for k, m in (hist or {}).items()]
    return jsonify(res)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
