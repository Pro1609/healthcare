import re
from flask import Flask, render_template, request, redirect, url_for
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

OCR_API_KEY = os.getenv("OCR_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

@app.route('/')
def home():
    return redirect(url_for('symptoms'))

@app.route('/symptoms')
def symptoms():
    return render_template("symptoms.html")

@app.route('/aadhaar', methods=['POST'])
def aadhaar():
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
        print("OCR Extracted Text:\n", result_text)  # 🔍 Console Debugging

        aadhaar_number = re.search(r'\d{4}\s\d{4}\s\d{4}', result_text)
        dob = re.search(r'\d{2}[/-]\d{2}[/-]\d{4}', result_text)
        name_match = re.search(r'[A-Z][a-z]+(?:\s[A-Z][a-z]+)+', result_text)

        if not (aadhaar_number and dob and name_match):
            return f"""
            <h2>Invalid Aadhaar Card. Please upload a valid and clear Aadhaar image.</h2>
            <a href='/symptoms'>🡸 Try Again</a>
            """

        extracted_name = name_match.group()
        extracted_dob = dob.group().replace("-", "/")
        extracted_aadhaar = aadhaar_number.group()

        return redirect(url_for('report',
            name=extracted_name,
            dob=extracted_dob,
            aadhaar=extracted_aadhaar,
            symptoms=symptoms
        ))

    except Exception as e:
        print("OCR error:", str(e))
        return "OCR failed. Try again."

@app.route('/report')
def report():
    name = request.args.get("name")
    dob = request.args.get("dob")
    aadhaar = request.args.get("aadhaar")
    symptoms = request.args.get("symptoms")

    client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1")

    prompt = f"""
The following patient details must be used *as-is* without guessing or adding symptoms:

Patient Name: {name}
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
