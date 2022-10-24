var searchepoch = function( data ) {
    $.ajax({
        type: "post",
        url: $('#epoch-search').attr("data-url"),
        data: {
            'keyword': data,
        },
        success: function(respond) {
            if(Object.keys(respond).length === 0){
                epochadd = $('#epoch-search-appear').attr('data-url');
                $('.epoch-search-appear').html(
                `<div style='padding:10px;'>
                    <a class="btn btn-primary btn tooltip" target="_blank" href="${epochadd}" data-tooltip="Add epoch">
                        <i class="icon icon-plus"></i>
                    </a>
                </div>
                `
                )
            }
            else{
                $('.epoch-search-appear').html(
                    `
                    <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                        <th>epoch</th>
                        <th></th>
                        </tr>
                    </thead>
                    <tbody id='epoch-search-tbody'>
                    </tbody>
                    </table>
                    `
                )
                for (const [key, value] of Object.entries(respond)) {
                    $('#epoch-search-tbody').append(
                        `<tr>
                        <td id=epoch_search_val_${key}>${value}</td>
                        <td><span class='btn search-epoch-item' id=epoch_search_result_${key}>Take</span></td>
                        </tr>
                        `
                    )
                }
            }
        }
    });
  }

$('#epoch-search').on('keyup paste',function(){
    if(this.value.length >= 3){
        searchepoch(this.value);
    }
  });

$("body").on("click",'.search-epoch-item', function(){
    pk = this.id.split('_')[3]
    val = $(`#epoch_search_val_${pk}`).html()
    $('#epoch-list').html(
        `<tr><td id="epoch_${pk}">${val}</td><td>-</td></tr>`
    )
    $('#epochlist').html(pk) // #TODO: Add to model
    $('.epoch-search-appear').html('')
});