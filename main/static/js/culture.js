// Attach search results to culture
// = parent
$("body").on('click', '.culture-search-item', function(){
    var formdata = new FormData();
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $('[name=info]').val()); //culture
    formdata.append('instance_y', $(this).attr('id')); //model
    var model = $(this).attr('id').split('_')[0]
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        url: $(`#culture_${model}_set`).attr('data-url'),
        data: formdata,
        }).done(function(){
            $('#reload').click();
        });
})