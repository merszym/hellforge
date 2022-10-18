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


$('.openModal').on('click', function(){
    $('#modal-id').removeClass('inactive')
    $('#modal-id').addClass('active')
});

$('#modal-close').on('click', function(){
    $('#modal-id').addClass('inactive')
    $('#modal-id').removeClass('active')
});

$(".addReference").on("click", function(){
    $.ajax({
        type: "POST",
        url: $('#ajax_add_ref').attr('data-url'),
        data: $("#reference-form").serialize(),
        }).done(function(data){
            $('#reference-list').append(
                `<tr><td id="ref_${data['pk']}">${data['short']}</td><td>${data['title']}</td><td>-</td></tr>`
            )
            $('#reflist').html($('#reflist').html()+','+data['pk'])
        });
});

//Searching for references
var searchFunction = function( data ) {
    $.ajax({
        type: "post",
        url: $('#ref-search').attr("data-url"),
        data: {
            'keyword': data,
        },
        success: function(respond) {
            $('.search-appear').html(
                `
                <table class="table table-striped table-hover">
                <thead>
                    <tr>
                    <th>Reference</th>
                    <th></th>
                    <th></th>
                    </tr>
                </thead>
                <tbody id='search-tbody'>
                </tbody>
                </table>
                `

            )
            for (const [key, value] of Object.entries(respond)) {
                $('#search-tbody').append(
                    `<tr>
                    <td id=search_short_${key}>${value.split(';;')[0]}</td>
                    <td id=search_title_${key}>${value.split(';;')[1]}</td>
                    <td><span class='btn search-item' id=search_result_${key}>Add</span></td>
                    </tr>
                    `
                )
            }
        }
    });
  }

$('#ref-search').on('keyup paste',function(){
    if(this.value.length >= 3)
        searchFunction(this.value);
  });

$("body").on("click",'.search-item', function(){
    pk = this.id.split('_')[2]
    short = $(`#search_short_${pk}`).html()
    title = $(`#search_title_${pk}`).html()
    $('#reference-list').append(
        `<tr><td id="ref_${pk}">${short}</td><td>${title}</td><td>-</td></tr>`
    )
    $('#reflist').html($('#reflist').html()+','+pk)
});
