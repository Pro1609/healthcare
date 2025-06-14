from flask import Flask, render_template, request
import os
import re
import requests
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
OCR_API_KEY = 'K85073730188957'
OCR_API_URL = 'https://api.ocr.space/parse/image'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

    # Smart Name Extraction
    lines = text.split('\n')
    name_candidates = []
    for line in lines:
        cleaned = line.strip()
        if re.fullmatch(r'[A-Za-z\s]{5,}', cleaned) and len(cleaned.split()) >= 2:
            name_candidates.append(cleaned)

    dob_index = next((i for i, l in enumerate(lines) if re.search(r'DOB|MALE|FEMALE', l, re.IGNORECASE)), None)
    if dob_index is not None:
        for i in range(dob_index - 1, -1, -1):
            cleaned = lines[i].strip()
            if cleaned in name_candidates:
                aadhaar_data["Name"] = cleaned
                break
    elif name_candidates:
        aadhaar_data["Name"] = name_candidates[0]

    return aadhaar_data

def convert_pdf_to_jpg(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)
    jpg_paths = []
    for i, image in enumerate(images):
        jpg_path = os.path.splitext(pdf_path)[0] + f'_{i}.jpg'
        image.save(jpg_path, 'JPEG')
        jpg_paths.append(jpg_path)
    return jpg_paths

def perform_ocr(filepath):
    with open(filepath, 'rb') as f:
        payload = {
            'isOverlayRequired': False,
            'apikey': OCR_API_KEY,
            'language': 'eng'
        }
        files = {'file': f}
        response = requests.post(OCR_API_URL, files=files, data=payload)
        result = response.json()
        if result.get("ParsedResults"):
            return result["ParsedResults"][0]["ParsedText"]
        else:
            return "OCR Failed"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    file = request.files['file']
    if not file:
        return "No file uploaded."

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    if filename.lower().endswith('.pdf'):
        images = convert_pdf_to_jpg(filepath)
        text = ''
        for img in images:
            text += perform_ocr(img) + '\n'
    else:
        text = perform_ocr(filepath)

    extracted = extract_aadhaar_details(text)

    return render_template('result.html', extracted_text=text, extracted=extracted)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
