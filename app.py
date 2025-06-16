import os
import re
import requests
import random
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from dotenv import load_dotenv
import openai
from twilio.rest import Client

# 🔹 Load environment variables
load_dotenv()

# 🔹 App setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "temporary-secret")
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔹 Environment configs
OCR_API_KEY = os.getenv("OCR_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")

print("🔐 TWILIO_ACCOUNT_SID:", TWILIO_ACCOUNT_SID)
print("🔐 TWILIO_AUTH_TOKEN:", TWILIO_AUTH_TOKEN)
print("🔐 TWILIO_VERIFY_SERVICE_SID:", TWILIO_VERIFY_SERVICE_SID)

# 🔹 OpenAI client config for Together AI
openai.api_key = TOGETHER_API_KEY
openai.base_url = "https://api.together.xyz/v1"

# 🔹 Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# 🔹 Aadhaar filter
with open("aadhaar_filter_keywords.txt", "r") as f:
    unwanted = [line.strip().lower() for line in f]

def clean_ocr_text(text):
    lines = text.split("\n")
    return "\n".join(line for line in lines if all(word not in line.lower() for word in unwanted))

# ─────────────────────────────────────────────
# ✅ ROUTES
# ─────────────────────────────────────────────

@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/symptoms')
def symptoms():
    return render_template("symptoms.html")

