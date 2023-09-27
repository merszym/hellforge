//#TODO: find better way to sort the layers!
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
                }).done(function(){
                    reloadTimeline()
                });
        },
    });
};
function getProfile(pk){
    url = $('#profile-add').attr('data-url').replace('1',pk)
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

// switch between profiles
$('body').on('click','.minor', function(){
    $.ajax({
        type: "GET",
        url: $(this).attr('data-url'),
        }).done(function(data){
            $('#profile-detail').html(data)
            makeSortable()
        });
});

// add profiles
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
            $('#layers_update_click').click()
        });
});

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

$("body").on('click',"#resize-editor", function(){
    $('#mobile').toggleClass('col-4')
    $('#mobile').toggleClass('col-12')
});

$(window).resize(function resize(){
    if ($(window).width() < 1000) {
        $('#mobile').removeClass('col-4')
        $('#content-part').removeClass('col-8')
        $('#mobile').addClass('col-12')
    } else {
        $('#mobile').removeClass('col-12')
        $('#content-part').addClass('col-8')
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

// load the timeline-data
$('body').on('click', '.timeline-filter', function(){
    $(this).toggleClass('btn-primary')
    reloadTimeline()
});

function reloadTimeline(){
    var gets = ""
    // check if filters are toggled:
    if($('#timeline-show-hidden').hasClass('btn-primary')){
        gets = `hidden=1`
    }
    if($('#timeline-show-related').hasClass('btn-primary')){
        gets = `${gets}&related=1`
    }
    if($('#timeline-show-curves').hasClass('btn-primary')){
        gets = `${gets}&curves=1`
    }
    ele = $('#timeline-content')
    if(ele.length){
        ele.load(`${ele.attr('data-url')}?${gets}`)
    }
}

$( document ).ready(function(){
    reloadTimeline()
});

$('body').on('click', '.refresh_profile', function(){
    reloadTimeline()
})

// add site to project on clicking the button
$('body').on("click", '#site_project_add', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $(this).attr('data-x')); //site
    formdata.append('instance_y', $(this).attr('data-y')); //project
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        url: $(this).attr('data-url'),
        data: formdata,
        }).done(function(){
            location.reload()
        });

});

// remove site from project by clicking the button
$('body').on("click", '#site_project_remove', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $(this).attr('data-x')); //site
    formdata.append('instance_y', $(this).attr('data-y')); //project
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        url: $(this).attr('data-url'),
        data: formdata,
        }).done(function(){
            location.reload()
        });

});

// load descriptions
$('body').on("click", '.render_description', function(){
    $.ajax({
        type: "GET",
        url: $(this).attr('data-url'),
        }).done(function(html){
            $('#description-description').html(html)
        });
});

// switch between main tabs on the site level
$('body').on('click', '.select-block-content', function(){
    $('.block-content').hide();
    $(`#${$(this).attr('data-select')}`).show();
});