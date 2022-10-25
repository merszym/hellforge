//Searching for Checkpoint
var searchFunction = function( data ) {
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
        searchFunction(this.value);
  });

$("body").on("click",'.cp-search-item', function(){
    pk = this.id.split('_')[2]
    cpname = $(`#cp_${pk}`).html()
    type = $(`#cp_type_${pk}`).html()
    $('#cp-list').append(
        `<tr><td id="ref_${pk}">${cpname}</td><td>${type}</td><td></td></tr>`
    )
    $('#checkpointlist').html($('#checkpointlist').html()+','+pk)
});
