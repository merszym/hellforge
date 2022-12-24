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
                console.log($('#reload'))
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
    formdata.append('info', $('[name=info]').val());
    formdata.append('pk', $(this).attr('id')); //culture
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
                console.log($('#reload'))
                $('#reload').click()
            }
        }
    });

});