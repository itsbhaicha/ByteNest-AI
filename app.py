import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import threading

app = Flask(__name__)
CORS(app)

# Render থেকে এপিআই কি নেওয়া হবে (নিরাপদ)
AI_API_KEY = os.environ.get('AI_API_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_alert(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat_engine():
    if request.method == 'OPTIONS': return jsonify({"status": "ok"}), 200

    data = request.json
    user_message = data.get('message', '')

    # 1. API End-point (Latest Google AI Studio Endpoint)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={AI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{
            "parts": [{"text": f"You are a helpful AI assistant. Keep responses short and friendly. If the user provides a name AND email/phone, output: LEAD_SECURED_NAME:{user_message}"}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        ai_data = response.json()
        
        # জেমিনাই এর রেসপন্স থেকে টেক্সট বের করা
        reply = ai_data['candidates'][0]['content']['parts'][0]['text']
        
        # লিড ডিটেকশন সিম্পল লজিক
        if "LEAD_SECURED_NAME" in reply:
            threading.Thread(target=send_telegram_alert, args=(f"🚀 <b>LEAD SECURED!</b>\n{reply}",)).start()
            return jsonify({"reply": "Details logged successfully! Our team will contact you soon."})

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": "AI Brain waking up! Please try again in a few seconds."}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
