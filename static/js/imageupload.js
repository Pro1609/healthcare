console.log("🖼️ Image/Video upload page loaded.");

document.querySelectorAll('input[type="file"]').forEach(input => {
  input.addEventListener('change', () => {
    if (input.files.length > 0) {
      console.log(`📁 File selected: ${input.files[0].name}`);
    }
  });
});
