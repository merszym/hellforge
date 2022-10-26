$('.DateModal').on('click', function(){
    $('#dating-modal').addClass('active')
});

$('#dating-modal-close').on('click', function(){
    $('#dating-modal').removeClass('active')
});

$(".addDate").on("click", function(){
    $('#dating-modal').removeClass('active')
    $.ajax({
        type: "POST",
        url: $('#ajax_add_date').attr('data-url'),
        data: $("#dating-form").serialize(),
        }).done(function(data){
            $('#dating-list').append(
                `<tr><td id="date_${data['pk']}">${data['upper']}-${data['lower']}</td><td>${data['method']}</td><td></td></tr>`
            )
            $('#id_date').append(
                `<option value="${data['pk']}" selected></option>`
            )
        });
});
