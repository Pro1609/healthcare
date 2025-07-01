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
import subprocess
import uuid
import time
import math
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

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
AZURE_SPEECH_ENDPOINT = os.getenv("AZURE_SPEECH_ENDPOINT")

AZURE_TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
AZURE_TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION")
AZURE_TRANSLATOR_ENDPOINT = os.getenv("AZURE_TRANSLATOR_ENDPOINT")

AZURE_VISION_KEY = os.getenv("AZURE_VISION_KEY")
AZURE_VISION_ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT")

AZURE_MAPS_KEY = os.getenv("AZURE_MAPS_KEY")


# Load AssemblyAI API key from .env
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

# AI Client
client = Together()

# Twilio Client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Aadhaar filter
with open("aadhaar_filter_keywords.txt", "r") as f:
    unwanted = [line.strip().lower() for line in f]
def image_to_bytes(img):
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()
def clean_ocr_text(text):
    lines = text.split("\n")
    return "\n".join(line for line in lines if all(word not in line.lower() for word in unwanted))

# Dummy hospital list (fake data)
hospitals_data = [
    {"name": "Sundarpur Health Center", "lat": 20.294, "lon": 85.825, "address": "Sundarpur, Bhubaneswar"},
    {"name": "CarePlus Clinic", "lat": 20.299, "lon": 85.820, "address": "Acharya Vihar, Bhubaneswar"},
    {"name": "Sunshine Hospital", "lat": 20.305, "lon": 85.835, "address": "Sahid Nagar, Bhubaneswar"},
    {"name": "Janata Medical", "lat": 20.280, "lon": 85.830, "address": "Baramunda, Bhubaneswar"},
    {"name": "Lifeline Diagnostics", "lat": 20.275, "lon": 85.815, "address": "Khandagiri, Bhubaneswar"}
]

# Distance formula (Haversine)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))), 2)



@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/login')
def login():
    return render_template("login.html")

# ✅ Transcribe audio from base64 and auto-translate to English
@app.route('/transcribe', methods=['POST'])
def transcribe_audio_base64():
    try:
        data = request.get_json(force=True)
        print("📥 Raw incoming JSON:", data)

        audio_base64 = data.get("audio")
        language_code = data.get("language", "en-IN")

        if not audio_base64:
            print("❗ No audio data found in request.")
            return jsonify({"error": "No audio data provided"}), 400

        # Step 1: Decode & save raw audio (input)
        audio_bytes = base64.b64decode(audio_base64)
        raw_audio_path = f"static/uploads/raw_{uuid.uuid4().hex}.webm"
        with open(raw_audio_path, "wb") as f:
            f.write(audio_bytes)
        print(f"💾 Raw audio saved at {raw_audio_path}")

        # Step 2: Convert to WAV using ffmpeg
        wav_audio_path = raw_audio_path.replace(".webm", ".wav")
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", raw_audio_path, "-ac", "1", "-ar", "16000", wav_audio_path]
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"🎧 Converted WAV saved at {wav_audio_path}")

        # Step 3: Azure STT
        stt_url = f"https://{AZURE_SPEECH_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        headers = {
            "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
            "Content-Type": "audio/wav",
            "Accept": "application/json"
        }
        params = {
            "language": language_code
        }

        with open(wav_audio_path, 'rb') as audio_file:
            stt_response = requests.post(stt_url, headers=headers, params=params, data=audio_file)

        print("🔁 Azure STT Status:", stt_response.status_code)
        print("🔊 Azure STT Raw Response:", stt_response.text)

        stt_data = stt_response.json()
        original_text = stt_data.get("DisplayText", "")
        if not original_text:
            return jsonify({"error": "Speech recognition returned empty text"}), 500

        print("🗣️ Transcribed:", original_text)

        # Step 4: Translate if needed
        if language_code.startswith("en"):
            translated_text = original_text
        else:
            trans_url = f"{AZURE_TRANSLATOR_ENDPOINT}/translate?api-version=3.0&to=en"
            trans_headers = {
                "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
                "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
                "Content-Type": "application/json"
            }
            trans_body = [{"Text": original_text}]
            trans_response = requests.post(trans_url, headers=trans_headers, json=trans_body)

            print("🌍 Translator Status:", trans_response.status_code)
            print("🌍 Translator Raw Response:", trans_response.text)

            trans_data = trans_response.json()
            translated_text = trans_data[0]["translations"][0]["text"]

        print("🌐 Final Output:", translated_text)

        return jsonify({
            "original_text": original_text,
            "translated_text": translated_text
        })

    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg conversion failed:", e)
        return jsonify({"error": "Audio conversion failed"}), 500

    except Exception as e:
        print("❌ Error in transcription/translation:", str(e))
        return jsonify({"error": str(e)}), 500


# Symptoms route (no change)
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

from flask import request, render_template, redirect, url_for, session
import os, re, time, requests
from pdf2image import convert_from_bytes
from PIL import Image

# Aadhaar filter

