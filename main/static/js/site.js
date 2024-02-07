function reloadTimeline(){
    var gets = ""
    // check if filters are toggled:
    if($('#timeline-show-hidden').hasClass('btn-primary')){
        gets = `hidden=1`
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

// switch between profiles
$('body').on('click','.switch_profile', function(){
    $('.show_profile').hide();
    $(`#show_${$(this).attr('data-show')}`).show()
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
    var reload = $(this).attr('data-reload')
    $.ajax({
        type: "POST",
        url: $('#profile-submit').attr('data-url'),
        data: $("#profile-form").serialize()
        }).done(function(){
            reloadElement(reload)
        });
});

// overview buttons
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

// resize sideboard
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

// load the timeline-data
$('body').on('click', '.timeline-filter', function(){
    $(this).toggleClass('btn-primary')
    reloadTimeline()
});


// switch between main tabs on the site level
$('body').on('click', '.select-block-content', function(){
    $('.block-content').hide();
    $(`#${$(this).attr('data-select')}`).show();
});