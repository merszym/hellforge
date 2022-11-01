try{
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
        var json = drawnItems.toGeoJSON();
        document.getElementById('geojson').innerHTML = JSON.stringify(json);
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

var searchLocation = function( data ) {
    $.ajax({
        type: "post",
        url: $('#loc-search').attr("data-url"),
        data: {
            'keyword': data,
        },
        success: function(respond) {
            if(Object.keys(respond).length === 0){
                locadd = $('#loc-search-appear').attr('data-url');
                $('.loc-search-appear').html(
                `<div style='padding:10px;'>
                    <a class="btn btn-primary btn tooltip" target="_blank" href="${locadd}" data-tooltip="Add Location">
                        <i class="icon icon-plus"></i>
                    </a>
                </div>
                `
                )
            }
            else{
                $('.loc-search-appear').html(
                    `
                    <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                        <th>Location</th>
                        <th></th>
                        </tr>
                    </thead>
                    <tbody id='loc-search-tbody'>
                    </tbody>
                    </table>
                    `
                )
                for (const [key, value] of Object.entries(respond)) {
                    $('#loc-search-tbody').append(
                        `<tr>
                        <td id=loc_search_val_${key}>${value}</td>
                        <td><span class='btn search-loc-item' id=loc_search_result_${key}>Take</span></td>
                        </tr>
                        `
                    )
                }
            }
        }
    });
  }

$('#loc-search').on('keyup paste',function(){
    if(this.value.length >= 3){
        searchLocation(this.value);
    }
  });

$("body").on("click",'.search-loc-item', function(){
    pk = this.id.split('_')[3]
    val = $(`#loc_search_val_${pk}`).html()
    $('#location-list').html(
        `<tr><td id="loc_${pk}">${val}</td><td>-</td></tr>`
    )
    $('#id_loc').html(
        `<option value="${pk}" selected></option>`
    )
});

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