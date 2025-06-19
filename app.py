import os
import re
import requests
import random
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from dotenv import load_dotenv
import openai
from twilio.rest import Client

# Load env variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "temporary-secret")
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

OCR_API_KEY = os.getenv("OCR_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")

openai.api_key = TOGETHER_API_KEY
openai.base_url = "https://api.together.xyz/v1"

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

with open("aadhaar_filter_keywords.txt", "r") as f:
    unwanted = [line.strip().lower() for line in f]

def clean_ocr_text(text):
    lines = text.split("\n")
    return "\n".join(line for line in lines if all(word not in line.lower() for word in unwanted))

@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/symptoms', methods=['GET', 'POST'])
def symptoms():
    if request.method == 'POST':
        symptoms_text = request.form.get("symptoms")
        severity = request.form.get("severity")

        if not symptoms_text:
            return "<h2>Please enter your symptoms.</h2><a href='/symptoms'>🡸 Try Again</a>"

        session['symptoms'] = symptoms_text
        session['severity'] = severity

        return redirect(url_for('image_upload'))

    return render_template("symptoms.html")

@app.route('/imageupload', methods=['GET', 'POST'])
def image_upload():
    if request.method == 'POST':
        image_file = request.files.get('image')
        video_file = request.files.get('video')

        uploaded_files = []

        for file in [image_file, video_file]:
            if file and file.filename:
                filename = file.filename.replace(" ", "_")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                uploaded_files.append(filepath)

        print("✅ Uploaded media files:", uploaded_files)

        return redirect(url_for("aadhaar"))

    return render_template("imageupload.html")

@app.route('/aadhaar', methods=['GET', 'POST'])
def aadhaar():
    if request.method == 'GET':
        return render_template("aadhaar.html")

    aadhaar_file = request.files.get('aadhaar')

    if not aadhaar_file or aadhaar_file.filename == '':
        return """
        <h2>No Aadhaar file uploaded. Please try again.</h2>
        <a href='/aadhaar'>🡸 Try Again</a>
        """

    if not aadhaar_file.filename.lower().endswith('.pdf'):
        return """
        <h2>Only PDF format is currently supported.</h2>
        <a href='/aadhaar'>🡸 Try Again</a>
        """

    filename = aadhaar_file.filename.replace(" ", "_")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    aadhaar_file.save(filepath)

    with open(filepath, 'rb') as f:
        ocr_result = requests.post(
            'https://api.ocr.space/parse/image',
            files={"filename": f},
            data={"apikey": OCR_API_KEY, "isOverlayRequired": False, "OCREngine": 2, "scale": True, "isTable": False}
        )

    try:
        raw_text = ocr_result.json()['ParsedResults'][0]['ParsedText']
    except (KeyError, IndexError):
        return """
        <h2>OCR failed. Please try with a clearer Aadhaar PDF.</h2>
        <a href='/aadhaar'>🡸 Try Again</a>
        """

    print("🔍 Raw OCR Text:\n", raw_text)
    cleaned_text = clean_ocr_text(raw_text)
    print("🧹 Cleaned OCR Text:\n", cleaned_text)

    aadhaar_match = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b', cleaned_text)
    dob_match = (
        re.search(r'\d{2}[/-]\d{2}[/-]\d{4}', cleaned_text) or
        re.search(r'Year\s*of\s*Birth\s*[:\s]*((?:19|20)\d{2})', cleaned_text, re.IGNORECASE) or
        re.search(r'\b(19|20)\d{2}\b', cleaned_text)
    )

    name_match = None
    for line in cleaned_text.split("\n"):
        if ':' in line:
            continue
        if re.match(r'^[A-Z][a-z]+(\s[A-Z][a-z]+)+$', line.strip()):
            name_match = line.strip()
            break

    extracted_name = name_match if name_match else "Name Not Detected"
    extracted_dob = dob_match.group(1) if dob_match else "DOB Not Detected"
    extracted_aadhaar = aadhaar_match.group() if aadhaar_match else "Aadhaar Not Detected"

    print("✅ Extracted Name:", extracted_name)
    print("✅ Extracted DOB:", extracted_dob)
    print("✅ Extracted Aadhaar:", extracted_aadhaar)

    return redirect(url_for('report',
        name=extracted_name,
        dob=extracted_dob,
        aadhaar=extracted_aadhaar,
        symptoms=session.get("symptoms", "")
    ))

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
Based on the symptoms, the condition could range from a mild infection to a potentially serious illness. Please consider clinical examination.

Plan:
1. Immediate consultation with a physician.
2. Blood tests and imaging if necessary.
3. Monitor temperature and pain levels regularly.

Triage Severity Score: 7/10

One-line health advice: Please seek urgent medical attention if symptoms worsen or do not improve.
"""

@app.route('/report')
def report():
    name = request.args.get("name")
    dob = request.args.get("dob")
    aadhaar = request.args.get("aadhaar")
    symptoms = request.args.get("symptoms", "").lower()

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

Use only the verified patient data below. Provide a clinically realistic and useful output.

Patient Name: {name}
Date of Birth: {dob}
Aadhaar: {aadhaar}

Symptoms:
"{symptoms}"

Instructions:
- Summarize the patient's complaint in Subjective.
- Leave Objective blank unless there's medical data.
- Make an educated clinical Assessment (avoid vague "common condition" remarks).
- Suggest specific Plan actions.
- Assign a triage score.
- Give one-line advice based only on symptoms.
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

    return render_template("report.html", name=name, dob=dob, aadhaar=aadhaar, soap=soap_note)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
