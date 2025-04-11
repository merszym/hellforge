// This is all related to the person-list view

$("body").on('click', '.tr_click', function(){
    var id = $(this).attr('id').split('_')[1]
    $(".person_form").hide()
    $(`#person_form_${id}`).show()
});

$('#contact-list-search').on("keyup paste", function() {
    var value = $("#contact-list-search").val().toLowerCase();
    $("tr").filter(function() {
        if($(this).text().toLowerCase().indexOf(value) > -1){
            $(this).show()
        } else {
            $(this).hide()
        }
    });
});

// Update a Persons personal information
$("body").on('click', '.update_person', function(){
    var id = $(this).attr('data-x').split('_')[1]
    var form = $(`#formdata_${id}`)[0];

    var formdata = new FormData(form);
    formdata.append('instance_x', $(this).attr('data-x')); //Person

    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        url: $(this).attr('data-url'),
        data: formdata,
        }).done(function(){
            reloadElement(`trperson_${id}`)
            reloadElement(`person_form_${id}`)
        });
})

//Add a person from the search String
$('body').on('click','#create_person_from_string', function(){
    var formdata = new FormData();
    var search_string = $("#contact-list-search").val()
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('person_search', search_string)

    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $(this).attr("data-url"),
        success: function(data) {
            // do right later
            location.reload()
        }
    });
});
