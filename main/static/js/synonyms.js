$('body').on('click','#synonym-add', function(){
    //add a synonym to a model on click
    var formdata = new FormData();
    formdata.append('name', $('[name=synonym]').val());
    formdata.append('type', $('[name=synonym-type]').val());
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    const url = window.location.pathname.split('/')
    pk = url.pop()
    model = url[1]
    formdata.append('model',model);
    formdata.append('modelpk', pk);
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $('#synonym-add').attr("data-url"),
        success: function(data) {
            if(data['status']){
                location.reload()
            }
        }
    });
});

$('body').on('click','.synonym_delete', function(){
    //add a synonym to a model on click
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('pk',$(this).attr('id').split('_')[1]);
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