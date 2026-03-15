from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import json
from pymongo import MongoClient
import os
import urllib.parse

# --------------------------
# Groq / OpenAI API key
api_key = os.environ.get("GROQ_API_KEY", "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")
ai_client = openai.OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

# MongoDB Atlas connection
password = urllib.parse.quote_plus("Mongo@223DB")
MONGO_URI = f"mongodb+srv://gayathrisubramanian2006_db_user:{password}@medicalai.ekrw2wb.mongodb.net/?appName=MedicalAI"
try:
    client = MongoClient(MONGO_URI)
    db = client["MedicalAI"]       # Database name
    patients_collection = db["Patientdetails"]  # Collection name
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    patients_collection = None
# --------------------------

app = Flask(__name__)
CORS(app)

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
        response = ai_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        content = response.choices[0].message.content
        output = json.loads(content)
    except Exception as e:
        print(f"Failed to generate checklist: {e}")
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
    if patients_collection is not None:
        try:
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
        except Exception as e:
            print(f"Failed to insert patient record: {e}")

    return jsonify(output)

@app.route("/query_assistant", methods=["POST"])
def query_assistant():
    data = request.json
    user_query = data.get("query", "")
    
    if not user_query:
        return jsonify({"response": "Please provide a query."}), 400

    # Step 1: Extract patient name using LLM
    extract_prompt = f"""
    Extract the patient name from the following user query. 
    If you cannot find a clear patient name, return null.
    User Query: "{user_query}"
    Return ONLY a valid JSON object in this exact format, with no extra text or markdown:
    {{"patient_name": "extracted_name" or null}}
    """
    
    try:
        extract_response = ai_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": extract_prompt}],
            temperature=0.1
        )
        extract_content = extract_response.choices[0].message.content.strip()
        # sometimes LLMs return markdown wrapper
        if extract_content.startswith("```json"):
            extract_content = extract_content[7:-3].strip()
        elif extract_content.startswith("```"):
            extract_content = extract_content[3:-3].strip()
            
        extracted_data = json.loads(extract_content)
        patient_name = extracted_data.get("patient_name")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Extraction failed: {e}")
        patient_name = None

    # Step 2: Query the database
    patient_data = None
    if patient_name and patients_collection is not None:
        try:
            # Case-insensitive search for the patient name
            patient_data = patients_collection.find_one(
                {"name": {"$regex": patient_name, "$options": "i"}},
                {"_id": 0} # Exclude the MongoDB ObjectId from results
            )
        except Exception as e:
            print(f"Database query failed: {e}")

    # Step 3: Generate the final conversational response
    if patient_data:
        response_prompt = f"""
        The user asked: "{user_query}"
        Here is the relevant patient data found in the database:
        {json.dumps(patient_data, indent=2)}
        
        Write a natural, helpful, and professional response answering the user's query using only the provided data.
        """
    else:
        response_prompt = f"""
        The user asked: "{user_query}"
        I searched the database but could not find a matching patient record. 
        Write a polite response informing the user that the patient could not be found or that the query was unclear.
        """

    try:
        final_response = ai_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": response_prompt}],
            temperature=0.5
        )
        answer = final_response.choices[0].message.content
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed to generate final response: {e}")
        answer = "I'm sorry, I encountered an error while processing your request."

    return jsonify({"response": answer})

if __name__ == "__main__":
    app.run(debug=True)