// Iniciar o mapa
let map = L.map('map').setView([-23.5342, -46.6358], 14); // Coordenadas da Faculdade Impacta

// Adicionar tiles ao mapa
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
}).addTo(map);

// Adicionar marcadores de sensores (um real e cinco fictícios)
let sensors = [
    {name: "Sensor Real", lat: -23.5342, lng: -46.6358},
    {name: "Sensor 2", lat: -23.5372, lng: -46.6400},
    {name: "Sensor 3", lat: -23.5302, lng: -46.6402},
    {name: "Sensor 4", lat: -23.5335, lng: -46.6300},
    {name: "Sensor 5", lat: -23.5355, lng: -46.6335},
    {name: "Sensor 6", lat: -23.5360, lng: -46.6370}
];

sensors.forEach(sensor => {
    let marker = L.marker([sensor.lat, sensor.lng]).addTo(map);
    marker.bindPopup(`<b>${sensor.name}</b><br>Clique para mais detalhes.`);
});
