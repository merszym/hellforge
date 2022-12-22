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