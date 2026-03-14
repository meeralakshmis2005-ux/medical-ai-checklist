from flask import Flask, request, jsonify
import openai
import json
from pymongo import MongoClient
import os

# --------------------------
# Groq / OpenAI API key
# Make sure to set as environment variable in VS Code terminal:
# Windows: set GROQ_API_KEY=YOUR_KEY
# Mac/Linux: export GROQ_API_KEY=YOUR_KEY
openai.api_key = os.environ.get("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")

# MongoDB Atlas connection
MONGO_URI = "mongodb+srv://gayathrisubramanian2006_db_user:<Mongo@223DB>@medicalai.ekrw2wb.mongodb.net/?appName=MedicalAI"
client = MongoClient(MONGO_URI)
db = client["MedicalAI"]       # Database name
patients_collection = db["Patientdetails"]  # Collection name
# --------------------------

app = Flask(__name__)

@app.route("/generate_checklist", methods=["POST"])
def generate_checklist():
    data = request.json
    patient_name = data.get("name")
    age = data.get("age")
    allergies = data.get("allergy")
    medications = data.get("medications")
    procedure = data.get("procedure")

    prompt = f"""
You are a medical safety AI assistant. Generate a step-by-step checklist and warnings.
Patient Name: {patient_name}
Age: {age}
Allergies: {allergies}
Current Medications: {medications}
Procedure: {procedure}

Return JSON object:
{{
  "checklist": ["step 1", "step 2", "..."],
  "warnings": ["warning 1", "warning 2", "..."]
}}
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        content = response['choices'][0]['message']['content']
        output = json.loads(content)
    except Exception as e:
        output = {
            "checklist": [
                f"Verify patient identity: {patient_name}",
                f"Confirm procedure: {procedure}",
                "Check allergies and current medications",
                "Ensure consent form signed",
                "Monitor vital signs"
            ],
            "warnings": []
        }

    # Save patient info + checklist in MongoDB
    patient_record = {
        "name": patient_name,
        "age": age,
        "allergies": allergies,
        "medications": medications,
        "procedure": procedure,
        "checklist": output["checklist"],
        "warnings": output["warnings"]
    }
    patients_collection.insert_one(patient_record)

    return jsonify(output)

if __name__ == "__main__":
    app.run(debug=True)