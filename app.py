# app.py (Final Version — Corrected for OpenRouter API)

import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for
import os
import requests # Using requests to send custom headers
import json     # To format the data for the request
from datetime import timedelta

app = Flask(__name__)

# --- SECRET KEY FOR SESSIONS ---
app.secret_key = 'arogya_sathi_sih_2025_secret_key'
app.permanent_session_lifetime = timedelta(hours=1)

# --- CONFIGURATION FOR OPENROUTER ---
# The new API key has been pasted directly here.
OPENROUTER_API_KEY = "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"

# =================================================================
# DATABASE SETUP
# =================================================================
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent TEXT NOT NULL UNIQUE,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Corrected this line
with app.app_context():
    init_db()

# =================================================================
# AI RESPONSE FUNCTION (Final working version)
# =================================================================
def get_generative_response(user_message):
    system_prompt = f"""You are "Arogya Sathi," an AI Health Assistant for the Smart India Hackathon.
Your mission is to educate rural and semi-urban populations in India about preventive healthcare. 
You must always be safe, simple, and concise. Your knowledge is integrated with government health databases 
and regional outbreak information.

**Core Mission Objectives:**
1. Preventive Healthcare: Share clear, easy-to-follow tips on hygiene, nutrition, safe water, and lifestyle.  
2. Disease Awareness: Explain common disease symptoms in simple language.  
3. Vaccination Schedules: Share newborn and child vaccination schedules as per Indian health guidelines.  
4. Generic Daily Advice: Always provide small, actionable tips (drink clean water, wash hands, use mosquito nets).  
5. Safe Home Remedies: Suggest harmless natural remedies (like warm water, turmeric milk, steam inhalation).  
6. Suggest Meals: Recommend light and safe meals for recovery (rice and dal, fruits, leafy vegetables).  
7. Regional Disease Detection: Mention seasonal diseases in India (like dengue during monsoon, flu during winter).  
8. Safe Medicines: Mention only very safe remedies (ORS, paracetamol for mild fever) with age considerations.  
9. Follow-Up: If unclear, ask follow-up questions in the user's language (English, Hindi, or Hinglish).  
10. Weekly Health Checkups: Remind users to monitor weight, hydration, diet, and BP weekly.  
11. Educational Tips: Always add 1–2 awareness tips (wash hands, boil water, eat balanced meals).  
12. Language: Detect the user’s language and reply in the SAME simple language.  
13. Outbreak Alerts: If asked, say you can provide real-time alerts from official sources.  

**Critical Safety Rules:**
- NEVER give a confirmed diagnosis.  
- NEVER prescribe antibiotics or risky medicines.  
- ALWAYS advise consulting a qualified doctor for serious or persistent problems."""

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            # This URL is for the live Render deployment
            "HTTP-Referer": "https://health-chatbot-project-33ia.onrender.com", 
            "X-Title": "Arogya Sathi"
        }

        data = {
            # Using the Google Gemini Flash model as requested
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return "मुझे क्षमा करें, AI कोई जवाब नहीं दे सका।"
        else:
            print(f"❌ API call failed with status code {response.status_code}: {response.text}")
            return "मुझे क्षमा करें, अभी AI जवाब देने में असमर्थ है।"

    except Exception as e:
        print(f"❌ An exception occurred: {e}")
        return "मुझे क्षमा करें, अभी उत्तर देने में कोई समस्या आ रही है। कृपया बाद में प्रयास करें।"

# =================================================================
# CHAT ROUTES
# =================================================================
@app.route("/", methods=['GET', 'POST'])
def chat():
    session.permanent = True
    if 'chat_history' not in session:
        session['chat_history'] = []

    if request.method == 'POST':
        user_message = request.form['message']
        session['chat_history'].append({"sender": "You", "message": user_message})

        bot_response = get_generative_response(user_message)
        session['chat_history'].append({"sender": "Bot", "message": bot_response})

        session.modified = True

    return render_template("index.html", chat_history=session['chat_history'])

@app.route("/clear")
def clear_chat():
    session.pop('chat_history', None)
    return redirect(url_for('chat'))

# =================================================================
# RUN APP
# =================================================================
if __name__ == '__main__':
    app.run(debug=True)

