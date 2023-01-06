//generic search function!
//search-input is handled by the specific data-url tag!
//make sure to have a csrf token ready
$('body').on('keyup paste','#search-input',function(){
    var model = $(this).attr('data-model') //data-model is the searched for model
    var origin = $(this).attr('data-origin') //data-for is the current model in search of model
    if ($(this).val().length === 0) {
        $(`.${model}-search-appear`).hide()
    }
    else {
        var formdata = new FormData();
        formdata.append('keyword', $(this).val());
        formdata.append('origin', origin)
        formdata.append('model', model)
        formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
        $.ajax({
            type: "POST",
            processData: false,
            contentType: false,
            data: formdata,
            url: $(this).attr("data-url"),
            success: function(html) {
                $(`.${model}-search-appear`).show()
                $(`.${model}-search-appear`).html(html)
            }
        });
    }
});