const phoneInput = document.getElementById("phone");
const otpInput = document.getElementById("otp");

function sendOTP() {
  const number = phoneInput.value;
  if (!number.startsWith("+")) {
    alert("Please enter phone number in international format, e.g. +917852910701");
    return;
  }

  fetch("/send-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ number })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert("OTP sent successfully!");
    } else {
      alert("Failed to send OTP: " + data.error);
    }
  });
}

function verifyOTP() {
  const number = phoneInput.value;
  const code = otpInput.value;

  fetch("/verify-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ number, code })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      localStorage.setItem("user", number);
      window.location.href = "/symptoms";
    } else {
      alert("OTP verification failed: " + data.error);
    }
  });
}

function continueAsGuest() {
  localStorage.setItem("user", "guest");
  window.location.href = "/symptoms";
}
