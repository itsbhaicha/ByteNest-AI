import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import threading

app = Flask(__name__)
CORS(app)

# === CONFIGURATION (সঠিক ফরম্যাট) ===
TELEGRAM_TOKEN = "8798938808:AAF712x7YhG_EQWw2HJ9_G4vymL8rseSbrI"
TELEGRAM_CHAT_ID = "8127463560"
AI_API_KEY = "AIzaSyCnEqCOxiwEttLQHSjGAwjkjalsZzwC_nE"

def send_telegram_alert(message):
    # সঠিক URL কনস্ট্রাকশন
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Error: {e}")

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ByteNest AI Is Online"}), 200

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat_engine():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"reply": "Empty transmission."}), 400

    # Telegram Alert
    threading.Thread(target=send_telegram_alert, args=(f"<b>New Incoming:</b> {user_message}",)).start()

    # Gemini API Call
    url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {AI_API_KEY}"}
    
    payload = {
        "model": "gemini-1.5-flash",
        "messages":[
            {"role": "system", "content": "You are a friendly business assistant. If user gives name, email, or phone, call capture_lead."},
            {"role": "user", "content": user_message}
        ],
        "tools":[{
            "type": "function",
            "function": {
                "name": "capture_lead",
                "description": "Save lead info",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"}
                    },
                    "required": ["name"]
                }
            }
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        ai_data = response.json()
        
        # এরর হ্যান্ডলিং (Gemini এরর চেক)
        if "choices" not in ai_data:
            return jsonify({"reply": "AI Service error: " + str(ai_data)})

        ai_msg = ai_data['choices'][0]['message']
        
        # Lead detection
        if 'tool_calls' in ai_msg:
            func = ai_msg['tool_calls'][0]['function']
            args = json.loads(func['arguments'])
            lead_alert = f"🚀 <b>LEAD SECURED!</b>\nName: {args.get('name')}\nEmail: {args.get('email')}\nPhone: {args.get('phone')}"
            threading.Thread(target=send_telegram_alert, args=(lead_alert,)).start()
            return jsonify({"reply": "Data logged successfully! Our team will contact you."})

        return jsonify({"reply": ai_msg.get('content', "No response")})

    except Exception as e:
        return jsonify({"reply": "Neural connection failed: " + str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
