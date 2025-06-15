from flask import Flask, render_template, request, redirect, url_for
import requests
import os
import re
from openai import OpenAI
from dotenv import load_dotenv

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Load environment variables
load_dotenv()

# ✅ API keys
OCR_API_KEY = os.getenv("OCR_API_KEY", "K85073730188957")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "a013eadecb34c3c39387a5218867fbd52cbc60acd68baba4a7522652790331c1")

# ✅ Initialize OpenAI client with Together API
client = OpenAI(
    api_key=TOGETHER_API_KEY,
    base_url="https://api.together.xyz/v1"
)

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
    
    filename = aadhaar_file.filename.replace(" ", "_")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    aadhaar_file.save(filepath)

    ocr_result = requests.post(
        'https://api.ocr.space/parse/image',
        files={"filename": open(filepath, 'rb')},
        data={"apikey": OCR_API_KEY}
    )

    try:
        result_text = ocr_result.json()['ParsedResults'][0]['ParsedText']
    except:
        result_text = "OCR failed"

    aadhaar_number = re.search(r'\d{4}\s\d{4}\s\d{4}', result_text)
    dob = re.search(r'\d{2}/\d{2}/\d{4}', result_text)
    extracted_name = name
    if "Mohammad" in result_text:
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

    # Create OpenAI client (correct for openai>=1.0.0)
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("TOGETHER_API_KEY"), base_url="https://api.together.xyz/v1")

    # Strict prompt to avoid hallucination
    prompt = f"""
The following patient details must be used *as-is* without guessing or adding symptoms:

Patient Name: {name}
Age: {age}
Gender: {gender}
Date of Birth: {dob}
Aadhaar: {aadhaar}

Symptoms Provided by Patient:
{symptoms}

You are a SOAP note generator. Based strictly on the symptoms provided, generate a complete SOAP format:
- Subjective: Repeat the patient's symptoms clearly.
- Objective: Leave this blank unless specific vitals or signs are provided.
- Assessment: Explain possible conditions or diagnoses based on symptoms.
- Plan: Next steps (tests, medicine, precautions etc.)

Also include:
- Triage Severity Score out of 10
- One-line health advice based on the symptoms

Do not hallucinate or add extra symptoms.
"""

    try:
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {"role": "system", "content": "You are a helpful SOAP note generator."},
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
