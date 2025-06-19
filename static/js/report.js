window.onload = function () {
  const boxes = document.querySelectorAll('.report-box');

  boxes.forEach((box, index) => {
    setTimeout(() => {
      box.classList.add('slide-in');
    }, index * 200); // slight delay for staggered animation
  });
};
