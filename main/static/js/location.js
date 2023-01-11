try{
    var map = L.map('map',{
        scrollWheelZoom: false
    }).setView([51.3, 12], 5);
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
            circle:false,
        },
        edit: {
            featureGroup: drawnItems,
        }
    });

    map.addControl(drawControl);

    map.on('draw:created', function (e) {
        layer = e.layer;
        drawnItems.addLayer(layer);
    });

    function saveLayer(){
        if(drawnItems.getLayers().length > 0){
            var json = drawnItems.toGeoJSON();
            $('#geojson').html(JSON.stringify(json));
        }
    }

    function onEachFeature(feature, layer){
        if (feature.properties && feature.properties.popupContent) {
            layer.bindPopup(feature.properties.popupContent);
        }
        if (feature.properties && feature.properties.id) {
            layer.options.id = feature.properties.id;
        }
        //make colorful icons in case the propoerty is set
        if (feature.properties && feature.properties.color) {
            layer.setIcon(
                new L.DivIcon({
                    html: `
                        <svg style='z-index:2000' width="40" height="40" viewBox="0 0 512 512" version="1.1" preserveAspectRatio="none"  xmlns="http://www.w3.org/2000/svg">
                            <path d="M256,0C167.641,0,96,71.625,96,160c0,24.75,5.625,48.219,15.672,69.125C112.234,230.313,256,512,256,512l142.594-279.375   C409.719,210.844,416,186.156,416,160C416,71.625,344.375,0,256,0z" fill="${feature.properties.color}"></path>
                        </svg>`,
                    className: "",
                    iconSize: [40, 40],
                    iconAnchor: [20, 40],
                    popupAnchor:  [0, -20]
                })
            )
        }
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
    function openPopup(id){
        drawnItems.eachLayer(function (layer) {
            if (layer.options.id == id){
                layer.togglePopup()
            }
        });
    }
} catch {
    //;
}

// add layer by coordinates
$('#coordinates-span').on('click', function(){
    coords = $('#coordinates').val()
    lat = parseFloat(coords.split(',')[0])
    long = parseFloat(coords.split(',')[1])

    //geojson uses long-lat order -.-
    json = {"type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Point",
                "coordinates": [long, lat]
            }
        }]
    }
    drawJson(json)
    fitBounds()
});