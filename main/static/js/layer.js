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

// Set foreign key model to the layer
// = epoch, culture
$("body").on('click', '.set-search-item', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $('[name=info]').val()); //layer
    formdata.append('instance_y', $(this).attr('id')); //model
    var model = $(this).attr('id').split('_')[0]
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        url: $(`#layer_${model}_set`).attr('data-url'),
        data: formdata,
        }).done(function(){
            $('#reload').click();
        });
})

// remove forein key model from layer
// = epoch, culture, parent
$('body').on('click', '.unset-fk-item', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $('[name=info]').val()); //the layer
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