@app.route('/aadhaar', methods=['GET', 'POST'])
def aadhaar():
    if request.method == 'GET':
        return render_template("aadhaar.html")

    aadhaar_file = request.files.get('aadhaar')
    if not aadhaar_file or aadhaar_file.filename == '':
        return "<h2>No file uploaded.</h2><a href='/aadhaar'>🡸 Try Again</a>"

    ext = aadhaar_file.filename.lower().split('.')[-1]
    filename = aadhaar_file.filename.replace(" ", "_")
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        aadhaar_file.save(filepath)
        print(f"💾 File saved to {filepath}")
    except Exception as e:
        print("❌ Save error:", str(e))
        return "<h2>Upload failed. Try again.</h2><a href='/aadhaar'>🡸 Try Again</a>"

    # 🔍 Azure OCR Setup
    ocr_url = f"{AZURE_VISION_ENDPOINT}/vision/v3.2/read/analyze"
    headers = {"Ocp-Apim-Subscription-Key": AZURE_VISION_KEY}

    if ext == 'pdf':
        headers["Content-Type"] = "application/pdf"
    elif ext in ['jpg', 'jpeg', 'png']:
        headers["Content-Type"] = "application/octet-stream"
    else:
        return "<h2>Unsupported file type. Only PDF or image allowed.</h2><a href='/aadhaar'>🡸 Try Again</a>"

    try:
        with open(filepath, 'rb') as f:
            response = requests.post(ocr_url, headers=headers, data=f)

        if response.status_code != 202:
            print("❌ OCR API failure:", response.text)
            raw_text = ""
        else:
            operation_url = response.headers['Operation-Location']
            for _ in range(10):
                result = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": AZURE_VISION_KEY}).json()
                if result.get("status") == "succeeded":
                    raw_text = "\n".join(
                        line["text"]
                        for page in result["analyzeResult"]["readResults"]
                        for line in page["lines"]
                    )
                    break
                time.sleep(2)
            else:
                raw_text = ""
    except Exception as e:
        print("❌ OCR Error:", str(e))
        raw_text = ""

    # 🧹 Clean and Extract
    cleaned_text = clean_ocr_text(raw_text) if raw_text else ""
    print("🧹 Cleaned OCR Text:\n", cleaned_text)

    # === Fallback defaults ===
    aadhaar_number = "Not provided"
    dob = "Not provided"
    name = "Not provided"

    # 🔎 Try extracting Aadhaar number
    try:
        match = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b', cleaned_text.replace("\n", " "))
        if match:
            aadhaar_number = match.group()
    except: pass

    # 🔎 Try extracting DOB
    try:
        dob_match = (
            re.search(r'\d{2}[/-]\d{2}[/-]\d{4}', cleaned_text) or
            re.search(r'Year\s*of\s*Birth\s*[:\s]*((?:19|20)\d{2})', cleaned_text, re.IGNORECASE) or
            re.search(r'\b(19|20)\d{2}\b', cleaned_text)
        )
        if dob_match:
            dob = dob_match.group(1) if dob_match.lastindex else dob_match.group()
    except: pass

    # 🔎 Try extracting Name
    try:
        for line in cleaned_text.split("\n"):
            line = line.strip()
            if (
                len(line.split()) >= 2 and
                not any(word in line.lower() for word in ["aadhaar", "govt", "dob", "year", "issued", "male", "female"]) and
                not re.search(r'[^a-zA-Z\s]', line)
            ):
                name = line.title()
                break
    except: pass

    print("✅ Name:", name)
    print("✅ DOB:", dob)
    print("✅ Aadhaar:", aadhaar_number)

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

@app.route('/consultchoice', methods=['GET', 'POST'])
def consult_choice():
    if request.method == 'POST':
        choice = request.form.get('choice')
        if choice == 'yes':
            return redirect(url_for('consult'))  # You'll define this later
        else:
            return redirect(url_for('thankyou'))
    return render_template("consultchoice.html")

@app.route('/consult', methods=['GET', 'POST'])
def consult():
    if request.method == 'GET':
        return render_template("consult.html", azure_maps_key=os.getenv("AZURE_MAPS_KEY"))

    try:
        data = request.get_json()
        lat, lon = data.get("lat"), data.get("lon")
        if not lat or not lon:
            raise ValueError("Missing lat/lon")

        # Azure Maps POI Search API
        search_url = "https://atlas.microsoft.com/search/poi/category/json"
        params = {
            "api-version": "1.0",
            "subscription-key": os.getenv("AZURE_MAPS_KEY"),
            "query": "hospital",
            "lat": lat,
            "lon": lon,
            "radius": 10000,
            "limit": 25  # Fetch more to allow fallback
        }

        response = requests.get(search_url, params=params)
        if response.status_code != 200:
            print("❌ Azure API error:", response.text)
            return jsonify({"results": []})

        all_hospitals = response.json().get("results", [])

        # Load top hospital keywords
        top_keywords = []
        with open("hospitals.txt", "r", encoding="utf-8") as file:
            top_keywords = [line.strip().lower() for line in file if line.strip()]

        # Step 1: Renowned hospitals
        renowned = []
        fallback = []

        for hosp in all_hospitals:
            name = hosp.get("poi", {}).get("name", "").lower()
            if any(keyword in name for keyword in top_keywords):
                renowned.append(hosp)
            else:
                fallback.append(hosp)

        # Step 2: Combine results up to 9 max (renowned first, then fallback)
        final_results = renowned + [h for h in fallback if h not in renowned]
        final_results = final_results[:9]

        return jsonify({"results": final_results})

    except Exception as e:
        print("❌ Consult route error:", str(e))
        return jsonify({"results": []})

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
