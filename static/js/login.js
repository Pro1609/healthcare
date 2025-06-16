const firebaseConfig = {
  apiKey: "AIzaSyCUCtrzLGYo7RVP0tLO7_bXju0Otn9mofo",
  authDomain: "auth-3438b.firebaseapp.com",
  projectId: "auth-3438b",
  storageBucket: "auth-3438b.appspot.com",
  messagingSenderId: "957059014720",
  appId: "1:957059014720:web:xyz"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// reCAPTCHA Setup
window.onload = () => {
  window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {
    'size': 'normal',
    'callback': (response) => {
      console.log("reCAPTCHA solved ✅");
    },
    'expired-callback': () => {
      alert("reCAPTCHA expired, please refresh and try again.");
    }
  });
  recaptchaVerifier.render();
};

let confirmationResult;

// Send OTP
function sendOTP() {
  const phone = document.getElementById("phone").value;
  const appVerifier = window.recaptchaVerifier;

  firebase.auth().signInWithPhoneNumber(phone, appVerifier)
    .then((result) => {
      confirmationResult = result;
      alert("OTP Sent Successfully!");
    })
    .catch((error) => {
      console.error(error);
      alert("OTP sending failed. Make sure your number is valid.");
    });
}

// Verify OTP
function verifyOTP() {
  const otp = document.getElementById("otp").value;

  confirmationResult.confirm(otp).then((result) => {
    const user = result.user;
    localStorage.setItem("user", user.phoneNumber);
    window.location.href = "/symptoms";
  }).catch((error) => {
    console.error(error);
    alert("Invalid OTP. Try again.");
  });
}

// Guest Access
function continueAsGuest() {
  localStorage.setItem("user", "guest");
  window.location.href = "/symptoms";
}
