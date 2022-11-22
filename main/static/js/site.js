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

$('#profile-add').on('click', function(){
    $('#modal-profile').addClass('active')
});

$('#modal-profile-close').on('click', function(){
    $('#modal-profile').removeClass('active')
});

$('#profile-submit').on('click', function(){
    $('#modal-profile').removeClass('active')
    $.ajax({
        type: "POST",
        url: $('#profile-submit').attr('data-url'),
        data: $("#profile-form").serialize()
        }).done(function(data){
            url = $('#profile-add').attr('data-url').replace('1',data['pk'])
            $('.tab-item').removeClass('active')
            $(
            `
            <li class="tab-item active" data-url="${url}">
                <a class="c-hand">${data['name']}</a>
            </li>
            `
            ).insertBefore($('#before-profile-add'))
            getProfile(data['pk'])
        });
});

$('.tab-block').on('click','.tab-item', function(){
    $('.tab-item').removeClass('active')
    $(this).addClass('active')
    getProfile()
});

function makeSortable(){
    $("#layer_tbody").sortable({
        items:'tr',
        cursor:'move',
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

$(window).resize(function resize(){
    if ($(window).width() < 1000) {
        $('#mobile').removeClass('col-4')
    } else {
        $('#mobile').addClass('col-4')
    }
}).trigger('resize');

getProfile()
resize()