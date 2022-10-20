function getProfile(pk=null){
    console.log('get_profile')
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
                <a href='#'>${data['name']}</a>
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

getProfile()