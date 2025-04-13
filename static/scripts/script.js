// Asset for custom map marker
const busIcon =
  "https://icons.iconarchive.com/icons/flaticonmaker/flat-style/48/bus-icon.png";

let liveLocationData = {};
let stoppingsData = {};
let userBusNo;
let map;
let polylines = [];
let markers = [];
let watchId = null;
let passengerInterval = null;
let currentMode = "passenger"; // 'passenger' or 'bus'
let busMarker = null;

// ✅ Fetch user's assigned bus number
async function getUserBus() {
  try {
    const response = await fetch("/busno");
    userBusNo = await response.json();
    console.log("User Bus Number:", userBusNo);
  } catch (error) {
    console.error("Error fetching user bus number:", error);
  }
}

// ✅ Fetch live bus locations
async function getLiveLocation() {
  try {
    const response = await fetch("/location");
    liveLocationData = await response.json();
    console.log("Live Bus Locations:", liveLocationData);
  } catch (error) {
    console.error("Error fetching live location:", error);
  }
}

// ✅ Fetch route stoppings
async function getStoppings() {
  try {
    const response = await fetch("/stoppings");
    stoppingsData = await response.json();
    console.log("Stoppings Data:", stoppingsData);

    // Attach event listener after fetching stops
    document
      .getElementById("choice-busroute")
      .addEventListener("change", updateMap);
  } catch (error) {
    console.error("Error fetching stoppings:", error);
  }
}

// ✅ Initialize Google Map
function initMap() {
  const mapElement = document.getElementById("map");

  if (!mapElement) {
    console.error("Error: Map container not found!");
    return;
  }

  map = new google.maps.Map(mapElement, {
    center: { lat: 12.9716, lng: 80.1462 },
    zoom: 12,
    mapTypeControl: false,
    streetViewControl: false,
  });

  // Add mode toggle handler
  document
    .getElementById("modeToggle")
    .addEventListener("change", handleModeChange);
}

function handleModeChange() {
  currentMode = this.value;
  clearMapElements();

  if (currentMode === "bus") {
    alert("Bus mode activated! Select your route to start sharing location.");
  }
}



// ✅ Update Map when Bus Route Changes
function updateMap() {
  const busNumber = document.getElementById("choice-busroute").value;

  if (!busNumber || busNumber === "none") {
    clearMapElements();
    return;
  }

  clearMapElements();
  drawRoute(stoppingsData[busNumber]);
  placeMarkers(stoppingsData[busNumber]);

  if (currentMode === "bus") {
    startSharingLocation(busNumber);
  } else {
    startTrackingBusLocation(busNumber);
  }
}

function startSharingLocation(busNumber) {
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser");
    return;
  }

  watchId = navigator.geolocation.watchPosition(
    (position) => {
      const pos = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };

      // Update server with current position
      fetch("/update-location", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ busNo: busNumber, lat: pos.lat, lng: pos.lng }),
      });

      // Update local marker
      updateBusMarker(pos, busNumber);
      map.setCenter(pos);
    },
    (error) => {
      console.error("Geolocation error:", error);
      alert(`Error getting location: ${error.message}`);
    },
    { enableHighAccuracy: true }
  );
}


function startTrackingBusLocation(busNumber) {
  passengerInterval = setInterval(async () => {
    try {
      const response = await fetch(`/get-location/${busNumber}`);
      if (!response.ok) throw new Error("Location not available");

      const { lat, lng } = await response.json();
      updateBusMarker({ lat, lng }, busNumber);
      map.setCenter({ lat, lng });
    } catch (error) {
      console.error("Error fetching bus location:", error);
    }
  }, 3000); // Update every 3 seconds
}

function updateBusMarker(position, busNumber) {
  if (!busMarker) {
    busMarker = new google.maps.Marker({
      position: position,
      map: map,
      icon: busIcon,
      title: `Bus ${busNumber}`,
      animation: google.maps.Animation.BOUNCE,
    });
    markers.push(busMarker);
  } else {
    busMarker.setPosition(position);
  }
}


function clearMapElements() {
  clearRoutes();
  clearMarkers();
  busMarker = null;

  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }

  if (passengerInterval !== null) {
    clearInterval(passengerInterval);
    passengerInterval = null;
  }
}

// ✅ Draw Route on the Map
// ✅ Draw Route on the Map using Google Directions API
async function drawRoute(routeCoords) {
  if (!routeCoords || routeCoords.length < 2) return;

  clearRoutes(); // Clear existing routes before drawing a new one

  const directionsService = new google.maps.DirectionsService();
  const directionsRenderer = new google.maps.DirectionsRenderer({
    suppressMarkers: false, // Keep markers visible
    polylineOptions: {
      strokeColor: "#FF0000",
      strokeOpacity: 1.0,
      strokeWeight: 5, // Increase thickness for better visibility
    },
  });

  directionsRenderer.setMap(map); // Attach the renderer to the map

  const waypoints = routeCoords.slice(1, -1).map(coord => ({
    location: new google.maps.LatLng(coord[0], coord[1]),
    stopover: false, // Stops are just pass-through points
  }));

  const request = {
    origin: new google.maps.LatLng(routeCoords[0][0], routeCoords[0][1]),
    destination: new google.maps.LatLng(routeCoords[routeCoords.length - 1][0], routeCoords[routeCoords.length - 1][1]),
    waypoints: waypoints,
    travelMode: google.maps.TravelMode.DRIVING, // Ensure the route follows roads
    optimizeWaypoints: true, // Improves route efficiency
  };

  directionsService.route(request, (result, status) => {
    if (status === google.maps.DirectionsStatus.OK) {
      directionsRenderer.setDirections(result); // Draw the optimized route
      polylines.push(directionsRenderer); // Store reference for clearing later
      console.log("Route drawn successfully on roads");
    } else {
      console.error("Directions request failed:", status);
    }
  });
}


