from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    aadhar_file = request.files['aadhar']
    symptom_text = request.form['symptom']
    
    # For now, just confirm receipt
    return f"Aadhaar file received: {aadhar_file.filename}<br>Symptoms: {symptom_text}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
