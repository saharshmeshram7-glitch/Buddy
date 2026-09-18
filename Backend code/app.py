import os
import time
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
load_dotenv()

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

# ── Gemini generation with model fallback & retry ──────────────────────────
FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]

def generate_with_fallback(contents, config):
    client = get_client()
    last_exception = None

    for model_name in FALLBACK_MODELS:
        for attempt in range(2):  # Retry up to 2 times per model
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                if response and response.text:
                    return response.text.strip(), model_name
            except Exception as e:
                err_msg = str(e)
                print(f"[Model Retry] Attempt {attempt+1} failed for model '{model_name}': {err_msg}")
                last_exception = e
                if "503" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg:
                    time.sleep(1)
                else:
                    break  # Switch to next fallback model on hard errors

    raise last_exception or Exception("All Gemini models failed to respond.")

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
    return jsonify({"status": "cleared", "message": "Chat history reset!"})

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    user_name = data.get("user_name", "").strip() or "Friend"
    buddy_name = data.get("buddy_name", "").strip() or "Buddy"
    incoming_history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    try:
        # Build contents from incoming_history or fallback to user_message
        contents = []
        if isinstance(incoming_history, list) and len(incoming_history) > 0:
            # Take only last 10 messages to keep context size manageable and fast
            recent_history = incoming_history[-10:]
            for item in recent_history:
                role = item.get("role")
                text = item.get("text", "")
                if role in ["user", "model"] and text:
                    contents.append({"role": role, "parts": [{"text": text}]})

        # Append current user message
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        system_prompt = get_system_prompt(user_name=user_name, buddy_name=buddy_name)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.8,
        )

        bot_reply, used_model = generate_with_fallback(contents=contents, config=config)

        return jsonify({
            "reply": bot_reply,
            "user_name": user_name,
            "buddy_name": buddy_name,
            "model_used": used_model
        })

    except Exception as e:
        print("Backend Error:", str(e))
        return jsonify({"error": f"Failed to generate AI response: {str(e)}"}), 500

# ── Local dev ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)