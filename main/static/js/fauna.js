// Handle the upload file
$('body').on('change','#fauna-batch-input', function(){
    var file_data = $('#fauna-batch-input').prop('files')[0];
    var form_data = new FormData();
    form_data.append('file', file_data);
    form_data.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    $.ajax({
        type: "POST",
        url: $(this).attr('data-url'),
        processData: false,
        contentType: false,
        data: form_data
        }).done(function(html){
            alert('test')
        });
})