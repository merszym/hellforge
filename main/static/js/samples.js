//Add image to a sample-batch-gallery
$('body').on('click','.add_samplebatch_image',function(){
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