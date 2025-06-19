window.onload = function () {
  const uploadBoxes = document.querySelectorAll('.upload-box');
  const fileInputs = document.querySelectorAll('input[type="file"]');

  uploadBoxes.forEach(box => {
    box.addEventListener('mouseenter', () => box.classList.add('hovered'));
    box.addEventListener('mouseleave', () => box.classList.remove('hovered'));
  });

  fileInputs.forEach(input => {
    input.addEventListener('change', function () {
      if (this.files.length > 0) {
        const parentBox = this.closest('.upload-box');
        parentBox.classList.add('selected');

        // Remove animation class after it completes
        setTimeout(() => {
          parentBox.classList.remove('selected');
        }, 400);
      }
    });
  });
};
