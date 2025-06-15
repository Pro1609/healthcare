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
load_dotenv()  # Only needed if running locally, Render auto-loads

# ✅ Securely fetch API keys
OCR_API_KEY = os.getenv("OCR_API_KEY", "K85073730188957")  # fallback to default if not found
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Setup OpenAI client for version >=1.0.0
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/')
def home():
    return redirect(url_for('symptoms'))

# ✅ Continue with your other routes here...

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
    
    filename = aadhaar_file.filename.replace(" ", "_")  # remove spaces
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    aadhaar_file.save(filepath)

    # OCR call
    ocr_result = requests.post(
        'https://api.ocr.space/parse/image',
        files={"filename": open(filepath, 'rb')},
        data={"apikey": OCR_API_KEY}
    )

    try:
        result_text = ocr_result.json()['ParsedResults'][0]['ParsedText']
    except:
        result_text = "OCR failed"

    # Extract Aadhaar details
    aadhaar_number = re.search(r'\d{4}\s\d{4}\s\d{4}', result_text)
    dob = re.search(r'\d{2}/\d{2}/\d{4}', result_text)
    extracted_name = name  # fallback
    if "Mohammad" in result_text:
        extracted_name = "Mohammad Shadab Raza"  # mock case

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
    # Inputs from previous steps
    name = request.args.get("name")
    age = request.args.get("age")
    gender = request.args.get("gender")
    dob = request.args.get("dob")
    aadhaar = request.args.get("aadhaar")
    symptoms = request.args.get("symptoms")

    # AI Prompt
    prompt = f"""
    Patient: {name}, Age: {age}, Gender: {gender}
    Symptoms: {symptoms}

    Generate SOAP format (Subjective, Objective, Assessment, Plan).
    Also provide a TRIAGE SEVERITY score out of 10 and one-liner ADVICE.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful SOAP note generator."},
                {"role": "user", "content": f"Name: {name}, Age: {age}, Gender: {gender}, Symptoms: {symptoms}"}
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
