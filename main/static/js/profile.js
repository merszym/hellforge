//delete the profile
$('body').on('click', '.profile_delete', function(){
    //delete a synonym on click
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', `profile_${$('[name=profile_id]').val()}`);
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $(this).attr("data-url"),
        success: function(data) {
            if(data['status']){
                location.reload()
            }
        }
    });
});


// Add a new layer to the profile
$('body').on('click', '.add_new_layer', function(){
    pk = $('[name=profile_id]').val()
    var formdata = new FormData()
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_y', `profile_${pk}`);
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $(this).attr('data-url'),
        success: function(data) {
            if(data['status']){
                getProfile(pk)
            }
        }
    });
});

// add an existing layer to the profile
// or remove an existing layer from the profile
$('body').on('click', '.layer_profile', function(){
    pk = $('[name=profile_id]').val()
    var formdata = new FormData()
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_y', `profile_${pk}`);
    formdata.append('instance_x', `layer_${$(this).attr('id').split('_')[2]}`);
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $(this).attr('data-url'),
        success: function(data) {
            if(data['status']){
                getProfile(pk)
            }
        }
    });
});


$('body').on('click', '.clone_layer', function(){
    pk = $('[name=profile_id]').val()
    $.ajax({
        type: "GET",
        url: $(this).attr('data-url'),
        }).done(function(){
            getProfile(pk)
        });
});

//Fill blank modal with dating html
//Add info-field for the dating
function fillModal(ele){
    const instance = ele.attr('data-info')
    var clone = ele.clone()
    clone.css('display', 'none')
    clone.attr('id','reload' )
    $.ajax({
        type: "GET",
        url: `${ele.attr('data-url')}&instance=${instance}`
        }).done(function(html){
            $('#modal-blank').html(html)
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

$('body').on('click','#modal-close', function(){
    $('#modal-blank').removeClass('active')
})

$('body').on('click', '.refresh_profile', function(){
    getProfile()
})