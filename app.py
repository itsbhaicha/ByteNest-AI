from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import threading

app = Flask(__name__)
CORS(app) # Allows requests from any domain

# === CONFIGURATION (আপনার আসল ডেটা দিন) ===
TELEGRAM_TOKEN = "8798938808:AAF712x7YhG_EQWw2HJ9_G4vymL8rseSbrI"
TELEGRAM_CHAT_ID = "8127463560"
AI_API_KEY = "AIzaSyCnEqCOxiwEttLQHSjGAwjkjalsZzwC_nE"

def send_telegram_alert(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{8798938808:AAF712x7YhG_EQWw2HJ9_G4vymL8rseSbrI}/sendMessage"
    payload = {"8127463560": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ByteNest AI Is Online"}), 200

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat_engine():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.json
    client_id = data.get('client_id', 'Unknown')
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"reply": "Empty transmission received."}), 400

    # 1. Background Telegram Alert for New Message
    threading.Thread(target=send_telegram_alert, args=(f"<b>New Incoming Transmission:</b>\n{user_message}",)).start()

    # 2. AI Payload (Gemini)
    url = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {AIzaSyCnEqCOxiwEttLQHSjGAwjkjalsZzwC_nE}"}

    sys_prompt = "You are a professional SaaS AI assistant. Keep answers succinct (max 2 sentences). If the user provides a name AND email/phone, immediately call 'capture_lead'."
    
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
                "description": "Trigger when user gives contact details.",
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
        }],
        "temperature": 0.5
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        ai_data = response.json()
        ai_msg = ai_data.get('choices', [{}])[0].get('message', {})
        
        # 3. Detect if AI captured a lead
        if 'tool_calls' in ai_msg:
            func = ai_msg['tool_calls'][0]['function']
            if func['name'] == 'capture_lead':
                args = json.loads(func['arguments'])
                u_name = args.get('name', 'User')
                u_email = args.get('email', '')
                u_phone = args.get('phone', '')
                
                # Send Urgent Telegram Lead Alert
                lead_alert = f"🚀 <b>NEW LEAD SECURED!</b>\nName: {u_name}\nEmail: {u_email}\nPhone: {u_phone}"
                threading.Thread(target=send_telegram_alert, args=(lead_alert,)).start()
                
                # We return a special flag so frontend JS knows to save it in InfinityFree DB
                return jsonify({
                    "reply": f"Data logged successfully, {u_name}! Our team will connect with you shortly.",
                    "lead_captured": True,
                    "lead_data": {"name": u_name, "email": u_email, "phone": u_phone}
                })

        reply_text = ai_msg.get('content', "Processing anomaly.")
        return jsonify({"reply": reply_text, "lead_captured": False})

    except Exception as e:
        return jsonify({"reply": "Neural network timeout. Retrying connection..."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)