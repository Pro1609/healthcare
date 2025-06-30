document.addEventListener("DOMContentLoaded", () => {
  const statusEl = document.getElementById("status");
  const listEl = document.getElementById("hospital-list");

  if (!navigator.geolocation) {
    statusEl.textContent = "Geolocation is not supported by your browser.";
    return;
  }

  navigator.geolocation.getCurrentPosition(success, error);

  function success(position) {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    statusEl.textContent = "Searching for hospitals near you...";

    fetch(`https://atlas.microsoft.com/search/poi/json?subscription-key=${AZURE_MAPS_KEY}&api-version=1.0&query=hospital&lat=${lat}&lon=${lon}&radius=10000&limit=10`)
      .then(res => res.json())
      .then(data => {
        if (!data.results || data.results.length === 0) {
          statusEl.textContent = "No hospitals found nearby.";
          return;
        }

        statusEl.textContent = "Hospitals near you:";
        listEl.innerHTML = "";

        data.results.forEach(hospital => {
          const li = document.createElement("li");
          li.className = "hospital-item";
          li.innerHTML = `
            <strong>${hospital.poi.name}</strong><br/>
            📍 ${hospital.address.freeformAddress}<br/>
            📏 ${(hospital.dist / 1000).toFixed(2)} km away
          `;
          listEl.appendChild(li);
        });
      })
      .catch(err => {
        console.error(err);
        statusEl.textContent = "Error fetching hospital data.";
      });
  }

  function error() {
    statusEl.textContent = "Permission denied or location access failed.";
  }
});
