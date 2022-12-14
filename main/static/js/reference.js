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

//Searching for references
var searchFunction = function( data ) {
    var form_data = new FormData();
    form_data.append('keyword', data);
    form_data.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: form_data,
        url: $('#ref-search').attr("data-url"),
        success: function(respond) {
            $('.search-appear').show()
            $('.search-appear').html(
                `
                <table class="table table-striped table-hover">
                <thead>
                    <tr>
                    <th>Reference</th>
                    <th></th>
                    <th></th>
                    </tr>
                </thead>
                <tbody id='search-tbody'>
                </tbody>
                </table>
                `

            )
            for (const [key, value] of Object.entries(respond)) {
                $('#search-tbody').append(
                    `<tr>
                    <td id=search_short_${key}>${value.split(';;')[0]}</td>
                    <td id=search_title_${key}>${value.split(';;')[1]}</td>
                    <td><span class='btn search-item' id=search_result_${key}>Add</span></td>
                    </tr>
                    `
                )
            }
        }
    });
  }

$('#ref-search').on('keyup paste',function(){
    if(this.value.length >= 3)
        searchFunction(this.value);
  });

$("body").on("click",'.search-item', function(){
    pk = this.id.split('_')[2]
    short = $(`#search_short_${pk}`).html()
    title = $(`#search_title_${pk}`).html()
    $('#reference-list').append(
        `<tr id="ref_display_row_${pk}">
            <td id="ref_${pk}">${short}</td>
            <td>${title}</td>
            <td><i id="ref_delete_${pk}" class="icon btn btn-primary icon-delete ref_delete"></i></td>
        </tr>`
    )
    $('#id_ref').append(`<option id="ref_option_${pk}" value="${pk}" selected></option>`)
    $('.search-appear').hide()
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