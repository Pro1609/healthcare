from flask import Flask, render_template, request, redirect
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Replace this with your API key
OCR_SPACE_API_KEY = 'K85073730188957'

def ocr_space_file(filename, overlay=False, language='eng'):
    """ OCR.space API request with local file """
    payload = {
        'isOverlayRequired': overlay,
        'apikey': OCR_SPACE_API_KEY,
        'language': language,
    }
    with open(filename, 'rb') as f:
        r = requests.post(
            'https://api.ocr.space/parse/image',
            files={ 'filename': f },
            data=payload,
        )
    result = r.json()
    return result['ParsedResults'][0]['ParsedText']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            extracted_text = ocr_space_file(filepath)
            return render_template('result.html', text=extracted_text)
        except Exception as e:
            return f"Error occurred during OCR: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
