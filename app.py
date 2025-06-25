import os
import re
import requests
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
from together import Together
from twilio.rest import Client
import assemblyai as aai
from flask import jsonify
import base64

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "temporary-secret")
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

OCR_API_KEY = os.getenv("OCR_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")

# Load AssemblyAI API key from .env
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

# AI Client
client = Together()

# Twilio Client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Aadhaar filter keywords
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

# --- Transcribe Audio Route ---
@app.route('/transcribe-audio', methods=['POST'])
def transcribe_audio_file():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file uploaded'}), 400

    audio_file = request.files['audio']
    temp_path = os.path.join("static/uploads", audio_file.filename)
    audio_file.save(temp_path)

    try:
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(temp_path)

        if transcript.status == "error":
            return jsonify({'error': transcript.error}), 500

        return jsonify({'text': transcript.text})
    except Exception as e:
        print("Transcription error (file):", str(e))
        return jsonify({'error': 'Failed to transcribe'}), 500


@app.route('/transcribe', methods=['POST'])
def transcribe_audio_base64():
    data = request.get_json()
    audio_base64 = data.get("audio")

    if not audio_base64:
        return jsonify({"error": "No audio data"}), 400

    try:
        audio_bytes = base64.b64decode(audio_base64)
        temp_path = "static/uploads/temp_audio.wav"
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)

        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(temp_path)

        if transcript.status == "error":
            return jsonify({"error": transcript.error}), 500

        return jsonify({"text": transcript.text})
    except Exception as e:
        print("Transcription error (base64):", str(e))
        return jsonify({"error": "Failed to transcribe"}), 500


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
        return "<h2>No Aadhaar file uploaded. Please try again.</h2><a href='/aadhaar'>🡸 Try Again</a>"

    if not aadhaar_file.filename.lower().endswith('.pdf'):
        return "<h2>Only PDF format is currently supported.</h2><a href='/aadhaar'>🡸 Try Again</a>"

    filename = aadhaar_file.filename.replace(" ", "_")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    aadhaar_file.save(filepath)

    # OCR API call
    with open(filepath, 'rb') as f:
        ocr_result = requests.post(
            'https://api.ocr.space/parse/image',
            files={"filename": f},
            data={"apikey": OCR_API_KEY, "isOverlayRequired": False, "OCREngine": 2, "scale": True}
        )

    try:
        raw_text = ocr_result.json()['ParsedResults'][0]['ParsedText']
    except (KeyError, IndexError):
        return "<h2>OCR failed. Please try with a clearer Aadhaar PDF.</h2><a href='/aadhaar'>🡸 Try Again</a>"

    print("🔍 Raw OCR Text:\n", raw_text)
    cleaned_text = clean_ocr_text(raw_text)
    print("🧹 Cleaned OCR Text:\n", cleaned_text)

    # Aadhaar number (match 12-digit group or spaced format)
    aadhaar_match = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b', cleaned_text.replace("\n", " "))
    aadhaar_number = aadhaar_match.group() if aadhaar_match else "Aadhaar Not Detected"

    # DOB in formats: DD/MM/YYYY, YYYY, or 'Year of Birth: 2002'
    dob_match = (
        re.search(r'\d{2}[/-]\d{2}[/-]\d{4}', cleaned_text) or
        re.search(r'Year\s*of\s*Birth\s*[:\s]*((?:19|20)\d{2})', cleaned_text, re.IGNORECASE) or
        re.search(r'\b(19|20)\d{2}\b', cleaned_text)
    )
    try:
        dob = dob_match.group(1) if dob_match.lastindex else dob_match.group()
    except:
        dob = "DOB Not Detected"

    # Name extraction - look for lines that:
    # - have 2+ words
    # - no digits or symbols
    # - aren't keywords like 'aadhaar', 'govt', etc.
    name = "Name Not Detected"
    for line in cleaned_text.split("\n"):
        line = line.strip()
        if (
            len(line.split()) >= 2 and
            not any(x in line.lower() for x in ["aadhaar", "govt", "year", "dob", "issued", "male", "female", "of", "birth"]) and
            not re.search(r'[^a-zA-Z\s]', line)
        ):
            name = line.title()
            break

    print("✅ Extracted Name:", name)
    print("✅ Extracted DOB:", dob)
    print("✅ Extracted Aadhaar:", aadhaar_number)

    return redirect(url_for('report',
        name=name,
        dob=dob,
        aadhaar=aadhaar_number,
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
    symptoms = request.args.get("symptoms", "").lower()

    with open("symptom_keywords.txt", "r") as file:
        keywords = [line.strip().lower() for line in file if line.strip()]
    matches = sum(1 for word in keywords if word in symptoms)

    if matches < 1:
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
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        soap_note = response.choices[0].message.content.strip()
        print("🧠 AI SOAP Note:\n", soap_note)

    except Exception as e:
        print("AI fallback reason:", str(e))
        soap_note = generate_soap_strict(symptoms, name, dob, aadhaar)

    return render_template("report.html", name=name, dob=dob, aadhaar=aadhaar, soap=soap_note)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
