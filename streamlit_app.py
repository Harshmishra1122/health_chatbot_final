# streamlit_app.py (The Final Streamlit Version)

import streamlit as st
import sqlite3
import os
import google.generativeai as genai

# --- DATABASE INITIALIZATION FUNCTION ---
def init_db():
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
    conn.commit()
    conn.close()

# --- Call the function to ensure DB is ready when the app starts ---
init_db()

# --- CONFIGURATION & MODEL LOADING ---
# We get the key from Streamlit's secrets manager
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

generative_model = None
if GOOGLE_API_KEY:
    try:
        generation_config = { "temperature": 0.7, "top_p": 1, "top_k": 1, "max_output_tokens": 2048 }
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
    except Exception as e:
        st.error(f"Error initializing Generative AI: {e}")
# --- END CONFIGURATION & MODEL LOADING ---


intent_keywords = {
    "malaria_prevention": ["malaria", "mosquito", "mosquitoes", "insect", "bite", "bites", "prevent"],
    "dengue_symptoms": ["dengue", "joint", "pain", "eyes", "headache"],
    "covid_symptoms": ["covid", "cough", "fever", "taste", "smell", "tiredness", "sars"],
    "common_cold_treatment": ["cold", "runny", "nose", "sneeze", "sore", "throat"],
    "newborn_vaccination": ["newborn", "baby", "babies", "vaccine", "vaccination", "schedule", "shot", "shots"]
}

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
    if not generative_model:
        return "The Generative AI model is not available. Please check the API key configuration."
    try:
        prompt = f"""You are a helpful and compassionate AI Health Assistant from India...""" # (prompt is the same)
        response = generative_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Sorry, there was an error with the AI: {e}"

# --- STREAMLIT UI CODE ---
st.title("AI Health Assistant 🩺")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
if prompt := st.chat_input("Ask a health question..."):
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response
    intent = get_intent_from_keywords(prompt)
    bot_response = ""
    if intent != "fallback":
        conn = get_db_connection()
        result = conn.execute('SELECT answer FROM faqs WHERE intent = ?', (intent,)).fetchone()
        conn.close()
        bot_response = result['answer'] if result else get_generative_response(prompt)
    else:
        bot_response = get_generative_response(prompt)

    # Add bot response to history and display it
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    with st.chat_message("assistant"):
        st.markdown(bot_response)