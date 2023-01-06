$('.RefModal').on('click', function(){
    $('#reference-modal').removeClass('inactive')
    $('#reference-modal').addClass('active')
});

$('#modal-close').on('click', function(){
    $('#reference-modal').addClass('inactive')
    $('#reference-modal').removeClass('active')
});

$(".addReference").on("click", function(){
    $.ajax({
        type: "POST",
        url: $('#ajax_add_ref').attr('data-url'),
        data: $("#reference-form").serialize(),
        }).done(function(data){
            $('#reference-list').append(
                `<tr><td id="ref_${data['pk']}">${data['short']}</td><td>${data['title']}</td><td>-</td></tr>`
            )
            $('#id_ref').append(`<option value="${data['pk']}" selected></option>`)
        });
});

$("body").on("click",'.form-search-item', function(){
    pk = this.id.split('_')[1]
    short = $(`#reference_${pk}_short`).html()
    title = $(`#reference_${pk}_title`).html()
    $('#reference-list').append(
        `<tr id="ref_display_row_${pk}">
            <td id="ref_${pk}">${short}</td>
            <td>${title}</td>
            <td><i id="ref_delete_${pk}" class="icon btn btn-primary icon-delete ref_delete"></i></td>
        </tr>`
    )
    $('#id_ref').append(`<option id="ref_option_${pk}" value="${pk}" selected></option>`)
    $('.reference-search-appear').hide()
});

$("body").on("click",'.ref_delete', function(){
    pk = this.id.split('_')[2]
    ele = $(`#ref_option_${pk}`)
    if(ele.attr('selected')){
        ele.removeAttr('selected')
        $(`#ref_display_row_${pk} > td`).addClass('del')
    } else {
        ele.attr('selected','selected')
        $(`#ref_display_row_${pk} > td`).removeClass('del')
    }
});