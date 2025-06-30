function getLocation() {
  const status = document.getElementById("status");
  status.innerText = "Requesting location access...";

  if (!navigator.geolocation) {
    status.innerText = "Geolocation is not supported by your browser.";
    return;
  }

  navigator.geolocation.getCurrentPosition(success, error);
}

function success(position) {
  const latitude = position.coords.latitude;
  const longitude = position.coords.longitude;

  document.getElementById("status").innerText = "Fetching nearby hospitals...";

  fetch("/consult", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ lat: latitude, lon: longitude })
  })
    .then(response => response.json())
    .then(data => {
      document.getElementById("status").innerText = "";
      renderHospitals(data.hospitals);
    })
    .catch(() => {
      document.getElementById("status").innerText = "Something went wrong while fetching hospitals.";
    });
}

function error() {
  document.getElementById("status").innerText = "Unable to retrieve location. Please allow location access and try again.";
}

function renderHospitals(hospitals) {
  const resultsBox = document.getElementById("resultsBox");
  resultsBox.innerHTML = "";

  if (hospitals.length === 0) {
    resultsBox.innerHTML = "<p style='text-align:center; color:#ccc;'>No hospitals found nearby.</p>";
    return;
  }

  hospitals.forEach(hospital => {
    const card = document.createElement("div");
    card.className = "hospital-card";

    card.innerHTML = `
      <h3>${hospital.name}</h3>
      <p><strong>Distance:</strong> ${hospital.distance} km</p>
      <p><strong>Address:</strong> ${hospital.address}</p>
      <button class="btn-glow" onclick="alert('Demo: Booking initiated for ${hospital.name}')">Book Now</button>
    `;

    resultsBox.appendChild(card);
  });
}
