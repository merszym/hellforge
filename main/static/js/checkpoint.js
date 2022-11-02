//Searching for Checkpoint
var cpSearchFunction = function( data ) {
    $.ajax({
        type: "post",
        url: $('#cp-search').attr("data-url"),
        data: {
            'keyword': data,
        },
        success: function(respond) {
            $('.cp-search-appear').html(
                `
                <table class="table table-striped table-hover">
                <thead>
                    <tr>
                    <th>Checkpoint</th>
                    <th>Type</th>
                    <th></th>
                    </tr>
                </thead>
                <tbody id='cp-search-tbody'>
                </tbody>
                </table>
                `

            )
            for (const [key, value] of Object.entries(respond)) {
                $('#cp-search-tbody').append(
                    `<tr>
                    <td id=cp_${key}>${value.split(';;')[0]}</td>
                    <td id=cp_type_${key}>${value.split(';;')[1]}</td>
                    <td><span class='btn cp-search-item' id=cp-search_result_${key}>Add</span></td>
                    </tr>
                    `
                )
            }
        }
    });
  }

$('#cp-search').on('keyup paste',function(){
    if(this.value.length >= 3)
        cpSearchFunction(this.value);
  });

$("body").on("click",'.cp-search-item', function(){
    pk = this.id.split('_')[2]
    cpname = $(`#cp_${pk}`).html()
    type = $(`#cp_type_${pk}`).html()
    $('#cp-list').append(
        `<tr id=cp_display_row_${pk}>
            <td id="cp_${pk}">${cpname}</td>
            <td>${type}</td>
            <td><i id="cp_delete_${pk}" class="icon btn btn-primary icon-delete cp_delete"></i></td>
        </tr>`
    )
    $('#id_checkpoint').append(
        `<option id=cp_option_${pk} value="${pk}" selected></option>`
        )
});

// mark cp as delete
$("body").on('click', '.cp_delete', function(){
    pk = $(this).attr('id').split('_')[2]
    ele = $(`#cp_option_${pk}`)
    if(ele.attr('selected')){
        ele.removeAttr('selected')
        $(`#cp_display_row_${pk} > td`).addClass('del')
    } else {
        ele.attr('selected','selected')
        $(`#cp_display_row_${pk} > td`).removeClass('del')
    }
});