// ✅ Place Markers for Stops
function placeMarkers(routeCoords) {
  if (!routeCoords || routeCoords.length === 0) return;

  routeCoords.forEach((coord, index) => {
    let marker = new google.maps.Marker({
      position: { lat: coord[0], lng: coord[1] },
      map: map,
      title: "Bus Stop " + (index + 1),
      icon: {
        url: "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
        scaledSize: new google.maps.Size(30, 30),
      },
    });

    // Create an InfoWindow for the popup card
    let infoWindow = new google.maps.InfoWindow({
      content: `
        <div style="padding: 10px; font-family: Arial;">
          <h3 style="margin: 0; font-size: 16px;">Bus Stop ${index + 1}</h3>
          <p style="margin: 5px 0;"><strong>Location:</strong> ${
            coord[2] || "Unknown"
          }</p>
          <p style="margin: 5px 0;"><strong>Time:</strong> ${
            coord[3] || "Not Available"
          }</p>
          <p style="margin: 5px 0;"><strong>Estimated Time:</strong> ${
            coord[4] || "Not Available"
          }</p>
        </div>
      `,
    });

    // Add click event to show the popup
    marker.addListener("click", () => {
      infoWindow.open(map, marker);
    });

    markers.push(marker);
  });

  console.log("Markers placed successfully");
}

// ✅ Clear Routes from Map
function clearRoutes() {
  polylines.forEach((renderer) => renderer.setMap(null));
  polylines = [];
}


// ✅ Clear Markers from Map
function clearMarkers() {
  markers.forEach((marker) => marker.setMap(null));
  markers = [];
}
function startSharingLocation(busNumber) {
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser");
    return;
  }

  watchId = navigator.geolocation.watchPosition(
    (position) => {
      const pos = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };

      // Update server with current position
      fetch("/update-location", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          busNo: busNumber,
          lat: pos.lat,
          lng: pos.lng,
        }),
      });

      updateBusMarker(pos, busNumber);
      map.setCenter(pos);
    },
    (error) => {
      console.error("Geolocation error:", error);
      alert(`Error getting location: ${error.message}`);
    },
    { enableHighAccuracy: true }
  );
}

// ✅ Start tracking bus location (Passenger mode)
function startTrackingBusLocation(busNumber) {
  passengerInterval = setInterval(async () => {
    try {
      const response = await fetch(`/get-location/${busNumber}`);
      if (!response.ok) throw new Error("Location not available");

      const { lat, lng } = await response.json();
      updateBusMarker({ lat, lng }, busNumber);
      map.setCenter({ lat, lng });
    } catch (error) {
      console.error("Error fetching bus location:", error);
    }
  }, 3000);
}
// ✅ Share Current Location
function currentpos() {
  let busRoute = document.getElementById("choice-busroute").value;

  if (busRoute === "none" || !busRoute) {
    alert("Please select a bus route first!");
    return;
  }

  const websiteLink = window.location.href; // Get the current website link

  fetch("/sharelocation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      busno: parseInt(busRoute),
      link: websiteLink,
    }),
  })
    .then((response) => response.text())
    .then((data) => {
      openModal(websiteLink); // Open modal after sharing the website link

      // Ensure the selected bus route remains visible
      document.getElementById("choice-busroute").value = busRoute;

      // Fetch the latest stoppings data before updating the map
      return getStoppings();
    })
    .then(() => {
      updateMap(); // Ensure the map updates correctly with latest data
    })
    .catch((error) => {
      console.error("Error sharing website link:", error);
      alert("Failed to share website link. Please try again.");
    });
}

// Function to open the modal with location link
function openModal(locationLink) {
  document.getElementById("shareModal").style.display = "block";
  window.shareLocationLink = locationLink;
}

// Function to close the modal
function closeModal() {
  document.getElementById("shareModal").style.display = "none";
}

// Share on WhatsApp
function shareOnWhatsApp() {
  let url = `https://wa.me/?text= ${window.shareLocationLink}`;
  window.open(url, "_blank");
}

// Share on Instagram (Note: Instagram does not support direct location sharing)
function shareOnInstagram() {
  alert(
    "Instagram does not allow direct location sharing. Copy the link and share manually."
  );
}

// Share via SMS
function shareViaMessage() {
  let url = `sms:?body= ${window.shareLocationLink}`;
  window.open(url, "_blank");
}

// Copy Link
function copyLink() {
  navigator.clipboard.writeText(window.shareLocationLink).then(() => {
    alert("Link copied to clipboard!");
  });
}
// ✅ Add cleanup for geolocation tracking
window.addEventListener('beforeunload', () => {
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
  }
});
// ✅ Initialize App on Page Load
window.onload = async function () {
  try {
    await getUserBus();
    await getStoppings();
    initMap();
  } catch (error) {
    console.error("Error initializing app:", error);
  }
};

// Cleanup when page unloads
window.addEventListener("beforeunload", clearMapElements);


