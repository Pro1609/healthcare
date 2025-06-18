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

  // Helper to determine color by severity
  function getSeverityColor(val) {
    const score = parseInt(val);
    if (score <= 3) return '#28a745';
    if (score <= 6) return '#ffc107';
    return '#dc3545';
  }

  // Initialize slider background
  severitySlider.dispatchEvent(new Event('input'));
});
