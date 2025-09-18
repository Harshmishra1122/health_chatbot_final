# app.py (FINAL VERSION with Background Model Loading)

import sqlite3
from flask import Flask, render_template, request
import os
import google.generativeai as genai
import threading # <-- NEW IMPORT

# --- Initialize the Flask App FIRST ---
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

# --- Call the function to set up the database BEFORE the app starts ---
with app.app_context():
    init_db()

# --- CONFIGURATION ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") 
genai.configure(api_key=GOOGLE_API_KEY)

# =================================================================
# NEW: BACKGROUND MODEL LOADING
# =================================================================
# We start with empty models and a flag to track loading status
generative_model = None
models_loaded = False

def load_models_background():
    """This function will run in a separate thread to load models without blocking."""
    global generative_model, models_loaded
    print("Background thread started: Initializing models...")
    
    generation_config = { "temperature": 0.7, "top_p": 1, "top_k": 1, "max_output_tokens": 2048, }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    
    generative_model = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash-latest",
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    models_loaded = True
    print("Generative AI model loaded successfully in background. Server is fully ready.")

# Start the background thread to load the models
model_loader_thread = threading.Thread(target=load_models_background)
model_loader_thread.start()
# =================================================================

intent_keywords = {
    "malaria_prevention": ["malaria", "mosquito", "mosquitoes", "insect", "bite", "bites", "prevent"],
    "dengue_symptoms": ["dengue", "joint", "pain", "eyes", "headache"],
    "covid_symptoms": ["covid", "cough", "fever", "taste", "smell", "tiredness", "sars"],
    "common_cold_treatment": ["cold", "runny", "nose", "sneeze", "sore", "throat"],
    "newborn_vaccination": ["newborn", "baby", "babies", "vaccine", "vaccination", "schedule", "shot", "shots"]
}

chat_history = []

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

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
    # --- NEW CHECK: Wait for models to be loaded ---
    if not models_loaded or not generative_model:
        return "The AI is still warming up. Please try again in 30 seconds."
    # --- END NEW CHECK ---
    try:
        prompt = f"""You are a helpful and compassionate AI Health Assistant from India. Your goal is to provide clear, general health information based on trusted sources like the WHO. You must never give medical advice or a diagnosis. If a user seems to be in distress or asks for a diagnosis, you must gently guide them to consult a real doctor.
        
        The user's question is: "{user_message}"
        
        Your answer (in a friendly, conversational tone):"""
        response = generative_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error with Generative AI: {e}")
        return "I'm sorry, I'm having trouble connecting to my advanced knowledge base right now."

@app.route("/", methods=['GET', 'POST'])
def chat():
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

@app.route('/health')
def health_check():
    """A simple route that Render can check to see if the app is alive."""
    return "OK", 200