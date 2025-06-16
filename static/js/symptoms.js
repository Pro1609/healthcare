document.addEventListener("DOMContentLoaded", () => {
  const severitySlider = document.getElementById("severity");
  const severityValue = document.getElementById("severity-value");
  const symptomsForm = document.getElementById("symptoms-form");
  const symptomsInput = document.getElementById("symptoms");

  // Initialize value display
  severityValue.textContent = severitySlider.value;

  // Update slider value dynamically
  severitySlider.addEventListener("input", () => {
    severityValue.textContent = severitySlider.value;
  });

  // Enhance input with soft UI
  symptomsInput.addEventListener("focus", () => {
    symptomsInput.style.boxShadow = "0 0 8px rgba(95, 39, 205, 0.7)";
  });
  symptomsInput.addEventListener("blur", () => {
    symptomsInput.style.boxShadow = "none";
  });

  // Smooth scroll on submission
  symptomsForm.addEventListener("submit", (e) => {
    e.preventDefault();
    symptomsInput.style.borderColor = "#5f27cd";
    symptomsInput.style.transition = "border-color 0.5s ease";
    setTimeout(() => {
      symptomsForm.submit();
    }, 300);
  });

  // Add smooth entrance effect
  const formContainer = document.querySelector(".form-container");
  formContainer.style.opacity = 0;
  formContainer.style.transform = "translateY(20px)";
  setTimeout(() => {
    formContainer.style.transition = "all 0.8s ease";
    formContainer.style.opacity = 1;
    formContainer.style.transform = "translateY(0)";
  }, 100);

  // Add slider style interaction
  severitySlider.addEventListener("mousedown", () => {
    severitySlider.style.cursor = "grabbing";
  });
  severitySlider.addEventListener("mouseup", () => {
    severitySlider.style.cursor = "grab";
  });
});
