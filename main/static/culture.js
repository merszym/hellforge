var searchCulture = function( data ) {
    $.ajax({
        type: "post",
        url: $('#culture-search').attr("data-url"),
        data: {
            'keyword': data,
        },
        success: function(respond) {
            if(Object.keys(respond).length === 0){
                cultureadd = $('#culture-search-appear').attr('data-url');
                $('.culture-search-appear').html(
                `<div style='padding:10px;'>
                    <a class="btn btn-primary btn tooltip" target="_blank" href="${cultureadd}" data-tooltip="Add Culture">
                        <i class="icon icon-plus"></i>
                    </a>
                </div>
                `
                )
            }
            else{
                $('.culture-search-appear').html(
                    `
                    <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                        <th>Culture</th>
                        <th></th>
                        </tr>
                    </thead>
                    <tbody id='culture-search-tbody'>
                    </tbody>
                    </table>
                    `
                )
                for (const [key, value] of Object.entries(respond)) {
                    $('#culture-search-tbody').append(
                        `<tr>
                        <td id=culture_search_val_${key}>${value}</td>
                        <td><span class='btn search-culture-item' id=culture_search_result_${key}>Take</span></td>
                        </tr>
                        `
                    )
                }
            }
        }
    });
  }

$('#culture-search').on('keyup paste',function(){
    if(this.value.length >= 3){
        searchCulture(this.value);
    }
  });

$("body").on("click",'.search-culture-item', function(){
    pk = this.id.split('_')[3]
    val = $(`#culture_search_val_${pk}`).html()
    $('#culture-list').html(
        `<tr>
            <td><strong>Culture:</strong></td>
            <td id="culture_${pk}">${val}</td>
        </tr>`
    )
    $('#culturelist').html(pk) // #TODO: Add to model
    $('.culture-search-appear').html('')
});