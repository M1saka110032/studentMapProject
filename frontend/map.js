var map = L.map('map').setView([40, -95], 4);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
  .addTo(map);

fetch("http://127.0.0.1:8000/api/schools")
  .then(res => res.json())
  .then(schools => {
    schools.forEach(school => {

      let color = "blue";
      if (school.type === "university") color = "red";
      if (school.current_students === 0) color = "gray";

      let marker = L.circleMarker(
        [school.lat, school.lng],
        { radius: 8, color: color }
      ).addTo(map);

      let popupContent = `
        <b>${school.name}</b><br>
        Type: ${school.type}<br>
        Current: ${school.current_students}<br>
        Ever: ${school.historical_students}<br>
        <a href="${school.website}" target="_blank">Official Website</a><br>
        <a href="school.html?id=${school.id}">View More</a>
      `;

      marker.bindPopup(popupContent);
    });
  });
