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
    console.log(layer, profile)
    $.ajax({
        type: "GET",
        url: $(this).attr('data-url')
        }).done(function(data){
            getProfile(profile)
        });
});