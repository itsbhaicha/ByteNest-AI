import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import threading

app = Flask(__name__)
CORS(app)

# YOUR SECURE DATA (Private Repo হলে এটি সেফ)
AI_API_KEY = "AIzaSyAKPRZHNopY770bdvhiqndH40cgUH8rhlo"
TELEGRAM_TOKEN = "8798938808:AAF712x7YhG_EQWw2HJ9_G4vymL8rseSbrI"
TELEGRAM_CHAT_ID = "8127463560"

# Telegram Function
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

# Chat API Route
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', '')
    
    if not user_msg:
        return jsonify({"reply": "System Error: Message transmission null."}), 400

    # Gemini 1.5 Flash End-point (Fastest)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={AI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": f"User: {user_msg}. If user provides name and phone/email, respond with: 'LEAD_SECURED: [Name]' followed by confirmation. Otherwise answer briefly."}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        result = response.json()
        
        # জেমিনাই রেসপন্স চেক
        if "candidates" not in result:
            return jsonify({"reply": "AI Node is busy, please try again."})
            
        reply = result['candidates'][0]['content']['parts'][0]['text']
        
        # Lead Detection
        if "LEAD_SECURED" in reply:
            threading.Thread(target=send_telegram, args=(f"🚀 <b>LEAD SECURED!</b>\n{reply}",)).start()
            return jsonify({"reply": "Details logged successfully! Our support team will contact you soon."})
            
        return jsonify({"reply": reply})
        
    except Exception as e:
        return jsonify({"reply": "System operational anomaly."}), 500

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "ByteNest Core Active"}), 200

if __name__ == '__main__':
    # Render Port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
