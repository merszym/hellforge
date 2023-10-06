$('body').on('click','#synonym-add', function(){
    //add a synonym to a model on click
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('name', $('[name=synonym]').val());
    formdata.append('type', $('[name=synonym-type]').val());
    formdata.append('instance_y', `${$('[name=model]').val()}_${$('[name=pk]').val()}`);
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $('#synonym-add').attr("data-url"),
        success: function(data) {
            if(data['status']){
                $('#reload').click()
            }
        }
    });
});