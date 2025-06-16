// ✅ Twilio-compatible phone format
function formatPhoneNumber(phone) {
  phone = phone.trim().replace(/\s|-/g, '');

  if (phone.startsWith('+')) return phone;
  if (/^\d{10}$/.test(phone)) return `+91${phone}`;
  return ''; // Invalid number
}

function sendOTP() {
  const rawPhone = document.getElementById("phone").value;
  const phone = formatPhoneNumber(rawPhone);

  if (!phone) {
    alert("⚠️ Please enter a valid Indian phone number (10 digits or with +91).");
    return;
  }

  fetch("/send-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("✅ OTP sent successfully!");
        localStorage.setItem("user", phone);  // Store phone number for session
      } else {
        alert("❌ Failed to send OTP: " + (data.error || "Unknown error"));
      }
    })
    .catch(error => {
      console.error("OTP send error:", error);
      alert("⚠️ An error occurred while sending OTP.");
    });
}

function verifyOTP() {
  const phone = formatPhoneNumber(document.getElementById("phone").value);
  const code = document.getElementById("otp").value.trim();

  if (!phone || !code) {
    alert("⚠️ Please fill in both phone and OTP fields.");
    return;
  }

  fetch("/verify-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, otp: code })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("✅ OTP Verified!");
        localStorage.setItem("user", phone);
        window.location.href = "/symptoms";
      } else {
        alert("❌ Invalid OTP. Please try again.");
      }
    })
    .catch(error => {
      console.error("OTP verification error:", error);
      alert("⚠️ Error verifying OTP. Try again.");
    });
}

function continueAsGuest() {
  localStorage.setItem("user", "guest");
  window.location.href = "/symptoms";
}
