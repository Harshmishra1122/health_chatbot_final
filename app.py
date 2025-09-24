# app.py (FINAL VERSION with Private Sessions + SIH Prompt)

import sqlite3
from flask import Flask, render_template, request, session
import os
import google.generativeai as genai
from datetime import timedelta

app = Flask(__name__)

# --- SECRET KEY FOR SESSIONS ---
app.secret_key = 'your_very_secret_key_here'   # <-- REQUIRED for private sessions
app.permanent_session_lifetime = timedelta(hours=1)  # Store history for 1 hour
# --- END NEW PART ---

# --- CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyCIRszDPqKAAT1bNO6RZhNcMDcynnS2BIw"  # <-- keep only your real key
genai.configure(api_key=GOOGLE_API_KEY)
# --- END CONFIGURATION ---

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
    cursor.execute("SELECT COUNT(*) FROM faqs")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_faqs = [
            ("dengue_symptoms", "What are the symptoms of dengue?",
             "Common symptoms include high fever, headache, pain behind the eyes, and joint and muscle pain."),
            ("malaria_prevention", "How can I prevent malaria?",
             "Prevent malaria by using mosquito nets, applying insect repellent, and removing stagnant water around your home."),
            ("newborn_vaccination", "What is the vaccination schedule for a newborn?",
             "A newborn should get the BCG, Oral Polio Vaccine (OPV 0), and Hepatitis B (Birth Dose) vaccines."),
            ("covid_symptoms", "What are the symptoms of covid?",
             "Common symptoms are fever, cough, tiredness, and loss of taste or smell. Seek medical help for severe symptoms."),
            ("common_cold_treatment", "How to treat a common cold?",
             "For a common cold, general advice includes rest, staying hydrated, and using over-the-counter remedies for symptoms. This is not a substitute for medical advice.")
        ]
        cursor.executemany(
            "INSERT INTO faqs (intent, question, answer) VALUES (?, ?, ?)",
            sample_faqs
        )
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

# =================================================================
# LOAD MODEL
# =================================================================
print("Initializing AI model...")
generative_model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")
print("AI model loaded.")


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- SIH FINAL PROMPT (unchanged) ---
def get_generative_response(user_message):
    try:
        prompt = f"""You are "Arogya Sathi," an AI Health Assistant for the Smart India Hackathon.
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
- ALWAYS advise consulting a qualified doctor for serious or persistent problems.  

**User's Question:** "{user_message}"

**Your concise, safe, and helpful answer (in the user's language):**
"""
        response = generative_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error with Generative AI: {e}")
        return "I'm sorry, I’m having trouble answering that right now. Please try again."

# --- SESSION-BASED CHAT ---
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


if __name__ == '__main__':
    app.run(debug=True)
