function getProfile(pk=null){
    if(pk != null){
        url = $('#profile-add').attr('data-url').replace('1',pk)
    } else {
        url = $('.tab-item.active').attr('data-url')
    }
    if(url){
        $.ajax({
            type: "GET",
            url: url,
            }).done(function(data){
                $('#profile-detail').html(data)
                makeSortable()
            });
        }
}

$('body').on('click','#profile-add', function(){
    $('#modal-profile').addClass('active')
});

$('body').on('click', '#modal-profile-close', function(){
    $('#modal-profile').removeClass('active')
});

$('body').on('click', '#profile-submit', function(){
    $('#modal-profile').removeClass('active')
    $.ajax({
        type: "POST",
        url: $('#profile-submit').attr('data-url'),
        data: $("#profile-form").serialize()
        }).done(function(html){
            $('#profile-list').replaceWith(html);
        });
});

$('body').on('click','.tab-item', function(){
    $('.tab-item').removeClass('active')
    $(this).addClass('active')
    getProfile()
});

function makeSortable(){
    $("#layer_tbody").sortable({
        items:'tr',
        containment: "parent",
        axis:'y',
        cursor:'move',
        delay: 200,
        handle:'.sort_handle',
        opacity: 0.7,
        stop: function( event, ui ) {
            //get the new order of layers
            positions = []
            $(".table_row").each(function(ind){
                pos = $(this).attr('id')
                if(pos){
                    positions.push(pos.split('_')[1])
                }
            });
            //make ajax call to save udpdates pos
            $.ajax({
                type: "GET",
                url: $('#layer_tbody').attr('data-url'),
                data: {'new_positions':positions.join(',')},
                });
        },
    });
};

$('.overview-toggle').on('click', function(){
    $('.overview-toggle').removeClass('btn-primary')
    $(this).addClass('btn-primary')
    if($(this).attr('id')=='btn-overview'){
        $('#description-overview').show()
        $('#description-description').hide()
    } else{
        $('#description-overview').hide()
        $('#description-description').show()
    }
})

$("#resize-editor").on('click', function(){
    $('#mobile').toggleClass('col-4')
    $('#mobile').toggleClass('col-12')
});

$(window).resize(function resize(){
    if ($(window).width() < 1000) {
        $('#mobile').removeClass('col-4')
        $('#mobile').addClass('col-12')
    } else {
        $('#mobile').removeClass('col-12')
        $('#mobile').addClass('col-4')
    }
}).trigger('resize');


// Attach search results to site
// = contactperson
$("body").on('click', '.site-search-item', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $('[name=info]').val()); //site
    formdata.append('instance_y', $(this).attr('id')); //model
    var model = $(this).attr('id').split('_')[0]
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        url: $(`#site_${model}_set`).attr('data-url'),
        data: formdata,
        }).done(function(){
            $('#reload').click();
        });
})


getProfile()