# ─────────────────────────────────────────────
# ✅ SEND OTP using Twilio Verify
# ─────────────────────────────────────────────
@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    phone = data.get("phone")

    if not phone:
        return jsonify({"success": False, "error": "Phone number missing"}), 400

    try:
        verification = twilio_client.verify.services(TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=phone,
            channel='sms'
        )
        return jsonify({"success": True, "message": "OTP sent"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─────────────────────────────────────────────
# ✅ VERIFY OTP using Twilio
# ─────────────────────────────────────────────
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    phone = data.get("phone")
    code = data.get("otp")

    try:
        verification_check = twilio_client.verify.services(TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
            to=phone,
            code=code
        )

        if verification_check.status == "approved":
            session["user"] = phone
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Invalid OTP"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/aadhaar', methods=['POST'])
def aadhaar():
    try:
        symptoms = request.form['symptoms']
        aadhaar_file = request.files['aadhaar']

        if not aadhaar_file:
            return "<h2>No file uploaded. Please try again.</h2><a href='/symptoms'>🡸 Try Again</a>"

        filename = aadhaar_file.filename.replace(" ", "_")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        aadhaar_file.save(filepath)

        with open(filepath, 'rb') as f:
            ocr_result = requests.post(
                'https://api.ocr.space/parse/image',
                files={"filename": f},
                data={"apikey": OCR_API_KEY}
            )

        raw_text = ocr_result.json()['ParsedResults'][0]['ParsedText']
        print("🔍 Raw OCR Text:\n", raw_text)

        cleaned_text = clean_ocr_text(raw_text)
        print("🧹 Cleaned OCR Text:\n", cleaned_text)

        aadhaar_match = re.search(r'\d{4}\s\d{4}\s\d{4}', cleaned_text)
        dob_match = re.search(r'\d{2}[/-]\d{2}[/-]\d{4}', cleaned_text)
        if not dob_match:
            dob_match = re.search(r'\b(19|20)\d{2}\b', cleaned_text)

        name_match = (
            re.search(r'Name[:\s]*([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)', cleaned_text) or
            re.search(r'[A-Z][a-z]+(?:\s[A-Z][a-z]+)+', cleaned_text) or
            re.search(r'[A-Z]{3,}(?:\s[A-Z]{3,})*', cleaned_text)
        )

        if not (aadhaar_match and dob_match and name_match):
            return """
            <h2>❌ Aadhaar extraction failed. Please upload a clearer Aadhaar card image.</h2>
            <a href='/symptoms'>🡸 Try Again</a>
            """

        extracted_name = name_match.group(1) if name_match.lastindex else name_match.group()
        extracted_dob = dob_match.group().replace("-", "/")
        extracted_aadhaar = aadhaar_match.group()

        print("✅ Extracted Name:", extracted_name)
        print("✅ Extracted DOB:", extracted_dob)
        print("✅ Extracted Aadhaar:", extracted_aadhaar)

        return redirect(url_for('report',
            name=extracted_name,
            dob=extracted_dob,
            aadhaar=extracted_aadhaar,
            symptoms=symptoms
        ))

    except Exception as e:
        print("⚠️ OCR Error:", str(e))
        return """
        <h2>Unexpected error occurred while processing the Aadhaar. Please try again.</h2>
        <a href='/symptoms'>🡸 Try Again</a>
        """

def generate_soap_strict(symptoms, name, dob, aadhaar):
    return f"""
SOAP Report for {name}
Date of Birth: {dob}
Aadhaar Number: {aadhaar}

SOAP Note:

Subjective:
The patient, {name}, reports the following symptoms: {symptoms}

Objective:
No vital signs or physical examination data provided.

Assessment:
The described symptoms may be associated with common conditions. Further diagnostic evaluation is recommended for a more accurate assessment.

Plan:
1. Visit a local health center or hospital for examination.
2. Basic diagnostic tests (e.g., CBC, imaging) may be required based on symptoms.
3. Follow general advice on hydration, rest, and symptom tracking.

Triage Severity Score: 5/10

One-line health advice: Please consult a doctor for further evaluation of your symptoms.
"""

@app.route('/report')
def report():
    name = request.args.get("name")
    dob = request.args.get("dob")
    aadhaar = request.args.get("aadhaar")
    symptoms = request.args.get("symptoms").lower()

    with open("symptom_keywords.txt", "r") as file:
        keywords = [line.strip().lower() for line in file if line.strip()]
    matches = sum(1 for word in keywords if word in symptoms)

    if matches < 2:
        return f"""
        <h2>Invalid Symptom Description</h2>
        <p>Your input doesn't seem to describe enough medical symptoms.</p>
        <p>Please try again with more specific symptoms (e.g., 'fever and headache after eating').</p>
        <br><br>
        <a href='/symptoms'>🡸 Back to Start</a>
        """

    prompt = f"""
You are a medical assistant generating a SOAP (Subjective, Objective, Assessment, Plan) note.

Please use only the following verified patient details and the symptom description. Do not add or assume any extra symptoms or diagnoses.

Patient Name: {name}
Date of Birth: {dob}
Aadhaar: {aadhaar}

Symptoms Reported by Patient:
"{symptoms}"

Instructions:
- Use only the symptoms provided — do not fabricate or modify them.
- The note should follow the SOAP format:
  - Subjective: Summarize what the patient described in simple clinical language.
  - Objective: Leave this section blank unless examination data is provided.
  - Assessment: Explain what could be the likely causes based only on the given symptoms.
  - Plan: Recommend reasonable next steps (e.g., rest, hydration, tests, common meds, or doctor visit).
- Add a triage severity score out of 10 based on urgency.
- Conclude with a one-line health advice based on the same symptoms.

Make the response realistic, useful, and grounded only in the data provided above.
"""

    try:
        response = openai.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {"role": "system", "content": "Generate a SOAP note strictly from symptoms."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024
        )
        soap_note = response.choices[0].message.content.strip()

        if "pain" in soap_note.lower() and "pain" not in symptoms:
            raise ValueError("Possible hallucination detected in SOAP.")

    except Exception as e:
        print("AI fallback reason:", str(e))
        soap_note = generate_soap_strict(symptoms, name, dob, aadhaar)

    return f"""
    <h2>SOAP Report for {name}</h2>
    <p><b>Date of Birth:</b> {dob}</p>
    <p><b>Aadhaar Number:</b> {aadhaar}</p>
    <pre>{soap_note}</pre>
    <br><br>
    <a href='/symptoms'>🡸 Back to Start</a>
    """

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
