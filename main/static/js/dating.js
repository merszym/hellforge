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

// mark dates as delete
$("body").on('click', '.date_delete', function(){
    pk = $(this).attr('id').split('_')[2]
    ele = $(`#date_option_${pk}`)
    if(ele.attr('selected')){
        ele.removeAttr('selected')
        $(`#date_display_row_${pk} > td`).addClass('del')
    } else {
        ele.attr('selected','selected')
        $(`#date_display_row_${pk} > td`).removeClass('del')
    }
});

// Validate the dating form
// what happens if uncal 14C is selected...
// show the required fields, hide the rest
$('body').on('change','#method',function(){
    if( this.value === '14C' ){
        $('#estimate_label').html('Radiocarbon Measurement')
        $('#range_label').html('Calibrated Date BP')
        $('.14c_group').show()
        $('.14c_hide').hide()
        $('.date_range').html("")
        $('#upper').prop('readonly', true);
        $('#lower').prop('readonly', true);
        $('#curve').prop('readonly', true);
    } else {
        $('#estimate_label').html('Point Estimate')
        $('#range_label').html('Range')
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
    $('#calibrate').removeClass('tooltip tooltip-left')
    $.ajax({
        type: "GET",
        url: `${$('#calibrate').attr('data-url')}?estimate=${estimate}&pm=${pm}`,
        }).done(function(data){
            console.log(data)
            if(data['status']){
                $('#curve').val(data['curve'])
                $('#upper').val(data['upper'])
                $('#lower').val(data['lower'])
                $('#calibrate').removeClass('loading')
                $('#calibrate').addClass('tooltip tooltip-left')
            } else {
                alert('Calibration went wrong, sorry')
            }
        });
});