//Searching for Checkpoint
var relatedSearchFunction = function( data ) {
    $.ajax({
        type: "post",
        url: $('#related-search').attr("data-url"),
        data: {
            'keyword': data,
        },
        success: function(respond) {
            $('.related-search-appear').html(
                `
                <table class="table table-striped table-hover">
                <thead>
                    <tr>
                    <th>Related Layer</th>
                    <th>Site</th>
                    <th></th>
                    </tr>
                </thead>
                <tbody id='related-search-tbody'>
                </tbody>
                </table>
                `

            )
            for (const [key, value] of Object.entries(respond)) {
                $('#related-search-tbody').append(
                    `<tr>
                    <td id=related_${key}>${value.split(';;')[0]}</td>
                    <td id=related_site_${key}>${value.split(';;')[1]}</td>
                    <td><span class='btn related-search-item' id=related-search_result_${key}>Add</span></td>
                    </tr>
                    `
                )
            }
        }
    });
  }

$('#related-search').on('keyup paste',function(){
    if(this.value.length >= 3)
        relatedSearchFunction(this.value);
  });

$("body").on("click",'.related-search-item', function(){
    pk = this.id.split('_')[2]
    relname = $(`#related_${pk}`).html()
    site = $(`#related_site_${pk}`).html()
    $('#related-list').append(
        `<tr id=related_display_row_${pk}>
            <td id="related_${pk}">${relname}</td>
            <td>${site}</td>
            <td><i id="related_delete_${pk}" class="icon btn btn-primary icon-delete related_delete"></i></td>
        </tr>`
    )
    $('#id_related').append(
        `<option id=related_option_${pk} value="${pk}" selected></option>`
        )
});

// mark cp as delete
$("body").on('click', '.related_delete', function(){
    pk = $(this).attr('id').split('_')[2]
    ele = $(`#related_option_${pk}`)
    if(ele.attr('selected')){
        ele.removeAttr('selected')
        $(`#related_display_row_${pk} > td`).addClass('del')
    } else {
        ele.attr('selected','selected')
        $(`#related_display_row_${pk} > td`).removeClass('del')
    }
});