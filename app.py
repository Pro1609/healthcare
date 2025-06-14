from flask import Flask, render_template, request
import os
import requests
import re

app = Flask(__name__)

# Create upload folder if it doesn't exist
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Your OCR.space API key
OCR_API_KEY = 'K85073730188957'

# Aadhaar parsing function
def extract_aadhaar_details(text):
    aadhaar_data = {}

    # Aadhaar Number
    aadhaar_match = re.search(r'(\d{4}\s\d{4}\s\d{4}|\d{12})', text)
    if aadhaar_match:
        aadhaar_data["Aadhaar Number"] = aadhaar_match.group(1)

    # Date of Birth
    dob_match = re.search(r'(DOB|Year of Birth|YOB)[^\d]*(\d{2}/\d{2}/\d{4}|\d{4})', text, re.IGNORECASE)
    if dob_match:
        aadhaar_data["Date of Birth"] = dob_match.group(2)

    # Name (First line with only alphabets)
    lines = text.split('\n')
    for line in lines:
        if re.match(r'^[A-Za-z\s]{5,}$', line.strip()):
            aadhaar_data["Name"] = line.strip()
            break

    return aadhaar_data

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Handle submission
@app.route('/submit', methods=['POST'])
def submit():
    file = request.files['file']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    with open(filepath, 'rb') as f:
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'file': f},
            data={'apikey': OCR_API_KEY, 'language': 'eng'}
        )

    result = response.json()

    try:
        text = result['ParsedResults'][0]['ParsedText']
    except Exception as e:
        return f"<h2>Error during OCR: {e}</h2><pre>{result}</pre>"

    aadhaar_info = extract_aadhaar_details(text)

    return render_template('result.html', text=text, aadhaar=aadhaar_info)

# Start the app (only for local testing, NOT needed on Render)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
