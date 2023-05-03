// Handle the upload file
$('body').on('change','#fauna-batch-input', function(){
    var file_data = $('#fauna-batch-input').prop('files')[0];
    var form_data = new FormData();
    form_data.append('file', file_data);
    form_data.append('instance_x', $('[name=info]').val())
    form_data.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    $.ajax({
        type: "POST",
        url: $(this).attr('data-url'),
        processData: false,
        contentType: false,
        data: form_data
        }).done(function(html){
            $('.content').html(html)
        });
})

// Handle verification of the upload table
$('body').on('click', '#fauna-table-confirm', function(){
    $('#fauna-table-confirm').addClass('loading')
    $.ajax({
        type: "POST",
        url: $('#fauna-table-confirm').attr('data-url'),
        data: $('#fauna-batch-verify-form').serialize()
        }).done(function(data){
            if(data['status']){
                location.reload()
            }
        });
})