# app.py (Final Deployed Version with DB Setup)

import sqlite3
from flask import Flask, render_template, request
import os
import google.generativeai as genai

app = Flask(__name__)

# --- DATABASE INITIALIZATION FUNCTION ---
def init_db():
    """Initializes the database and creates the table if it doesn't exist."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent TEXT NOT NULL UNIQUE,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    ''')
    
    # Add sample data if the table is empty
    cursor.execute("SELECT COUNT(*) FROM faqs")
    count = cursor.fetchone()[0]
    if count == 0:
        print("Database is empty, populating with sample data...")
        sample_faqs = [
            ("dengue_symptoms", "What are the symptoms of dengue?", "Common symptoms include high fever, headache, pain behind the eyes, and joint and muscle pain."),
            ("malaria_prevention", "How can I prevent malaria?", "Prevent malaria by using mosquito nets, applying insect repellent, and removing stagnant water around your home."),
            ("newborn_vaccination", "What is the vaccination schedule for a newborn?", "A newborn should get the BCG, Oral Polio Vaccine (OPV 0), and Hepatitis B (Birth Dose) vaccines."),
            ("covid_symptoms", "What are the symptoms of covid?", "Common symptoms are fever, cough, tiredness, and loss of taste or smell. Seek medical help for severe symptoms."),
            ("common_cold_treatment", "How to treat a common cold?", "Rest, drink plenty of fluids, and use over-the-counter medications for symptoms. Consult a doctor if it worsens.")
        ]
        cursor.executemany('INSERT INTO faqs (intent, question, answer) VALUES (?, ?, ?)', sample_faqs)
        print("Database populated successfully.")
    else:
        print("Database already contains data.")

    conn.commit()
    conn.close()

# --- Call the function to ensure DB is ready when the app starts ---
init_db()
# --- END DATABASE INITIALIZATION ---


# --- CONFIGURATION ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") 
genai.configure(api_key=GOOGLE_API_KEY)
# --- END CONFIGURATION ---

# =================================================================
# LOAD MODELS
# =================================================================
print("Initializing models...")
generation_config = { "temperature": 0.7, "top_p": 1, "top_k": 1, "max_output_tokens": 2048, }
safety_settings = [
    # (safety settings remain the same)
]
generative_model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash-latest",
    generation_config=generation_config,
    safety_settings=safety_settings
)
print("Generative AI model loaded. Server is ready.")
# =================================================================

intent_keywords = {
    # (keywords remain the same)
}

chat_history = []

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ... (The rest of your code, get_intent_from_keywords, get_generative_response, chat(), remains exactly the same) ...

def get_intent_from_keywords(user_message):
    user_message = user_message.lower()
    scores = {}
    for intent, keywords in intent_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in user_message:
                score += 1
        scores[intent] = score
    best_intent = max(scores, key=scores.get)
    if scores[best_intent] == 0:
        return "fallback"
    return best_intent

def get_generative_response(user_message):
    try:
        prompt = f"""You are a helpful and compassionate AI Health Assistant from India...""" # (prompt remains the same)
        response = generative_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error with Generative AI: {e}")
        return "I'm sorry, I'm having trouble connecting to my advanced knowledge base right now."

@app.route("/", methods=['GET', 'POST'])
def chat():
    # This entire function remains the same
    if request.method == 'POST':
        user_message = request.form['message']
        chat_history.append({"sender": "You", "message": user_message})
        intent = get_intent_from_keywords(user_message)
        if intent != "fallback":
            conn = get_db_connection()
            result = conn.execute('SELECT answer FROM faqs WHERE intent = ?', (intent,)).fetchone()
            conn.close()
            bot_response = result['answer'] if result else get_generative_response(user_message)
        else:
            bot_response = get_generative_response(user_message)
        chat_history.append({"sender": "Bot", "message": bot_response})
    return render_template("index.html", chat_history=chat_history)

if __name__ == '__main__':
    app.run(debug=True)