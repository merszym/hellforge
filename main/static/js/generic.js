//generic search function!
//search-input is handled by the specific data-url tag!
//make sure to have a csrf token ready
$('body').on('keyup paste','#search-input',function(){
    var model = $(this).attr('data-model') //data-model is the searched for model
    var origin = $(this).attr('data-origin') //data-for is the current model in search of model
    if ($(this).val().length === 0) {
        $(`.${model}-search-appear`).hide()
    }
    else {
        var formdata = new FormData();
        formdata.append('keyword', $(this).val());
        formdata.append('origin', origin)
        formdata.append('model', model)
        formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
        $.ajax({
            type: "POST",
            processData: false,
            contentType: false,
            data: formdata,
            url: $(this).attr("data-url"),
            success: function(html) {
                $(`.${model}-search-appear`).show()
                $(`.${model}-search-appear`).html(html)
            }
        });
    }
});

// generic reload of element, instead of rendering with html-snippets!
// get the webpage again by loading the same url, only bind the required element to the dom
function clickElement(element){
    $(`#${element}`).click()
}

function reloadElement(element){
    if(element==='location'){
        location.reload()
    }else{
        $.ajax({
            url: document.URL,
            success: function(response) {
                // Find the element you want to load
                var update = $(response).find(`#${element}`);
                // Insert the element into the DOM
                $(`#${element}`).replaceWith(update)
                //in case its hidden by default
                $(`#${element}`).show()
            }
        });
    }
}

$('body').on('click', '.generic_reload', function(){
    var element = $(this).attr('data-reload')
    reloadElement(element)
})


//load the project status button in each page
$(document).ready(function(){
    var element = $('#project_status_tile')
    $.ajax({
        url: element.attr('data-url'),
        success: function(html) {
            element.html(html)
        }
    });
});

// Generic Styling!
// for spectre elements

// general style of tab-items
$('body').on('click','.tab-item', function(){
    var group = $(this).attr('data-group')
    $(`.tab-item[data-group=${group}]`).removeClass('active')
    $(this).addClass('active')
});

//
// GENERIC ADD, REMOVE, DELETE
//

// generic delete --> add confirm class and remove it after 3 sec
$('body').on('click','.generic_delete', function(){
    $(this).addClass('generic_delete_confirm text-error')
    $(this).attr('data-tooltip', 'Confirm Delete!')
    var element = $(this).attr('data-x')
    setTimeout(function() {
        $('.generic_delete').attr('data-tooltip', `Delete ${element.split('_')[0]}`)
        $('.generic_delete').removeClass('generic_delete_confirm text-error')
    }, 2000);
})


$('body').on('click','.generic_delete_confirm', function(){
    var formdata = new FormData();
    var reload = $(this).attr('data-reload')
    var click = $(this).attr('data-click')
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $(this).attr('data-x'));
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $('#url_generic_delete').attr("data-url"),
        success: function() {
            if(click){
                clickElement(click)
            }else{
                reloadElement(reload)
            }
        }
    });
})

// generic m2m functions
// add

$('body').on('click', '.generic_addm2m', function(){
    var formdata = new FormData()
    var reload = $(this).attr('data-reload')
    var click = $(this).attr('data-click')
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $(this).attr('data-x'));
    formdata.append('instance_y', $(this).attr('data-y'));
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $('#url_generic_addm2m').attr('data-url'),
        success: function() {
            if(click){
                clickElement(click)
            }else{
                reloadElement(reload)
            }
        }
    });
});

//remove
$('body').on('click', '.generic_rmm2m', function(){
    var formdata = new FormData()
    var reload = $(this).attr('data-reload')
    var click = $(this).attr('data-click')
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $(this).attr('data-x'));
    formdata.append('instance_y', $(this).attr('data-y'));
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $('#url_generic_rmm2m').attr('data-url'),
        success: function() {
            if(click){
                clickElement(click)
            }else{
                reloadElement(reload)
            }
        }
    });
});