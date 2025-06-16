// Firebase config (replace with yours)
const firebaseConfig = {
  apiKey: "AIzaSyCUCtrzLGYo7RVP0tLO7_bXju0Otn9mofo",
  authDomain: "auth-3438b.firebaseapp.com",
  projectId: "auth-3438b",
  storageBucket: "auth-3438b.appspot.com",
  messagingSenderId: "957059014720",
  appId: "1:957059014720:web:xyz" // Replace if needed
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Setup reCAPTCHA with dark theme
window.onload = () => {
  window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {
    size: 'normal',
    theme: 'dark',
    callback: (response) => {
      console.log("✅ reCAPTCHA solved");
    },
    'expired-callback': () => {
      alert("reCAPTCHA expired. Please refresh and try again.");
    }
  });
  recaptchaVerifier.render().then(widgetId => {
    window.recaptchaWidgetId = widgetId;
  });
};

let confirmationResult = null;

// Send OTP to user's phone number
function sendOTP() {
  let phoneInput = document.getElementById('phone').value.trim();

  // Auto-format phone number
  if (!phoneInput.startsWith("+91")) {
    phoneInput = "+91" + phoneInput;
  }

  const appVerifier = window.recaptchaVerifier;

  firebase.auth().signInWithPhoneNumber(phoneInput, appVerifier)
    .then(result => {
      confirmationResult = result;
      alert("✅ OTP sent to " + phoneInput);
    })
    .catch(error => {
      console.error("❌ OTP Send Error:", error);
      alert("Failed to send OTP. Ensure number is valid and try again.");
    });
}

// Verify the OTP entered by the user
function verifyOTP() {
  const code = document.getElementById('otp').value.trim();

  if (!confirmationResult) {
    alert("You must first request an OTP.");
    return;
  }

  confirmationResult.confirm(code)
    .then(result => {
      const user = result.user;
      console.log("✅ Phone verified:", user.phoneNumber);
      localStorage.setItem("user", user.phoneNumber);
      window.location.href = "/symptoms";
    })
    .catch(error => {
      console.error("❌ OTP Verification Error:", error);
      alert("Invalid OTP. Please try again.");
    });
}

// Continue as guest (no auth, just store label)
function continueAsGuest() {
  localStorage.setItem("user", "guest");
  window.location.href = "/symptoms";
}
