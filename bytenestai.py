# app.py (Python Flask Backend)
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import threading

app = Flask(__name__)
CORS(app) # ഇത് যেকোনো ডোমেইন থেকে (InfinityFree থেকেও) রিকোয়েস্ট একসেপ্ট করবে

# === CONFIGURATION ===
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
AI_API_KEY = "YOUR_GEMINI_OR_OPENAI_KEY"
ACTIVE_ENGINE = "gemini" # or "openai"

# Telegram Background Sender (যাতে ইউজারের চ্যাট স্লো না হয়)
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat_engine():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.json
    client_id = data.get('client_id')
    user_message = data.get('message')

    if not client_id or not user_message:
        return jsonify({"reply": "System Error: Missing Client ID"}), 400

    # 1. New Message Alert to Telegram (Running in background)
    threading.Thread(target=send_telegram_alert, args=(f"<b>New Message:</b>\n{user_message}",)).start()

    # 2. AI Payload Setup (Gemini 1.5 Flash format)
    url = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}"
    }

    # AI Instructions & Tools
    sys_prompt = "You are a friendly SaaS AI. Keep answers short. If user gives name and phone/email, call 'capture_lead'."
    
    payload = {
        "model": "gemini-1.5-flash",
        "messages":[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_message}
        ],
        "tools":[{
            "type": "function",
            "function": {
                "name": "capture_lead",
                "description": "Capture lead info.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"}
                    },
                    "required":["name"]
                }
            }
        }],
        "temperature": 0.5
    }

    # 3. Call AI API
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        ai_data = response.json()
        
        ai_msg = ai_data.get('choices', [{}])[0].get('message', {})
        
        # Check if AI used Tool (Lead Captured)
        if 'tool_calls' in ai_msg:
            func = ai_msg['tool_calls'][0]['function']
            if func['name'] == 'capture_lead':
                args = json.loads(func['arguments'])
                u_name = args.get('name', 'User')
                u_phone = args.get('phone', 'N/A')
                
                # Send Lead to Telegram
                lead_alert = f"🚀 <b>NEW LEAD CAPTURED!</b>\nName: {u_name}\nPhone/Email: {u_phone}"
                threading.Thread(target=send_telegram_alert, args=(lead_alert,)).start()
                
                # TODO: Save to your MySQL Database here if needed
                
                return jsonify({"reply": f"Thanks {u_name}! I have securely logged your details. We will contact you soon!"})

        # Normal Text Reply
        reply_text = ai_msg.get('content', "Processing...")
        return jsonify({"reply": reply_text})

    except Exception as e:
        return jsonify({"reply": "Neural network timeout. Please try again."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)