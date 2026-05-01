import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import threading

app = Flask(__name__)
CORS(app)

# Environment Variables (Render-এ সেট করবেন)
AI_API_KEY = os.environ.get("AI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', '')
    
    # 1. Telegram Notification (Async)
    threading.Thread(target=send_telegram, args=(f"<b>New Msg:</b> {user_msg}",)).start()

    # 2. Gemini API Call
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={AI_API_KEY}"
    
    # System Prompt with Tool Call instructions
    sys_prompt = "You are a professional assistant. If user provides name AND phone/email, output: LEAD_SECURED_NAME: [name] EMAIL: [email] PHONE: [phone]"
    
    payload = {
        "contents": [{"parts": [{"text": f"System: {sys_prompt}. User: {user_msg}"}]}]
    }

    try:
        response = requests.post(url, json=payload, timeout=20)
        result = response.json()
        reply = result['candidates'][0]['content']['parts'][0]['text']

        # 3. Lead Capture Logic
        if "LEAD_SECURED_NAME" in reply:
            threading.Thread(target=send_telegram, args=(f"🚀 <b>LEAD SECURED!</b>\n{reply}",)).start()
            return jsonify({"reply": "Details logged successfully! Our team will contact you soon."})

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "AI is waking up... try again!"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
