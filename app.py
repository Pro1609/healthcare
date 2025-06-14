from flask import Flask, render_template, request
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import os
import re

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    aadhar_file = request.files['aadhar']
    symptom_text = request.form['symptom']

    file_path = "temp_upload"
    os.makedirs(file_path, exist_ok=True)
    file_ext = aadhar_file.filename.split('.')[-1].lower()
    saved_path = os.path.join(file_path, "aadhaar." + file_ext)
    aadhar_file.save(saved_path)

    text = ""
    try:
        if file_ext == 'pdf':
            images = convert_from_bytes(open(saved_path, 'rb').read())
            for img in images:
                text += pytesseract.image_to_string(img)
        elif file_ext in ['jpg', 'jpeg', 'png']:
            img = Image.open(saved_path)
            text = pytesseract.image_to_string(img)
        else:
            return "❌ Unsupported file format. Upload JPG, PNG, or PDF."
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"

    text_lower = text.lower()
    aadhaar_match = re.search(r"\d{4} \d{4} \d{4}", text)
    is_valid = "government of india" in text_lower and aadhaar_match

    if is_valid:
        aadhaar_number = aadhaar_match.group()
        gender = "Male" if "male" in text_lower else "Female" if "female" in text_lower else "Unknown"

        return f"""
        ✅ Aadhaar Verified<br><br>
        Aadhaar Number: {aadhaar_number}<br>
        Gender: {gender}<br>
        Symptoms: {symptom_text}<br><br>
        📢 Next Step: Proceeding to AI symptom analysis...
        """
    else:
        return "❌ This is not a valid Aadhaar card. Please upload a proper Aadhaar image or PDF."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
