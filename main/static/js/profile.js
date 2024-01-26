// Add a new layer to the profile
$('body').on('click', '.add_new_layer', function(){
    var formdata = new FormData()
    var reload = $(this).attr('data-reload')
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_y', $(this).attr('data-y'));
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $(this).attr('data-url'),
        success: function() {
            reloadElement(reload)
        }
    });
});

$('body').on('click', '.clone_layer', function(){
    pk = $('[name=profile_id]').val()
    $.ajax({
        type: "GET",
        url: $(this).attr('data-url'),
        }).done(function(){
            reloadElement('site_layer')
        });
});

//Fill blank modal with dating html
//Add info-field for the dating
function fillModal(ele){
    const instance = ele.attr('data-info')
    $('#modal-blank').removeClass('modal-lg')
    var size = ele.attr('data-size')
    var clone = ele.clone()
    clone.css('display', 'none')
    clone.attr('id','reload' )
    $.ajax({
        type: "GET",
        url: `${ele.attr('data-url')}&instance=${instance}`
        }).done(function(html){
            $('#modal-blank').html(html)
            $('#modal-blank').addClass(size)
            $('#modal-form').append(
                `<input id='info' style="display:none" name='info' type='text' value="${instance}">
                `
            )
            $('#modal-form').append(clone)
        });
    $('#modal-blank').addClass('active')
}

$('body').on('click','.fill_modal', function(){
    fillModal($(this))
})