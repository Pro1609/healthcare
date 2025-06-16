// Smooth fade-in for all sections
document.addEventListener("DOMContentLoaded", () => {
  const features = document.querySelector(".features");
  features.style.opacity = 0;
  features.style.transform = "translateY(50px)";
  setTimeout(() => {
    features.style.transition = "all 0.8s ease";
    features.style.opacity = 1;
    features.style.transform = "translateY(0)";
  }, 200);
});
