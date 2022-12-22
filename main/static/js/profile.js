$('body').on('click', '.add_layer', function(){
    pk = $(this).attr('id').split('_')[1]
    $.ajax({
        type: "GET",
        url: $(this).attr('data-url'),
        }).done(function(data){
            getProfile(pk)
        });

});

$('body').on('click', '.add_other_layer', function(){
    layer = $(this).attr('id').split('_')[2]
    profile = $('.add_layer').attr('id').split('_')[1]
    $.ajax({
        type: "GET",
        url: `${$('.add_layer').attr('data-url')}?layer=${layer}`,
        }).done(function(data){
            getProfile(profile)
        });
});

$('body').on('click','.remove_other_layer', function(){
    layer = $(this).attr('id').split('_')[2]
    profile = $('.add_layer').attr('id').split('_')[1]
    $.ajax({
        type: "GET",
        url: $(this).attr('data-url')
        }).done(function(data){
            getProfile(profile)
        });
});

$('body').on('click', '.clone_layer', function(){
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
    const info = ele.attr('data-info')
    const model = info.split(',')[0]
    const pk = info.split(',')[1]
    var clone = ele.clone()
    clone.css('display', 'none')
    clone.attr('id','reload' )
    $.ajax({
        type: "GET",
        url: `${ele.attr('data-url')}&model=${model}&pk=${pk}`
        }).done(function(html){
            $('#modal-blank').html(html)
            $('#modal-form').append(
                `<input id='info' style="display:none" name='info' type='text' value="${info}">
                `
            )
            $('#modal-form').append(clone)
        });
    $('#modal-blank').addClass('active')
}

$('body').on('click','.fill_modal', function(){
    fillModal($(this))
})

$('body').on('click','#modal-close', function(){
    $('#modal-blank').removeClass('active')
})