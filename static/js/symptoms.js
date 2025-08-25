document.addEventListener('DOMContentLoaded', function () {
  const severitySlider = document.getElementById('severity');
  const severityValue = document.getElementById('severity-value');
  const symptomsForm = document.getElementById('symptoms-form') || document.querySelector('form');
  const textarea = document.getElementById('symptoms');

  // Update severity value on slider move
  severitySlider.addEventListener('input', function () {
    severityValue.textContent = severitySlider.value;
    severityValue.style.color = getSeverityColor(severitySlider.value);
    this.style.background = `linear-gradient(to right, #5f27cd 0%, #5f27cd ${this.value * 10}%, #3a3a3a ${this.value * 10}%, #3a3a3a 100%)`;
  });

  // Textarea focus effect
  textarea.addEventListener('focus', function () {
    this.style.boxShadow = '0 0 8px rgba(95, 39, 205, 0.8)';
    this.style.transition = 'box-shadow 0.3s ease-in-out';
  });

  textarea.addEventListener('blur', function () {
    this.style.boxShadow = 'none';
  });

  // Validate form on submit
  symptomsForm.addEventListener('submit', function (e) {
    const symptomText = textarea.value.trim();
    if (symptomText.length < 10) {
      alert("Please describe your symptoms with more detail.");
      textarea.focus();
      e.preventDefault();
    } else {
      console.log("Form submitted with severity:", severitySlider.value);
    }
  });

  function getSeverityColor(val) {
    const score = parseInt(val);
    if (score <= 3) return '#28a745';
    if (score <= 6) return '#ffc107';
    return '#dc3545';
  }

  severitySlider.dispatchEvent(new Event('input'));
});

// 🎙️ Voice recording and transcription
let mediaRecorder;
let audioChunks = [];

const recordBtn = document.getElementById('recordBtn');
const recordStatus = document.getElementById('recordStatus');
const symptomsInput = document.getElementById('symptoms');
const languageSelect = document.getElementById('languageSelect');

recordBtn.addEventListener('click', async () => {
  try {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);

      audioChunks = [];
      mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

      mediaRecorder.onstop = async () => {
        const blob = new Blob(audioChunks, { type: 'audio/wav' });
        const base64 = await blobToBase64(blob);

        recordStatus.textContent = "Transcribing & Translating...";

        try {
          const response = await fetch('/transcribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              audio: base64,
              language: languageSelect.value
            })
          });

          const data = await response.json();
          if (data.translated_text) {
            symptomsInput.value = data.translated_text;
            recordStatus.textContent = "✔️ Transcribed & Translated!";
          } else if (data.original_text) {
            symptomsInput.value = data.original_text;
            recordStatus.textContent = "⚠️ Translation failed. Showing raw transcription.";
          } else {
            recordStatus.textContent = "❌ Transcription failed";
          }
        } catch (apiError) {
          console.error("API error:", apiError);
          recordStatus.textContent = "❌ API Error. Please try again.";
        }
      };

      mediaRecorder.start();
      recordStatus.textContent = "🎙️ Recording...";
      recordBtn.textContent = "⏹️";

      setTimeout(() => {
        mediaRecorder.stop();
        recordBtn.textContent = "🎙️";
      }, 7000);
    }
  } catch (err) {
    console.error("Microphone access denied:", err);
    recordStatus.textContent = "🚫 Microphone access denied. Please enable permissions in browser settings.";
  }
});

function blobToBase64(blob) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(',')[1]);
    reader.readAsDataURL(blob);
  });
}

// In your symptoms.js file, update the transcription success handler:
fetch('/transcribe', {
    method: 'POST',
    body: JSON.stringify({
        audio: audioBase64,
        language: selectedLanguage
    })
})
.then(response => response.json())
.then(data => {
    // Create a dual-column display
    const originalCol = document.createElement('div');
    originalCol.className = 'transcription-original';
    originalCol.innerHTML = `<strong>Original (${data.language_code}):</strong><br>${data.original_text}`;
    
    const translatedCol = document.createElement('div');
    translatedCol.className = 'transcription-translated';
    translatedCol.innerHTML = `<strong>English Translation:</strong><br>${data.translated_text}`;
    
    // Update your textarea with English (for processing)
    document.querySelector('textarea[name="symptoms"]').value = data.translated_text;
    
    // Display both versions in a container
    const displayContainer = document.getElementById('transcription-display');
    displayContainer.innerHTML = '';
    displayContainer.appendChild(originalCol);
    displayContainer.appendChild(translatedCol);
});
