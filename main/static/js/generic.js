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

//generic filter function
$('body').on('click', '.generic_filter', function(){
    console.log($(this).attr("data-term"))
    var term = $(this).attr('data-term').toLowerCase()
    var search = $(this).attr('data-search')
    $(search).filter(function() {
        if($(this).text().toLowerCase().indexOf(term) > -1){
            $(this).show()
        } else {
            $(this).hide()
        }
    });

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
    var element = $(`#${$(this).attr('data-open')}`)
    console.log(element)
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
            postGen(click, reload)
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
