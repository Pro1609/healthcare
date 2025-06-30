document.addEventListener("DOMContentLoaded", () => {
  const statusEl = document.getElementById("status");
  const hospitalList = document.getElementById("hospitalList");

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(success, error);
  } else {
    statusEl.textContent = "Geolocation not supported.";
  }

  function success(position) {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;

    statusEl.textContent = "Location acquired. Searching for hospitals...";

    fetch("/consult", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ lat, lon }),
    })
    .then((res) => res.json())
    .then((data) => {
      if (!data.hospitals || data.hospitals.length === 0) {
        hospitalList.innerHTML = "<p>No hospitals found nearby.</p>";
        return;
      }

      hospitalList.innerHTML = "";
      data.hospitals.forEach((hosp) => {
        const box = document.createElement("div");
        box.className = "hospital-card";
        box.innerHTML = `
          <div class="hospital-inner">
            <h3>${hosp.name}</h3>
            <p><strong>Address:</strong> ${hosp.address}</p>
            <p><strong>Distance:</strong> ${hosp.distance.toFixed(2)} km</p>
          </div>
        `;
        hospitalList.appendChild(box);
      });
    })
    .catch((err) => {
      console.error("❌ Fetch error:", err);
      statusEl.textContent = "Error fetching hospital data.";
    });
  }

  function error(err) {
    statusEl.textContent = "Permission denied or location unavailable.";
  }
});
