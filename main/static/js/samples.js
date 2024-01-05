// Handle the upload file
$('body').on('change','#sample-batch-input', function(){
    var file_data = $(this).prop('files')[0];
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
$('body').on('click', '#sample-table-confirm', function(){
    $('#sample-table-confirm').addClass('loading')
    $.ajax({
        type: "POST",
        url: $('#sample-table-confirm').attr('data-url'),
        data: $('#sample-batch-verify-form').serialize()
        }).done(function(data){
            if(data['status']){
                location.reload()
            }
        });
})

//Add image to a sample-batch-gallery
$('body').on('click','.add_samplebatch_image',function(){
    var instance_x = $(this).attr('data-x')
    var url = $(this).attr('data-url')
    var fileinput = $('<input>').attr({
            type: 'file',
            name: 'batch_image'
    })
    // click the button
    fileinput.change(function () {
        if (fileinput.get(0).files.length === 0) {
            console.log("No files selected.");
        } else {
            // handle the upload
            var file_data = fileinput.prop('files')[0];
            var form_data = new FormData();
            form_data.append('image', file_data);
            form_data.append('instance_x', instance_x)
            form_data.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
            $.ajax({
                type: "POST",
                url: url,
                processData: false,
                contentType: false,
                data: form_data
                }).done(function(){
                    //#TODO: update the gallery...
                    location.reload()
                });
        }
    });
    fileinput.click();
})

