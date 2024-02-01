// Validate the dating form
// what happens if uncal 14C is selected...
// show the required fields, hide the rest
// #TODO: get fresh from backend on change...
$('body').on('change','#method',function(){
    //Reset the form
    $('.date_range').val('')
    $('.date_range').prop('disabled', false)
    $('.estimate_range').val('')
    $('.estimate_range').prop('disabled', false)
    if( this.value === '14C' ){
        $('.14c_group').show()
        $('.14c_hide').hide()
    } else {
        $('.14c_group').hide()
        $('.14c_hide').show()
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

// Handle batch upload or download of dates for a site or layer
// download header
$('body').on('click','.get-batch-header', function(){
    $.ajax({
        type: "GET",
        url: $(this).attr('data-url'),
        }).done(function(text){
            var element = document.createElement('a');
            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
            element.setAttribute('download', 'header.csv');
            element.style.display = 'none';
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
          });
})


// Handle the upload file
$('body').on('change','#date-batch-input', function(){
    var file_data = $('#date-batch-input').prop('files')[0];
    var form_data = new FormData();
    form_data.append('file', file_data);
    form_data.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    form_data.append('instance_x', $('[name=info]').val())
    $.ajax({
        type: "POST",
        url: $(this).attr('data-url'),
        processData: false,
        contentType: false,
        data: form_data
        }).done(function(html){
            $('#dating-content').html(html)
        });
})

// Handle verification of the upload table
$('body').on('click', '#dating-table-confirm', function(){
    $('#dating-table-confirm').addClass('loading')
    $.ajax({
        type: "POST",
        url: $('#dating-table-confirm').attr('data-url'),
        data: $('#date-batch-verify-form').serialize()
        }).done(function(data){
            if(data['status']){
                location.reload()
            }
        });
})

//recalibrate
$('body').on('change','.14c-curve-select', function(){
    var form_data = new FormData();
    form_data.append('instance_x',`${$(this).attr('id')}`);
    form_data.append('curve', `${$(this).val()}`)
    form_data.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    $.ajax({
        type: "POST",
        url: $(this).attr('data-url'),
        processData: false,
        contentType: false,
        data: form_data
        }).done(function(){
            $('#reload').click()
        });
})