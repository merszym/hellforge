var map = L.map('map').setView([51.34, 12.39], 5);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

var drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

var drawControl = new L.Control.Draw({
    draw: {
        polyline: false,
        circlemarker: false,
        circle:false
    },
    edit: {
        featureGroup: drawnItems
    }
});
map.addControl(drawControl);

map.on('draw:created', function (e) {
    layer = e.layer;
    drawnItems.addLayer(layer);
});

function saveLayer(){
    var json = drawnItems.toGeoJSON();
    document.getElementById('geojson').innerHTML = JSON.stringify(json);
}

function onEachFeature(feature, layer){
    drawnItems.addLayer(layer)
}

function drawJson(json){
    L.geoJSON(json, {
        onEachFeature: onEachFeature
    });
}
function fitBounds(){
    map.fitBounds(drawnItems.getBounds());
}