function formatPhoneNumber(raw) {
  let cleaned = raw.trim().replace(/[^0-9]/g, '');
  if (cleaned.length === 10) {
    return "+91" + cleaned;
  } else if (cleaned.length === 12 && cleaned.startsWith("91")) {
    return "+" + cleaned;
  } else if (cleaned.length === 13 && cleaned.startsWith("+91")) {
    return cleaned;
  } else {
    return null;
  }
}

function sendOTP() {
  const phoneInput = document.getElementById("phone").value;
  const formatted = formatPhoneNumber(phoneInput);

  if (!formatted) {
    alert("Please enter a valid Indian mobile number.");
    return;
  }

  fetch('/send-otp', {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone: formatted })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert("OTP sent successfully!");
    } else {
      alert("Failed to send OTP: " + data.error);
    }
  })
  .catch(err => {
    console.error("Error:", err);
    alert("Error sending OTP. Try again.");
  });
}

function verifyOTP() {
  const otp = document.getElementById("otp").value;
  const phoneInput = document.getElementById("phone").value;
  const formatted = formatPhoneNumber(phoneInput);

  if (!formatted || otp.trim().length < 4) {
    alert("Enter valid phone number and OTP.");
    return;
  }

  fetch('/verify-otp', {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone: formatted, otp })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      localStorage.setItem("user", formatted);
      window.location.href = "/symptoms";
    } else {
      alert("OTP verification failed.");
    }
  })
  .catch(err => {
    console.error(err);
    alert("An error occurred.");
  });
}

function continueAsGuest() {
  localStorage.setItem("user", "guest");
  window.location.href = "/symptoms";
}
