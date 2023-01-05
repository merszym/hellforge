//generic search function!
//search-input is handled by the specific data-url tag!
//make sure to have a csrf token ready
$('body').on('keyup paste','#search-input',function(){
    var formdata = new FormData();
    formdata.append('keyword', $(this).val());
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $(this).attr("data-url"),
        success: function(html) {
            $('.search-appear').show()
            $('.search-appear').html(html)
        }
    });
});