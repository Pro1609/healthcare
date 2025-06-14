from flask import Flask, render_template, request
from google.cloud import vision
import io, re

app = Flask(__name__)
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/var/render/secrets/service_account.json"


client = vision.ImageAnnotatorClient()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    aadhar_file = request.files['aadhar']
    symptom_text = request.form['symptom']
    
    # Read uploaded file content
    content = aadhar_file.read()

    # Send to Google Cloud Vision
    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if response.error.message:
        return f"❌ Error from Vision API: {response.error.message}"

    text = response.full_text_annotation.text
    text_lower = text.lower()

    # Aadhaar Validation
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
    app.run(host='0.0.0.0', port=port)
