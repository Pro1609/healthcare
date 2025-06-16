const firebaseConfig = {
  apiKey: "AIzaSyCUCtrzLGYo7RVP0tLO7_bXju0Otn9mofo",
  authDomain: "auth-3438b.firebaseapp.com",
  projectId: "auth-3438b",
  storageBucket: "auth-3438b.appspot.com",
  messagingSenderId: "957059014720",
  appId: "1:957059014720:web:xxxxxxxxxxxxx"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

window.onload = () => {
  window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {
    size: 'normal',
    callback: () => {
      console.log("reCAPTCHA verified");
    }
  });
  recaptchaVerifier.render();
};

function sendOTP() {
  const phone = document.getElementById("phone").value;
  if (!phone.startsWith("+91")) {
    alert("Enter phone number in +91XXXXXXXXXX format.");
    return;
  }

  auth.signInWithPhoneNumber(phone, window.recaptchaVerifier)
    .then(confirmationResult => {
      window.confirmationResult = confirmationResult;
      document.querySelector(".otp-section").style.display = "block";
      alert("OTP Sent!");
    })
    .catch(error => {
      console.error("SMS not sent", error);
      alert("Failed to send OTP. Check console for details.");
    });
}

function verifyOTP() {
  const otp = document.getElementById("otp").value;
  confirmationResult.confirm(otp)
    .then(result => {
      const user = result.user;
      sessionStorage.setItem("phoneNumber", user.phoneNumber);
      window.location.href = "/home"; // or wherever you want to go next
    })
    .catch(err => {
      alert("Incorrect OTP!");
      console.error(err);
    });
}

function continueAsGuest() {
  auth.signInAnonymously()
    .then(() => {
      sessionStorage.setItem("phoneNumber", "guest");
      window.location.href = "/home";
    })
    .catch(error => {
      console.error("Guest login failed", error);
    });
}
