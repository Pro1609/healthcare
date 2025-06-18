window.onload = function () {
  const uploadBox = document.querySelectorAll('.upload-box');

  uploadBox.forEach(box => {
    box.addEventListener('mouseenter', () => {
      box.classList.add('hovered');
    });

    box.addEventListener('mouseleave', () => {
      box.classList.remove('hovered');
    });
  });
};
