
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


// delete author from description
$('body').on('click','.delete_author',function(){
    var formdata = new FormData();

    formdata.append('instance_x', $(this).attr('data-x')); //Authorship
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())

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