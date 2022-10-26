$('.DateModal').on('click', function(){
    $('#dating-modal').addClass('active')
});

$('#dating-modal-close').on('click', function(){
    $('#dating-modal').removeClass('active')
});

$(".addDate").on("click", function(){
    $('#dating-modal').removeClass('active')
    $.ajax({
        type: "POST",
        url: $('#ajax_add_date').attr('data-url'),
        data: $("#dating-form").serialize(),
        }).done(function(data){
            pk = data['pk']
            $('#dating-list').append(
                `<tr id=date_display_row_${pk} >
                    <td></td>
                    <td id="date_${pk}">${data['date']}</td>
                    <td>${data['method']}</td>
                    <td><i id="date_delete_${pk}" class="icon btn btn-primary icon-delete date_delete"></i></td>
                </tr>`
            )
            $('#id_date').append(
                `<option id="date_option_${pk}" value="${pk}" selected></option>`
            )
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