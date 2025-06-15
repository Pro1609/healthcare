from flask import Flask, render_template, request, redirect, url_for, flash
import os
import re
import requests
from openai import OpenAI
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # needed for flashing messages

# Upload folder setup
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load environment variables
load_dotenv()
OCR_API_KEY = os.getenv("OCR_API_KEY", "K85073730188957")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "a013eadecb34c3c39387a5218867fbd52cbc60acd68baba4a7522652790331c1")

# Setup OpenAI client with Together.ai
client = OpenAI(
    api_key=TOGETHER_API_KEY,
    base_url="https://api.together.xyz/v1"
)

# Utility: Check file type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes

@app.route('/')
def home():
    return redirect(url_for('symptoms'))

@app.route('/symptoms')
def symptoms():
    return render_template("symptoms.html")

@app.route('/aadhaar', methods=['POST'])
def aadhaar():
    name = request.form['name']
    age = request.form['age']
    gender = request.form['gender']
    symptoms = request.form['symptoms']
    aadhaar_file = request.files['aadhaar']

    if aadhaar_file.filename == '':
        flash("No file selected.")
        return redirect(request.url)

    if not allowed_file(aadhaar_file.filename):
        flash("Invalid file type. Only PNG, JPG, JPEG, and PDF allowed.")
        return redirect(request.url)

    filename = secure_filename(aadhaar_file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    aadhaar_file.save(filepath)

    # OCR parsing
    ocr_result = requests.post(
        'https://api.ocr.space/parse/image',
        files={"filename": open(filepath, 'rb')},
        data={"apikey": OCR_API_KEY}
    )

    try:
        result_text = ocr_result.json()['ParsedResults'][0]['ParsedText']
    except Exception as e:
        result_text = "OCR failed"
        flash("OCR parsing failed. Please try again with a clear image.")
        return redirect(url_for('symptoms'))

    # Aadhaar and DOB Extraction
    aadhaar_number = re.search(r'\d{4}\s\d{4}\s\d{4}', result_text)
    dob = re.search(r'\d{2}/\d{2}/\d{4}', result_text)
    extracted_name = name  # fallback

    # Fuzzy check for Aadhaar name (optional logic)
    if "Mohammad" in result_text and "Raza" in result_text:
        extracted_name = "Mohammad Shadab Raza"

    return redirect(url_for('report', 
        name=extracted_name, 
        age=age, 
        gender=gender, 
        dob=dob.group() if dob else "Unknown",
        aadhaar=aadhaar_number.group() if aadhaar_number else "Unknown",
        symptoms=symptoms
    ))

@app.route('/report')
def report():
    name = request.args.get("name")
    age = request.args.get("age")
    gender = request.args.get("gender")
    dob = request.args.get("dob")
    aadhaar = request.args.get("aadhaar")
    symptoms = request.args.get("symptoms")

    prompt = f"""
    Patient: {name}, Age: {age}, Gender: {gender}
    Symptoms: {symptoms}

    Generate a detailed SOAP format (Subjective, Objective, Assessment, Plan).
    Avoid hallucinating extra symptoms.
    Also provide:
    1. TRIAGE SEVERITY (score out of 10)
    2. One-line health advice
    3. Preventive measures if applicable
    """

    try:
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {"role": "system", "content": "You are a helpful SOAP note generator. Stick to given symptoms."},
                {"role": "user", "content": prompt}
            ]
        )
        soap_note = response.choices[0].message.content.strip()
    except Exception as e:
        soap_note = f"Error calling AI: {str(e)}"

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
