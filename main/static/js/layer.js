$('body').on('click', '#layer-setname', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('name', $('[name=layer-name]').val());
    formdata.append('unit', $('[name=layer-unit]').val());
    formdata.append('pk',$('[name=pk]').val());
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

//add culture to layer
$("body").on("click",'.search-culture-item', function(){
    //replace the culture in the backend and reload the modal
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', `${$('[name=info]').val().replace(',','_')}`); //layer
    formdata.append('instance_y', `culture_${$(this).attr('id')}`); //culture
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        url: $('#ajax_culture_set').attr('data-url'),
        data: formdata,
        }).done(function(){
            $('#reload').click();
        });
});

//remove culture from layer
$('body').on('click', '#culture_set_null', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $('[name=info]').val().replace(',','_'));
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

$('body').on('click', '#layer-setparent', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_y',$('[name=parent]').val()); //the layer_pk of the chosen parent
    formdata.append('instance_x',`layer_${$('[name=pk]').val()}`); //the pk of the layer, from the synonym-form
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

$('body').on('click', '.layer_unset_parent', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', `layer_${$('[name=pk]').val()}`); //layer,pk --> layer_pk
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