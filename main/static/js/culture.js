var searchCulture = function( data ) {
    $.ajax({
        type: "post",
        url: $('#culture-search').attr("data-url"),
        data: {
            'keyword': data,
        },
        success: function(response) {
            if(Object.keys(response).length === 0){
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
                for (const [key, value] of Object.entries(response)) {
                    $('#culture-search-tbody').append(
                        `<tr><td>${value}</td><td><span class='btn search-culture-item' id=${key}>Pick</span></td></tr>`
                    )
                }
            }
        }
    });
  }

$('body').on('keyup paste','#culture-search',function(){
    if(this.value.length >= 3){
        searchCulture(this.value);
    }
  });

