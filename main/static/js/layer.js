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
    formdata.append('info', $('[name=info]').val());
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $('#culture_set_null').attr("data-url"),
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
    formdata.append('parent', $('[name=parent-select]').val()); //the pk of the chosen parent
    formdata.append('pk',$('[name=pk]').val()); //the pk of the layer
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $('#layer-setparent').attr("data-url"),
        success: function(data) {
            if(data['status']){
                $('#reload').click()
            }
        }
    });
});

$('body').on('click', '#layer-unsetparent', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('info',$('[name=info]').val()); //the pk of the layer
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $('#layer-unsetparent').attr("data-url"),
        success: function(data) {
            if(data['status']){
                $('#reload').click()
            }
        }
    });
});