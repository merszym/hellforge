// switch between profiles
$('body').on('click','.switch_profile', function(){
    $('.show_profile').hide();
    $(`#show_${$(this).attr('data-show')}`).show()
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

// switch between main tabs on the site level
$('body').on('click', '.select-block-content', function(){
    $('.block-content').hide();
    $(`#${$(this).attr('data-select')}`).show();
});