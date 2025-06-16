const firebaseConfig = {
  apiKey: "AIzaSyCUCtrzLGYo7RVP0tLO7_bXju0Otn9mofo",
  authDomain: "auth-3438b.firebaseapp.com",
  projectId: "auth-3438b",
  storageBucket: "auth-3438b.appspot.com",
  messagingSenderId: "957059014720",
  appId: "1:957059014720:web:xyz"
};

firebase.initializeApp(firebaseConfig);

// Set up reCAPTCHA verifier on page load
window.onload = () => {
  window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {
    size: 'normal',
    callback: function(response) {
      console.log("reCAPTCHA solved");
    },
    'expired-callback': function() {
      alert("reCAPTCHA expired. Please solve again.");
    }
  });
  recaptchaVerifier.render();
};

let confirmationResult;

function sendOTP() {
  const phoneNumber = document.getElementById('phone').value.trim();
  
  if (!/^\+91\d{10}$/.test(phoneNumber)) {
    alert("Please enter a valid Indian phone number in the format +91xxxxxxxxxx");
    return;
  }

  const appVerifier = window.recaptchaVerifier;

  firebase.auth().signInWithPhoneNumber(phoneNumber, appVerifier)
    .then(result => {
      confirmationResult = result;
      alert("✅ OTP Sent Successfully!");
    })
    .catch(error => {
      console.error("❌ OTP Error:", error);
      alert("OTP sending failed. Make sure your number is valid and try again.");
    });
}

function verifyOTP() {
  const code = document.getElementById('otp').value.trim();
  if (!code || code.length < 6) {
    alert("Enter the 6-digit OTP.");
    return;
  }

  confirmationResult.confirm(code).then(result => {
    const user = result.user;
    localStorage.setItem("user", JSON.stringify(user.phoneNumber));
    window.location.href = "/symptoms";
  }).catch(error => {
    console.error("❌ OTP Verification Error:", error);
    alert("Invalid OTP. Please try again.");
  });
}

function continueAsGuest() {
  localStorage.setItem("user", "guest");
  window.location.href = "/symptoms";
}
