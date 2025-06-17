// ✅ Format number to Twilio-compatible E.164 format
function formatPhoneNumber(phone) {
  phone = phone.trim().replace(/\s|-/g, '');

  if (phone.startsWith('+')) return phone;
  if (/^\d{10}$/.test(phone)) return `+91${phone}`;
  return '';
}

function sendOTP() {
  const rawPhone = document.getElementById("phone").value;
  const phone = formatPhoneNumber(rawPhone);

  if (!phone) {
    alert("⚠️ Enter a valid Indian phone number (10 digits or with +91).");
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
        localStorage.setItem("user", phone);
      } else {
        console.error("❌ Send OTP Error:", data.error);
        alert("❌ Failed to send OTP:\n" + (data.error || "Unknown error"));
      }
    })
    .catch(err => {
      console.error("❌ Network error:", err);
      alert("⚠️ Network error. Please try again.");
    });
}

function verifyOTP() {
  const phone = formatPhoneNumber(document.getElementById("phone").value);
  const code = document.getElementById("otp").value.trim();

  if (!phone || !code) {
    alert("⚠️ Enter both phone number and OTP.");
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
        alert("✅ OTP verified successfully!");
        localStorage.setItem("user", phone);
        window.location.href = "/symptoms";
      } else {
        console.error("❌ Verification Error:", data.error);
        alert("❌ OTP verification failed:\n" + (data.error || "Try again"));
      }
    })
    .catch(err => {
      console.error("❌ Verification fetch error:", err);
      alert("⚠️ Something went wrong during verification.");
    });
}

function continueAsGuest() {
  localStorage.setItem("user", "guest");
  window.location.href = "/symptoms";
}
