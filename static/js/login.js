// login.js
document.querySelector('form').addEventListener('submit', function (e) {
  e.preventDefault();
  const phone = document.querySelector('#phone').value;
  if (!/^[6-9]\\d{9}$/.test(phone)) {
    alert('Please enter a valid 10-digit mobile number.');
    return;
  }
  alert('OTP sent (dummy). Redirecting...');
  // Simulate redirect (replace with actual OTP handling)
  window.location.href = '/symptoms';
});
