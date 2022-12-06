$('.add_layer').on('click', function(){
    pk = $(this).attr('id').split('_')[1]
    $.ajax({
        type: "GET",
        url: $(this).attr('data-url'),
        }).done(function(data){
            getProfile(pk)
        });

});

$('.add_other_layer').on('click', function(){
    layer = $(this).attr('id').split('_')[2]
    profile = $('.add_layer').attr('id').split('_')[1]
    $.ajax({
        type: "GET",
        url: `${$('.add_layer').attr('data-url')}?layer=${layer}`,
        }).done(function(data){
            getProfile(profile)
        });
});

$('.remove_other_layer').on('click', function(){
    layer = $(this).attr('id').split('_')[2]
    profile = $('.add_layer').attr('id').split('_')[1]
    $.ajax({
        type: "GET",
        url: $(this).attr('data-url')
        }).done(function(data){
            getProfile(profile)
        });
});

$('.clone_layer').on('click', function(){
    profile = $('.add_layer').attr('id').split('_')[1]
    $.ajax({
        type: "GET",
        url: $(this).attr('data-url')
        }).done(function(data){
            getProfile(profile)
        });
});

//Fill blank modal with dating html
//Add info-field for the dating
function fillModal(ele){
    $.ajax({
        type: "GET",
        url: ele.attr('data-url')
        }).done(function(html){
            $('#modal-blank').html(html)
            $('#dating-form').append(
                `<input id='info' style="display:none" name='info' type='text' value="${ele.attr('data-info')}">
                `
            )
        });
    $('#modal-blank').addClass('active')
}

$('.fill_modal').on('click', function(){
    fillModal($(this))
})

$('body').on('click','#modal-close', function(){
    $('#modal-blank').removeClass('active')
})