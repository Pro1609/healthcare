import re
from flask import Flask, render_template, request, redirect, url_for
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Aadhaar cleaning filter load
with open("aadhaar_filter_keywords.txt", "r") as f:
    unwanted = [line.strip().lower() for line in f]

def clean_ocr_text(text):
    lines = text.split("\n")
    return "\n".join(line for line in lines if all(word not in line.lower() for word in unwanted))


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
    try:
        symptoms = request.form['symptoms']
        aadhaar_file = request.files['aadhaar']

        if not aadhaar_file:
            return "<h2>No file uploaded. Please try again.</h2><a href='/symptoms'>🡸 Try Again</a>"

        # Save the uploaded file
        filename = aadhaar_file.filename.replace(" ", "_")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        aadhaar_file.save(filepath)

        # Perform OCR
        with open(filepath, 'rb') as f:
            ocr_result = requests.post(
                'https://api.ocr.space/parse/image',
                files={"filename": f},
                data={"apikey": OCR_API_KEY}
            )

        raw_text = ocr_result.json()['ParsedResults'][0]['ParsedText']
        print("🔍 Raw OCR Text:\n", raw_text)

        # Clean text (remove noise)
        cleaned_text = clean_ocr_text(raw_text)
        print("🧹 Cleaned OCR Text:\n", cleaned_text)

        # Extract Aadhaar number
        aadhaar_match = re.search(r'\d{4}\s\d{4}\s\d{4}', cleaned_text)

        # Extract DOB (full or year)
        dob_match = re.search(r'\d{2}[/-]\d{2}[/-]\d{4}', cleaned_text)
        if not dob_match:
            dob_match = re.search(r'\b(19|20)\d{2}\b', cleaned_text)  # fallback to year only

        # Extract name (fallback for all caps too)
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

        # Clean extracted values
        extracted_name = name_match.group(1) if name_match.lastindex else name_match.group()
        extracted_dob = dob_match.group().replace("-", "/")
        extracted_aadhaar = aadhaar_match.group()

        print("✅ Extracted Name:", extracted_name)
        print("✅ Extracted DOB:", extracted_dob)
        print("✅ Extracted Aadhaar:", extracted_aadhaar)

        # Redirect to report
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

@app.route('/report')
def report():
    name = request.args.get("name")
    dob = request.args.get("dob")
    aadhaar = request.args.get("aadhaar")
    symptoms = request.args.get("symptoms").lower()

    # Load medical keywords from the .txt file
    with open("symptom_keywords.txt", "r") as file:
        keywords = [line.strip().lower() for line in file if line.strip()]

    # Count how many keywords are present in the symptom string
    matches = sum(1 for word in keywords if word in symptoms)

    if matches < 2:
        return f"""
        <h2>Invalid Symptom Description</h2>
        <p>Your input doesn't seem to describe enough medical symptoms.</p>
        <p>Please try again with more specific symptoms (e.g., 'fever and headache after eating').</p>
        <br><br>
        <a href='/symptoms'>🡸 Back to Start</a>
        """

    # Proceed with AI generation
    client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1")

    prompt = f"""
    The following patient details must be used as-is without adding new symptoms:

    Patient Name: {name}
    Date of Birth: {dob}
    Aadhaar: {aadhaar}

    Symptoms Provided by Patient:
    {symptoms}

    You are a SOAP note generator. Based strictly on the symptoms provided, generate a complete SOAP format:

    - Subjective: Summarize the patient's symptoms clearly.
    - Objective: Leave this blank unless vitals or physical signs are provided.
    - Assessment: Discuss possible causes or medical conditions related to the symptoms.
    - Plan: Suggest next steps (tests, medicines, referrals, lifestyle changes, etc.)

    Additionally, provide:
    - Triage Severity Score out of 10
    - One-line health advice based on the symptoms

    Only assess based on the given symptoms. Do not invent new symptoms.
    """

    try:
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {"role": "system", "content": "You are a helpful SOAP note generator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024
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
