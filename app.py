from flask import Flask, render_template, request, redirect, url_for
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Setup upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

OCR_SPACE_API_KEY = 'K85073730188957'  # Replace with your real API key
OCR_URL = 'https://api.ocr.space/parse/image'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # OCR.Space API call
    with open(filepath, 'rb') as f:
        payload = {
            'apikey': OCR_SPACE_API_KEY,
            'isOverlayRequired': False,
            'language': 'eng',
        }
        files = {'file': f}
        response = requests.post(OCR_URL, files=files, data=payload)

    try:
        result = response.json()
        parsed_text = result['ParsedResults'][0]['ParsedText']
    except Exception as e:
        return f"OCR failed: {str(e)}", 500

    return render_template('result.html', text=parsed_text, image_path=filepath)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
