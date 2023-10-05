$('body').on('click', '#layer-setname', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('name', $('[name=layer-name]').val());
    formdata.append('unit', $('[name=layer-unit]').val());
    formdata.append('instance_x',$(this).attr('data-x'));
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $('#layer-setname').attr("data-url"),
        success: function(data) {
            if(data['status']){
                $('#reload').click()
            }
        }
    });

});

// remove forein key model from layer
// if id exists, its a m2m model --> remove that as well
// = epoch, culture, parent
$('body').on('click', '.unset-item', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $('[name=info]').val()); //the layer
    if($(this).attr('id')){
        formdata.append('instance_y', $(this).attr('id'))
    }
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $(this).attr('data-url'),
        success: function(data) {
            if(data['status']){
                $('#reload').click()
            }
        }
    });
});

$('body').on('click', '#layer-setparent', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_y',$('[name=parent]').val()); //the layer_pk of the chosen parent
    formdata.append('instance_x',$('[name=info]').val()); //the pk of the layer, from the synonym-form
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $(this).attr("data-url"),
        success: function(data) {
            if(data['status']){
                $('#reload').click()
            }
        }
    });
});