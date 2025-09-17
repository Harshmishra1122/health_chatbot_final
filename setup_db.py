# setup_db.py (Day 3 Version)

import sqlite3

# Connect to the database
connection = sqlite3.connect('database.db')
cursor = connection.cursor()

# Drop the old table if it exists, so we can create the new one
cursor.execute('DROP TABLE IF EXISTS faqs')

# Create the new 'faqs' table with an 'intent' column
cursor.execute('''
    CREATE TABLE faqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intent TEXT NOT NULL UNIQUE,
        question TEXT NOT NULL,
        answer TEXT NOT NULL
    )
''')

# --- Add our categorized data ---
# The 'intent' is a simple category name for the AI to find.
sample_faqs = [
    ("dengue_symptoms", "What are the symptoms of dengue?", "Common symptoms include high fever, headache, pain behind the eyes, and joint and muscle pain."),
    ("malaria_prevention", "How can I prevent malaria?", "Prevent malaria by using mosquito nets, applying insect repellent, and removing stagnant water around your home."),
    ("newborn_vaccination", "What is the vaccination schedule for a newborn?", "A newborn should get the BCG, Oral Polio Vaccine (OPV 0), and Hepatitis B (Birth Dose) vaccines."),
    ("covid_symptoms", "What are the symptoms of covid?", "Common symptoms are fever, cough, tiredness, and loss of taste or smell. Seek medical help for severe symptoms."),
    ("common_cold_treatment", "How to treat a common cold?", "Rest, drink plenty of fluids, and use over-the-counter medications for symptoms. Consult a doctor if it worsens.")
]

# Insert the data into the table
cursor.executemany('INSERT INTO faqs (intent, question, answer) VALUES (?, ?, ?)', sample_faqs)

connection.commit()
connection.close()

print("Database upgraded for Day 3 and populated successfully!")