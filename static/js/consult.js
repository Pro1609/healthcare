document.addEventListener("DOMContentLoaded", () => {
  const statusEl = document.getElementById("status");
  const hospitalListEl = document.getElementById("hospitalList");

  function showError(message) {
    statusEl.textContent = message;
    hospitalListEl.innerHTML = "";
  }

  function displayHospitals(hospitals) {
    hospitalListEl.innerHTML = "";
    if (!hospitals || hospitals.length === 0) {
      showError("No hospitals found nearby.");
      return;
    }

    hospitals.forEach(hospital => {
      const card = document.createElement("div");
      card.className = "hospital-card";

      const inner = document.createElement("div");
      inner.className = "hospital-inner";

      inner.innerHTML = `
        <h3>${hospital.poi?.name || "Unnamed Hospital"}</h3>
        <p><strong>Address:</strong> ${hospital.address?.freeformAddress || "N/A"}</p>
        <p><strong>Distance:</strong> ${(hospital.dist / 1000).toFixed(2)} km</p>
      `;

      card.appendChild(inner);
      hospitalListEl.appendChild(card);
    });

    statusEl.textContent = "Hospitals within 10 km:";
  }

  function fetchHospitals(lat, lon) {
    statusEl.textContent = "Fetching nearby hospitals...";

    fetch("/consult", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ lat, lon })
    })
    .then(res => res.json())
    .then(data => displayHospitals(data.results))
    .catch(err => {
      console.error("❌ Fetch error:", err);
      showError("Error fetching hospital data.");
    });
  }

  if ("geolocation" in navigator) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        const { latitude, longitude } = pos.coords;
        fetchHospitals(latitude, longitude);
      },
      err => {
        console.error("❌ Location error:", err);
        showError("Location access denied or unavailable.");
      }
    );
  } else {
    showError("Geolocation not supported by your browser.");
  }
});
