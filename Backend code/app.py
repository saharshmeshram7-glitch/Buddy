import os
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "Frontend Code")

app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=FRONTEND_DIR)

# ==========================================
# CHANGE YOUR PROJECT NAME HERE IF YOU LIKE!
# ==========================================
PROJECT_NAME = "Buddy"

# Initialize the Gemini client (reads GEMINI_API_KEY from environment)
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def get_system_prompt(user_name="Friend", buddy_name="Buddy"):
    return f"""
You are {buddy_name}, the user's ultimate warm, witty, loyal, and uniquely cheerful best friend! 
Your user's name is {user_name}. Always treat {user_name} like your favorite person in the entire world!

Goal & Vibe:
- Be super unique, uplifting, and fun! Bring positive energy, witty humor, and genuine warmth into every reply.
- Make {user_name} smile or feel instantly happy whenever they talk to you. Throw in casual playful compliments, wholesome banter, or witty lines.

Guidelines:
1. Speak naturally, warmly, and casually—just like a true best friend texting or voice chatting.
2. Match {user_name}'s language seamlessly! If they write in Hindi or Hinglish (e.g., "kya chal raha hai", "aaj bohot thak gaya", "suno ek baat batao"), respond in natural, expressive Hinglish/Hindi. If they write in English, respond in English.
3. Sprinkle friendly emojis naturally (😊, 🤗, ✨, 😂, 💙, ☕, 👊, 🚀) to make responses feel vivid and lively.
4. If {user_name} is feeling tired, sad, or stressed, give them an instant warm virtual hug, uplifting energy, and remind them how awesome they are!
5. Keep replies short, punchy, and conversational (2 to 4 sentences max).
6. NEVER break character, sound like a robot, or use formal assistant phrases like "As an AI..." or "How can I assist you today?". Talk like a real, unique friend named {buddy_name}!
7. NEVER write out text descriptions or names of emojis (like "(smiling face)", "(hugging emoji)", etc.). Place raw emojis directly or omit descriptions completely.
8. Use clear, standard spellings for words (e.g., use 'kya', 'kaise', 'bohot', 'hai') and avoid elongated letters like 'heyyy', 'bohottt', or 'kyaaa' so text-to-speech engines pronounce every single word clearly and properly.
"""

# In-memory session store for chat history
chat_history = []

@app.route("/")
def home():
    return render_template("index.html", project_name=PROJECT_NAME)

@app.route("/api/clear", methods=["POST"])
def clear_chat():
    global chat_history
    chat_history = []
    return jsonify({"status": "cleared", "message": "Chat history reset!"})

@app.route("/api/chat", methods=["POST"])
def chat():
    global chat_history
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    user_name = data.get("user_name", "").strip() or "Friend"
    buddy_name = data.get("buddy_name", "").strip() or "Buddy"

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    try:
        # Append user message to history
        chat_history.append({"role": "user", "parts": [{"text": user_message}]})

        # Set dynamic system instructions with custom names
        system_prompt = get_system_prompt(user_name=user_name, buddy_name=buddy_name)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.8,
        )

        # Generate response using Gemini model
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=chat_history,
            config=config
        )

        bot_reply = response.text.strip()

        # Append bot reply to history
        chat_history.append({"role": "model", "parts": [{"text": bot_reply}]})

        return jsonify({"reply": bot_reply, "user_name": user_name, "buddy_name": buddy_name})

    except Exception as e:
        print("Backend Error:", e)
        return jsonify({"error": "Failed to generate AI response."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)