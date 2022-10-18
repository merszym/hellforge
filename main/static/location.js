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
}
catch(err){
    //if no map is shown and leaflet not loaded
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
        console.log(this.value)
        searchLocation(this.value);
    }
  });

$("body").on("click",'.search-loc-item', function(){
    pk = this.id.split('_')[3]
    val = $(`#loc_search_val_${pk}`).html()
    $('#location-list').html(
        `<tr><td id="loc_${pk}">${val}</td><td>-</td></tr>`
    )
    $('#loclist').html(pk)
    $('.loc-search-appear').html('')
});