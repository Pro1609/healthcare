window.onload = () => {
  const box = document.getElementById('aadhaar-box');

  box.addEventListener('mouseenter', () => {
    box.classList.add('hovered');
  });

  box.addEventListener('mouseleave', () => {
    box.classList.remove('hovered');
  });
};
