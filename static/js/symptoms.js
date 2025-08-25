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

  // 🎙️ Voice recording and transcription
  let mediaRecorder;
  let audioChunks = [];
  let isRecording = false;

  const recordBtn = document.getElementById('recordBtn');
  const recordStatus = document.getElementById('recordStatus');
  const languageSelect = document.getElementById('languageSelect');

  recordBtn.addEventListener('click', async function () {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = function (event) {
          audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async function () {
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          const audioBase64 = await blobToBase64(audioBlob);
          const selectedLanguage = languageSelect.value;

          recordStatus.textContent = 'Processing...';

          try {
            const response = await fetch('/transcribe', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                audio: audioBase64,
                language: selectedLanguage
              })
            });

            const data = await response.json();

            if (response.ok) {
              // Create dual-column display
              const displayContainer = document.getElementById('transcription-display');
              displayContainer.style.display = 'block';
              displayContainer.innerHTML = '';

              const originalCol = document.createElement('div');
              originalCol.className = 'transcription-original';
              originalCol.innerHTML = `<strong>Original (${data.language_code || selectedLanguage}):</strong><br>${data.original_text || 'No speech detected'}`;
              
              const translatedCol = document.createElement('div');
              translatedCol.className = 'transcription-translated';
              translatedCol.innerHTML = `<strong>English Translation:</strong><br>${data.translated_text || 'No translation available'}`;
              
              displayContainer.appendChild(originalCol);
              displayContainer.appendChild(translatedCol);

              // Update textarea with English translation
              textarea.value = data.translated_text || data.original_text || '';
              recordStatus.textContent = 'Transcription complete!';
            } else {
              throw new Error(data.error || 'Transcription failed');
            }
          } catch (error) {
            console.error('Transcription error:', error);
            recordStatus.textContent = 'Transcription failed. Try again.';
            document.getElementById('transcription-display').style.display = 'none';
          }
        };

        mediaRecorder.start();
        isRecording = true;
        recordBtn.textContent = '🛑';
        recordStatus.textContent = 'Recording... Click to stop';
      } catch (error) {
        console.error('Error accessing microphone:', error);
        recordStatus.textContent = 'Microphone access denied';
      }
    } else {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      isRecording = false;
      recordBtn.textContent = '🎙️';
      recordStatus.textContent = 'Processing...';
    }
  });
});

function blobToBase64(blob) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(',')[1]);
    reader.readAsDataURL(blob);
  });
}
