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
$('body').on('click', '.generic_reload', function(){
    var element = $(this).attr('data-reload')
    $.ajax({
        url: document.URL,
        success: function(response) {
            // Find the element you want to load
            var update = $(response).find(`#${element}`);
            // Insert the element into the DOM
            $(`#${element}`).replaceWith(update)
        }
    });
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

// general style of
$('body').on('click','.tab-item', function(){
    if ($(this).hasClass('main')){
        $('.main').removeClass('active')
        $(this).addClass('active')
    }
    else{
        $('.minor').removeClass('active')
        $(this).addClass('active')
    }
});