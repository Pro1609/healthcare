document.addEventListener("DOMContentLoaded", () => {
  const box = document.querySelector(".choice-box");
  const buttons = document.querySelectorAll("button");

  // Fade-in animation on box load
  box.style.opacity = 0;
  box.style.transform = "scale(0.95)";
  setTimeout(() => {
    box.style.transition = "all 0.5s ease";
    box.style.opacity = 1;
    box.style.transform = "scale(1)";
  }, 100);

  // Ripple click effect
  buttons.forEach(btn => {
    btn.classList.add("btn-glow");

    btn.addEventListener("click", function (e) {
      const circle = document.createElement("span");
      circle.classList.add("ripple");
      this.appendChild(circle);

      const d = Math.max(this.clientWidth, this.clientHeight);
      circle.style.width = circle.style.height = `${d}px`;
      const rect = this.getBoundingClientRect();
      circle.style.left = `${e.clientX - rect.left - d / 2}px`;
      circle.style.top = `${e.clientY - rect.top - d / 2}px`;

      setTimeout(() => circle.remove(), 600);
    });

    // Glow feedback when selected
    btn.addEventListener("mousedown", () => {
      btn.style.boxShadow = "0 0 20px #9f6dfb";
    });
    btn.addEventListener("mouseup", () => {
      btn.style.boxShadow = "";
    });
  });
});
