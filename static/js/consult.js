document.addEventListener("DOMContentLoaded", () => {
  const statusEl = document.getElementById("status");
  const hospitalListEl = document.getElementById("hospitalList");
  const MAX_HOSPITALS = 9;

  // Display an error message
  function showError(message) {
    statusEl.textContent = message;
    hospitalListEl.innerHTML = "";
  }

  // Render hospital cards dynamically
  function displayHospitals(hospitals) {
    hospitalListEl.innerHTML = "";

    if (!hospitals || hospitals.length === 0) {
      showError("No hospitals found nearby.");
      return;
    }

    // Enforce max 9 hospitals
    const limitedHospitals = hospitals.slice(0, MAX_HOSPITALS);

    statusEl.textContent = `Showing ${limitedHospitals.length} hospital(s) near you:`;

    limitedHospitals.forEach(hospital => {
      const name = hospital.poi?.name || "Unnamed Hospital";
      const address = hospital.address?.freeformAddress || "N/A";
      const distance = hospital.dist ? `${(hospital.dist / 1000).toFixed(2)} km` : "N/A";

      const card = document.createElement("div");
      card.className = "hospital-card";

      const inner = document.createElement("div");
      inner.className = "hospital-inner";
      inner.innerHTML = `
        <h3>${name}</h3>
        <p><strong>Address:</strong> ${address}</p>
        <p><strong>Distance:</strong> ${distance}</p>
      `;

      card.appendChild(inner);
      hospitalListEl.appendChild(card);
    });
  }

  // Call backend with user's location
  function fetchHospitals(lat, lon) {
    statusEl.textContent = "Fetching nearby hospitals...";

    fetch("/consult", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ lat, lon })
    })
      .then(res => {
        if (!res.ok) throw new Error("Network response was not ok");
        return res.json();
      })
      .then(data => {
        console.log("✅ Hospital data received:", data);
        displayHospitals(data.results);
      })
      .catch(err => {
        console.error("❌ Fetch error:", err);
        showError("Error fetching hospital data.");
      });
  }

  // Request user location
  if ("geolocation" in navigator) {
    navigator.geolocation.getCurrentPosition(
      position => {
        const { latitude, longitude } = position.coords;
        console.log("📍 Location obtained:", latitude, longitude);
        fetchHospitals(latitude, longitude);
      },
      error => {
        console.error("❌ Location access error:", error);
        showError("Location access denied or unavailable.");
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  } else {
    showError("Geolocation not supported by your browser.");
  }
});
