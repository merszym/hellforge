$("body").on("click", '.addDate', function(){
    $.ajax({
        type: "POST",
        url: $('#ajax_add_date').attr('data-url'),
        data: $("#modal-form").serialize(),
        }).done(function(data){
            if(data['status']){
                location.reload();
            } else {
                ele = $('#info')
                $('#modal-blank').html(data)
                $('#modal-form').append(ele)
            }
        });
});

// Validate the dating form
// what happens if uncal 14C is selected...
// show the required fields, hide the rest
$('body').on('change','#method',function(){
    //Reset the form
    $('.date_range').val('')
    $('.date_range').prop('disabled', false)
    $('.estimate_range').val('')
    $('.estimate_range').prop('disabled', false)
    if( this.value === '14C' ){
        $('.14c_group').show()
        $('.14c_hide').hide()
        $('#upper').prop('readonly', true);
        $('#lower').prop('readonly', true);
        $('#curve').prop('readonly', true);
    } else {
        $('.14c_group').hide()
        $('.14c_hide').show()
        $('#upper').prop('readonly', false);
        $('#lower').prop('readonly', false);
        $('#curve').prop('readonly', false);
    }
});

$('body').on('keyup paste','#estimate',function(){
    if($('#method').val() != '14C'){
        if(this.value.length > 0){
            $('#upper').prop('disabled', true);
            $('#lower').prop('disabled', true);
        } else  {
            $('#upper').prop('disabled', false);
            $('#lower').prop('disabled', false);
        }
    }
});
$('body').on('keyup paste','.date_range',function(){
    if($('#method').val() != '14C'){
        if(this.value.length > 0){
            $('#estimate').prop('disabled', true);
            $('#plusminus').prop('disabled', true);
        } else {
            $('#estimate').prop('disabled', false);
            $('#plusminus').prop('disabled', false);
        }
    }
});

$('body').on('click','#calibrate',function(){
    estimate = $('#estimate').val()
    pm = $('#plusminus').val()
    $('#calibrate').addClass('loading')
    $('#calibrate').removeClass('tooltip tooltip-right')
    $.ajax({
        type: "GET",
        url: `${$('#calibrate').attr('data-url')}?estimate=${estimate}&pm=${pm}`,
        }).done(function(data){
            $('#calibrate').removeClass('loading')
            $('#calibrate').addClass('tooltip tooltip-right')
            if(data['status']){
                $('#curve').val(data['curve'])
                $('#upper').val(data['upper'])
                $('#lower').val(data['lower'])
            } else {
                alert('Calibration failed. Fill BOTH fields of the 14C Measurement field')
            }
        });
});