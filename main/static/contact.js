$('.ContactModal').on('click', function(){
    $('#contact-modal').addClass('active')
});

$('#contact-modal-close').on('click', function(){
    $('#contact-modal').removeClass('active')
});

$(".addContact").on("click", function(){
    $.ajax({
        type: "POST",
        url: $('#ajax_add_contact').attr('data-url'),
        data: $("#contact-form").serialize(),
        }).done(function(data){
            $('#contact-list').append(
                `<tr>
                    <td id="ref_${data['pk']}">${data['name']}</td>
                    <td> <i id="contact_delete_${data['pk']}" class="icon btn btn-primary icon-delete contact_delete"></i></td>
                </tr>`
            )
            $('#id_contact').append(`<option value="${data['pk']}" selected></option>`)
        });
});

//Searching for contact
var searchContact = function( data ) {
    $.ajax({
        type: "post",
        url: $('#contact-search').attr("data-url"),
        data: {
            'keyword': data,
        },
        success: function(respond) {
            $('.contact-search-appear').html(
                `
                <table class="table table-striped table-hover">
                <thead>
                    <tr>
                    <th>Contact Person</th>
                    <th></th>
                    </tr>
                </thead>
                <tbody id='contact-search-tbody'>
                </tbody>
                </table>
                `

            )
            for (const [key, value] of Object.entries(respond)) {
                $('#contact-search-tbody').append(
                    `<tr>
                        <td id=search_name_${key}>${value}</td>
                        <td><span class='btn contact-search-item' id=search_result_${key}>Add</span></td>
                    </tr>
                    `
                )
            }
        }
    });
  }

$('#contact-search').on('keyup paste',function(){
    if(this.value.length >= 3)
        searchContact(this.value);
  });

$("body").on("click",'.contact-search-item', function(){
    pk = this.id.split('_')[2]
    contact_name = $(`#search_name_${pk}`).html()
    $('#contact-list').append(
        `<tr id="contact_display_row_${pk}">
            <td id="contact_${pk}">${contact_name}</td>
            <td><i id="contact_delete_${pk}" class="icon btn btn-primary icon-delete contact_delete"></i></td>
        </tr>`
    )
    $('#id_contact').append(`<option id="contact_option_${pk}" value="${pk}" selected></option>`)
});

$("body").on("click",'.contact_delete', function(){
    pk = this.id.split('_')[2]
    ele = $(`#contact_option_${pk}`)
    console.log(ele)
    if(ele.attr('selected')){
        ele.removeAttr('selected')
        $(`#contact_display_row_${pk} > td`).addClass('del')
    } else {
        ele.attr('selected','selected')
        $(`#contact_display_row_${pk} > td`).removeClass('del')
    }
});