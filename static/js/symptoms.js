// symptoms.js — bilingual symptoms input + voice + translate
// Drop this file into /static/js/symptoms.js and include it near the end of your HTML.

document.addEventListener('DOMContentLoaded', () => {
  /* -------------------------
     Element references
     ------------------------- */
  const languageSelect = document.getElementById('languageSelect');
  const localWrapper = document.getElementById('local-input-wrapper');
  const symptomsTextarea = document.getElementById('symptoms');
  const symptomsLocalTextarea = document.getElementById('symptoms_local');
  const translateBtn = document.getElementById('translateLocalBtn');
  const translateStatus = document.getElementById('translateStatus');
  const transcriptionDisplay = document.getElementById('transcription-display');
  const transcriptionOriginal = document.getElementById('transcription-original-text');
  const transcriptionTranslated = document.getElementById('transcription-translated-text');
  const originalHidden = document.getElementById('original_text_hidden');
  const translatedHidden = document.getElementById('translated_text_hidden');

  const recordBtn = document.getElementById('recordBtn');
  const recordStatus = document.getElementById('recordStatus');

  const symptomsForm = document.getElementById('symptoms-form');

  const severitySlider = document.getElementById('severity');
  const severityValue = document.getElementById('severity-value');

  /* -------------------------
     Utility & state
     ------------------------- */
  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;
  // preserve local text when toggling languages
  let preservedLocalText = '';

  // Helper: set translate button state
  function updateTranslateButtonState() {
    const localHasText = symptomsLocalTextarea && symptomsLocalTextarea.value.trim().length > 0;
    if (translateBtn) {
      translateBtn.disabled = !localHasText;
      translateBtn.setAttribute('aria-disabled', (!localHasText).toString());
    }
  }

  // Helper: show/hide local wrapper depending on language
  function updateLocalWrapperVisibility() {
    const lang = languageSelect ? languageSelect.value : 'en-IN';
    if (lang.startsWith('en')) {
      // hide local input — preserve existing content
      if (localWrapper) {
        localWrapper.classList.add('hidden');
        localWrapper.setAttribute('aria-hidden', 'true');
      }
      // store current local content in memory
      if (symptomsLocalTextarea) preservedLocalText = symptomsLocalTextarea.value;
    } else {
      if (localWrapper) {
        localWrapper.classList.remove('hidden');
        localWrapper.setAttribute('aria-hidden', 'false');
      }
      // restore preserved text
      if (symptomsLocalTextarea && preservedLocalText) {
        symptomsLocalTextarea.value = preservedLocalText;
      }
    }
    updateTranslateButtonState();
  }

  // Helper: update transcription display visibility & texts
  function showTranscription(originalText, translatedText, langCode = null) {
    if (transcriptionOriginal) transcriptionOriginal.innerText = originalText || '';
    if (transcriptionTranslated) transcriptionTranslated.innerText = translatedText || '';
    if (transcriptionDisplay) transcriptionDisplay.style.display = 'block';
    // update hidden fields
    if (originalHidden) originalHidden.value = originalText || '';
    if (translatedHidden) translatedHidden.value = translatedText || '';
    // enable translate button if local textarea present
    updateTranslateButtonState();
    // set textareas based on current language selection
    if (languageSelect && languageSelect.value && !languageSelect.value.startsWith('en')) {
      // when non-English selected, fill the local textarea with original
      if (symptomsLocalTextarea) symptomsLocalTextarea.value = originalText || '';
    }
    // always fill the canonical English textarea with the translation (helpful fallback)
    if (symptomsTextarea) symptomsTextarea.value = translatedText || originalText || '';
  }

  // Convert Blob to base64 string (no mime prefix)
  function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const dataUrl = reader.result;
        const base64 = dataUrl.split(',')[1];
        resolve(base64);
      };
      reader.onerror = (err) => reject(err);
      reader.readAsDataURL(blob);
    });
  }

  /* -------------------------
     Severity slider UX (keep existing behavior)
     ------------------------- */
  if (severitySlider && severityValue) {
    function setSeverityVisual(val) {
      severityValue.textContent = val;
      severityValue.style.color = (val <= 3) ? '#28a745' : (val <= 6 ? '#ffc107' : '#dc3545');
      severitySlider.style.background = `linear-gradient(to right, #5f27cd 0%, #5f27cd ${val * 10}%, #3a3a3a ${val * 10}%, #3a3a3a 100%)`;
    }
    severitySlider.addEventListener('input', () => setSeverityVisual(severitySlider.value));
    setSeverityVisual(severitySlider.value);
  }

  /* -------------------------
     Language change handling
     ------------------------- */
  if (languageSelect) {
    languageSelect.addEventListener('change', () => {
      updateLocalWrapperVisibility();
      // update a small label for record button if you like
      if (recordStatus) {
        const langLabel = languageSelect.options[languageSelect.selectedIndex].text;
        recordStatus.textContent = `Ready to record (${langLabel})`;
      }
    });
    // init state
    updateLocalWrapperVisibility();
  }

  /* -------------------------
     Translate typed local text (calls /translate_text)
     ------------------------- */
  if (translateBtn) {
    translateBtn.addEventListener('click', async () => {
      const localText = symptomsLocalTextarea ? symptomsLocalTextarea.value.trim() : '';
      if (!localText) return;
      if (translateStatus) translateStatus.textContent = 'Translating...';
      translateBtn.disabled = true;

      // Prepare payload (from is the selected language, to is 'en')
      const payload = {
        text: localText,
        from: languageSelect ? languageSelect.value : null,
        to: 'en'
      };

      try {
        // Call the server-side translate endpoint
        const resp = await fetch('/translate_text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!resp.ok) {
          const txt = await resp.text().catch(() => '');
          if (translateStatus) translateStatus.textContent = `Translation failed (${resp.status}).`;
          console.warn('Translate endpoint returned error:', resp.status, txt);
        } else {
          const data = await resp.json();
          const translated = data.translated_text || data.translation || '';
          // populate canonical english textarea and hidden fields
          if (symptomsTextarea) symptomsTextarea.value = translated;
          if (translatedHidden) translatedHidden.value = translated;
          if (translateStatus) translateStatus.textContent = 'Translation complete.';
          // Also show the transcription pair UI for review
          showTranscription(localText, translated, payload.from);
        }
      } catch (err) {
        console.error('Error calling /translate_text:', err);
        if (translateStatus) translateStatus.textContent = 'Translation failed (network).';
      } finally {
        updateTranslateButtonState();
      }
    });
  }

  /* -------------------------
     Voice recording and transcription (uses /transcribe)
     ------------------------- */
  if (recordBtn) {
    recordBtn.addEventListener('click', async () => {
      if (!isRecording) {
        // start recording
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          mediaRecorder = new MediaRecorder(stream);
          audioChunks = [];

          mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

          mediaRecorder.onstop = async () => {
            // stop tracks
            try {
              stream.getTracks().forEach(t => t.stop());
            } catch (_) {}

            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            if (recordStatus) recordStatus.textContent = 'Processing...';

            try {
              const base64 = await blobToBase64(audioBlob);
              // call /transcribe with body { audio: base64, language: languageSelect.value }
              const body = { audio: base64, language: languageSelect ? languageSelect.value : 'en-IN' };
              const resp = await fetch('/transcribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
              });

              const data = await resp.json();
              if (!resp.ok) {
                throw new Error(data.error || `Transcription error (${resp.status})`);
              }

              // server returns { original_text, translated_text, language_code }
              const originalText = data.original_text || '';
              const translatedText = data.translated_text || originalText || '';
              // show in transcription UI and populate fields
              showTranscription(originalText, translatedText, data.language_code || body.language);
              if (recordStatus) recordStatus.textContent = 'Transcription complete!';
            } catch (err) {
              console.error('Transcription error:', err);
              if (recordStatus) recordStatus.textContent = 'Transcription failed. Try again.';
              // don't clear textareas
            }
          };

          mediaRecorder.start();
          isRecording = true;
          recordBtn.textContent = '🛑';
          if (recordStatus) recordStatus.textContent = 'Recording... Click to stop';
        } catch (err) {
          console.error('Microphone error:', err);
          if (recordStatus) recordStatus.textContent = 'Microphone access denied or unavailable';
        }
      } else {
        // stop recording
        try {
          mediaRecorder.stop();
        } catch (e) {
          console.warn('Error stopping mediaRecorder', e);
        } finally {
          isRecording = false;
          recordBtn.textContent = '🎙️';
        }
      }
    });
  }

  /* -------------------------
     Pre-submit: always submit English as canonical `symptoms`
     ------------------------- */
  if (symptomsForm) {
    symptomsForm.addEventListener('submit', (e) => {
      // Always submit English — pipeline requires English
      const englishText = symptomsTextarea ? symptomsTextarea.value.trim() : '';
      const localText = symptomsLocalTextarea ? symptomsLocalTextarea.value.trim() : '';

      // Basic validation: require some detail
      if (!englishText || englishText.length < 10) {
        e.preventDefault();
        alert('Please describe your symptoms with more detail before continuing.');
        return;
      }

      // Ensure canonical textarea holds the English text (this is what your server expects)
      if (symptomsTextarea) symptomsTextarea.value = englishText;

      // Update hidden fields so original/translated pair are preserved for logging/debugging
      if (originalHidden && symptomsLocalTextarea) originalHidden.value = localText;
      if (translatedHidden && symptomsTextarea) translatedHidden.value = englishText;

      // allow the form to submit normally
    });
  }

  /* -------------------------
     Misc: update translate button when local textarea changes
     ------------------------- */
  if (symptomsLocalTextarea) {
    symptomsLocalTextarea.addEventListener('input', () => updateTranslateButtonState());
  }

  // initialize button state
  updateTranslateButtonState();
});
