// create and add an author to the description
$('body').on('click','.add_author_button',function(){
    var form = $(`#formdata`)[0];
    var formdata = new FormData(form);

    var description = $(this).attr('id')

    formdata.append('instance_y', description); //Person

    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        url: $(this).attr('data-url'),
        data: formdata,
        }).done(function(){
            //reload author block
            $(`#author-block-reload-trigger`).click()
        });
});
