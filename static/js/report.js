// report.js
window.addEventListener('DOMContentLoaded', () => {
  const sections = document.querySelectorAll('.soap-section');
  sections.forEach((section, i) => {
    section.style.animationDelay = `${0.2 + i * 0.2}s`;
  });
});
