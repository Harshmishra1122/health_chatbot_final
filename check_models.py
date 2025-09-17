# check_models.py

import google.generativeai as genai

# --- CONFIGURATION ---
# IMPORTANT: 
GOOGLE_API_KEY = "AIzaSyCIRszDPqKAAT1bNO6RZhNcMDcynnS2BIw" 
genai.configure(api_key=GOOGLE_API_KEY)
# --- END CONFIGURATION ---

print("Finding all models your API key can use...")
print("-" * 20)

# This loop goes through all available models and prints the ones that can generate text
for m in genai.list_models():
  if 'generateContent' in m.supported_generation_methods:
    print(m.name)

print("-" * 20)
print("Finished. If you see a model name above, that is the one we should use in app.py")