$("body").on("click", '.addDate', function(){
    $.ajax({
        type: "POST",
        url: $('#ajax_add_date').attr('data-url'),
        data: $("#modal-form").serialize(),
        }).done(function(data){
            if(data['status']){
                location.reload();
            } else {
                ele = $('#info')
                $('#modal-blank').html(data)
                $('#modal-form').append(ele)
            }
        });
});

// mark dates as delete
$("body").on('click', '.date_delete', function(){
    pk = $(this).attr('id').split('_')[2]
    ele = $(`#date_option_${pk}`)
    if(ele.attr('selected')){
        ele.removeAttr('selected')
        $(`#date_display_row_${pk} > td`).addClass('del')
    } else {
        ele.attr('selected','selected')
        $(`#date_display_row_${pk} > td`).removeClass('del')
    }
});

// Validate the dating form
$('body').on('keyup paste','#estimate',function(){
    if(this.value.length > 0){
        $('#upper').prop('disabled', true);
        $('#lower').prop('disabled', true);
    } else {
        $('#upper').prop('disabled', false);
        $('#lower').prop('disabled', false);
    }
});
$('body').on('keyup paste','.date_range',function(){
    if(this.value.length > 0){
        $('#estimate').prop('disabled', true);
        $('#plusminus').prop('disabled', true);
    } else {
        $('#estimate').prop('disabled', false);
        $('#plusminus').prop('disabled', false);
    }
});