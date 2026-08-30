import os
from dotenv import load_dotenv
load_dotenv()  # local .env file se keys load karo

from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, DELETE, PUT'
    return response

# ── Gemini client (lazy init) ───────────────────────────────────────────────
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set!")
        _client = genai.Client(api_key=api_key)
    return _client

# ── System prompt ───────────────────────────────────────────────────────────
def get_system_prompt(user_name="Friend", buddy_name="Buddy"):
    return f"""
You are {buddy_name}, the user's ultimate warm, witty, loyal, and uniquely cheerful best friend!
Your user's name is {user_name}. Always treat {user_name} like your favorite person in the entire world!

Goal & Vibe:
- Be super unique, uplifting, and fun! Bring positive energy, witty humor, and genuine warmth into every reply.
- Make {user_name} smile or feel instantly happy whenever they talk to you. Throw in casual playful compliments, wholesome banter, or witty lines.

Guidelines:
1. Speak naturally, warmly, and casually—just like a true best friend texting or voice chatting.
2. Match {user_name}'s language seamlessly! If they write in Hindi or Hinglish (e.g., "kya chal raha hai", "aaj bohot thak gaya"), respond in natural, expressive Hinglish/Hindi. If they write in English, respond in English.
3. Sprinkle friendly emojis naturally (😊, 🤗, ✨, 😂, 💙, ☕, 👊, 🚀) to make responses feel vivid and lively.
4. If {user_name} is feeling tired, sad, or stressed, give them an instant warm virtual hug, uplifting energy, and remind them how awesome they are!
5. Keep replies short, punchy, and conversational (2 to 4 sentences max).
6. NEVER break character, sound like a robot, or use formal assistant phrases like "As an AI..." or "How can I assist you today?". Talk like a real, unique friend named {buddy_name}!
7. NEVER write out text descriptions or names of emojis. Place raw emojis directly or omit descriptions completely.
8. Use clear, standard spellings for words and avoid elongated letters so text-to-speech engines pronounce every word clearly.
"""

# ── In-memory chat history ──────────────────────────────────────────────────
chat_history = []

# ── Health check ────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "OPTIONS"])
def health():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    return jsonify({"status": "Buddy AI backend is running! 🚀"})

# ── API Routes ───────────────────────────────────────────────────────────────
@app.route("/api/clear", methods=["POST", "OPTIONS"])
def clear_chat():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    global chat_history
    chat_history = []
    return jsonify({"status": "cleared", "message": "Chat history reset!"})

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    global chat_history
    data         = request.get_json() or {}
    user_message = data.get("message", "").strip()
    user_name    = data.get("user_name", "").strip() or "Friend"
    buddy_name   = data.get("buddy_name", "").strip() or "Buddy"

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    try:
        chat_history.append({"role": "user", "parts": [{"text": user_message}]})

        system_prompt = get_system_prompt(user_name=user_name, buddy_name=buddy_name)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.8,
        )

        response = get_client().models.generate_content(
            model="gemini-3.6-flash",
            contents=chat_history,
            config=config
        )

        bot_reply = response.text.strip()
        chat_history.append({"role": "model", "parts": [{"text": bot_reply}]})

        return jsonify({"reply": bot_reply, "user_name": user_name, "buddy_name": buddy_name})

    except Exception as e:
        print("Backend Error:", str(e))
        return jsonify({"error": f"Failed to generate AI response: {str(e)}"}), 500

# ── Local dev ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)