window.addEventListener("DOMContentLoaded", () => {
  const boxes = document.querySelectorAll(".soap-box");

  boxes.forEach((box, index) => {
    setTimeout(() => {
      box.classList.add("slide-in");
    }, index * 200); // stagger animation
  });
});
