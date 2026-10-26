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

// Generic Styling!
// for spectre elements

// general style of tab-items
$('body').on('click','.tab-item', function(){
    var group = $(this).attr('data-group')
    $(`.tab-item[data-group=${group}]`).removeClass('active')
    $(this).addClass('active')
    //change the tab
    $(`.tab-panel[data-group=${group}]`).hide()
    $(`#${$(this).attr("data-show")}`).show()
    $(`.${$(this).attr("data-show")}`).show()
});

// generic modal handling
$('body').on('click','.modal_open', function(){
    var element = $("#modal-blank")
    element.addClass('active')
});
$('body').on('click','.modal_close', function(){
    $('.modal.active').removeClass('active')
});

//
// GENERIC ADD, REMOVE, DELETE
//

function postGen(click, reload){
    if(click){
        clickElement(click)
    }else{
        $.each(reload.split(','), function(i,val){
            reloadElement(val)
        });
    }
}

//
// A generic form and instance_y function
//
$('body').on('click', '.generic_form', function(){
    // specify the form id with data-form
    var form = $(`#${$(this).attr('data-form')}`)
    var formdata = new FormData(form[0]);
    var reload = $(this).attr('data-reload')
    var click = $(this).attr('data-click')
    formdata.append('instance_x',$(this).attr('data-x'));
    formdata.append('instance_y',$(this).attr('data-y'));
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    $.ajax({
        type: "POST",
        url: $(this).attr('data-url'),
        processData: false,
        contentType: false,
        data: formdata
        }).done(function(){
            postGen(click, reload)
        });
});


//
// A generic instance_x and instance_y function
//

$('body').on('click', '.generic_xy', function(){
    var formdata = new FormData();
    var reload = $(this).attr('data-reload')
    var click = $(this).attr('data-click')
    formdata.append('instance_x',$(this).attr('data-x'));
    formdata.append('instance_y',$(this).attr('data-y'));
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    $.ajax({
        type: "POST",
        url: $(this).attr('data-url'),
        processData: false,
        contentType: false,
        data: formdata
        }).done(function(){
            postGen(click, reload)
        });
});


// generic delete --> hide the element after delete request
// in case the one hx-target isnt enough...
$('body').on('click','.generic_delete', function(){
    var tohide = $(this).attr('data-hide')
    if (tohide == 'reload'){
        location.reload()
    }
    else {
        $.each(tohide.split(','), function(i,val){
            $(`#${val}`).hide()
        });
    }
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
            postGen(click, reload)
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
            postGen(click, reload)
        }
    });
});

//Foreign Key relationships
//set
$('body').on('click', '.generic_setfk', function(){
    var formdata = new FormData()
    var reload = $(this).attr('data-reload')
    var click = $(this).attr('data-click')
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    if ($(this).attr('data-y-select')){ // for cases, were the object comes from an options select form field
        formdata.append('instance_y', $(`[name=${$(this).attr('data-y-select')}]`).val());
    }else{
        formdata.append('instance_y', $(this).attr('data-y'));
    }
    formdata.append('instance_x', $(this).attr('data-x'));

    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $('#url_generic_setfk').attr('data-url'),
        success: function() {
            postGen(click, reload)
        }
    });
});

//unset
$('body').on('click', '.generic_unsetfk', function(){
    var formdata = new FormData()
    var reload = $(this).attr('data-reload')
    var click = $(this).attr('data-click')
    formdata.append('csrfmiddlewaretoken',$('[name=csrfmiddlewaretoken]').val())
    formdata.append('instance_x', $(this).attr('data-x'));
    formdata.append('field', $(this).attr('data-y'));
    $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: formdata,
        url: $('#url_generic_unsetfk').attr('data-url'),
        success: function() {
            postGen(click, reload)
        }
    });
});

// add URL params

function add_url_params(kwargs) {
    let url = new URL(location.href);
    Object.entries(kwargs).forEach((entry) => {
        url.searchParams.set(entry[0], entry[1]);
    });
    window.history.pushState({}, "", url);
}

function delete_url_params(entry) {
    let url = new URL(location.href);
    url.searchParams.delete(entry);
    window.history.pushState({}, "", url);
}

// copy to clipboard
function copyClipboard(text) {
    navigator.clipboard.writeText(text);
}