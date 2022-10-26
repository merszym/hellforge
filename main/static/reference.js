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
    $.ajax({
        type: "post",
        url: $('#ref-search').attr("data-url"),
        data: {
            'keyword': data,
        },
        success: function(respond) {
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
    console.log($('#id_ref'))
    pk = this.id.split('_')[2]
    short = $(`#search_short_${pk}`).html()
    title = $(`#search_title_${pk}`).html()
    $('#reference-list').append(
        `<tr><td id="ref_${pk}">${short}</td><td>${title}</td><td>-</td></tr>`
    )
    $('#id_ref').append(`<option value="${pk}" selected></option>`)
});
