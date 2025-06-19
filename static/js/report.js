// report.js
window.onload = function () {
  const boxes = document.querySelectorAll('.report-box');

  boxes.forEach((box, index) => {
    setTimeout(() => {
      box.classList.add('slide-in');
    }, index * 300); // staggered delay for each box
  });
};
