// open a reference search-window and add it from the backend

class Reference {
    static get sanitize() {
        return {
          'reference-tag': true
        }
    }
    static get isInline() {
        return true;
    }
    get state() {
        return this._state;
    }
    set state(state) {
        this._state = state;
        this.button.classList.toggle(this.api.styles.inlineToolButtonActive, state);
    }
    constructor({api}) {
        this.api = api;
        this.button = null;
        this._state = false;
        this.tag = 'REFERENCE-TAG'; //needs to be upper case...
    }
    render() {
        this.button = document.createElement('button');
        this.button.type = 'button';
        this.button.classList.add(this.api.styles.inlineToolButton)
        this.button.innerHTML = this.toolboxIcon;
        return this.button;
    }
    surround(range) {
        if (this.state) {
            this.unwrap(range);
            return;
        }
        this.wrap(range);
    }
    wrap(range){
        const ref = document.createElement(this.tag);
        const api = this.api
        $.ajax({
            type: "GET",
            url: $('#reference-modal-get').attr('data-url'),
            }).done(function(html){
                $('#reference-modal').addClass('active')
                $('#reference-modal-content').html(html)
                $('#ref-search').focus()
                $('body').off().on('click','.search-item' ,function(){
                    const selectedText = range.extractContents();
                    const id = $(this).attr('id').split('_')[2]
                    $('#search-appear').html("")
                    $('#reference-modal').removeClass('active')
                    // Render the modal, wait until click of
                    ref.id = id
                    ref.classList.add('reference')
                    // Append selected TextNode
                    ref.appendChild(selectedText);
                    range.insertNode(ref);
                    // Insert new element
                    api.selection.expandToTag(ref);
                    //save the reference to the site? --> Works, but is it necessary?? Better compile a list of references at the end
                    /*
                    const formdata = new FormData()
                    const site = window.location.pathname.split('/').pop()
                    formdata.append('model','site')
                    formdata.append('modelpk', site)
                    formdata.append('pk', id)
                    formdata.append('csrfmiddlewaretoken', $('[name=csrfmiddlewaretoken]').val())
                    $.ajax({
                        type: "POST",
                        processData: false,
                        contentType: false,
                        data: formdata,
                        url: `${$('#reference-add').attr('data-url')}?pk=${id}`,
                        })
                    */
                })
            });
    }
    unwrap(range){
        const ref = this.api.selection.findParentTag(this.tag);
        this.api.selection.expandToTag(ref);
        let fullrange = window.getSelection().getRangeAt(0);
        const text = fullrange.extractContents();
        ref.remove();
        range.insertNode(text);
    }
    checkState() {
        const ref = this.api.selection.findParentTag(this.tag);
        this.state = !!ref;
    }
    get toolboxIcon() {
        return `DOI`
    }
 }

 // for each <reference-tag> in the description: include a reference-popup
 // gets executed in the onReady handle of editor.js
 // only if readonly
 function load_popups(){
    if ($('#readonly').html() != 'False') {
        done = []
        $('reference-tag').each(function(){
            $('#description-references').show()
            const tag = $(this)
            const pk = tag.attr('id')
            const text = tag.html()
            $.ajax({
                type: "GET",
                url: `${$('#reference-popup-get').attr('data-url')}?pk=${pk}&title=${text}`,
                }).done(function(html){
                    tag.html(html)
                });
            if (done.includes(pk)==false){
                done.push(pk)
                $.ajax({
                    type: "GET",
                    url: `${$('#reference-row-get').attr('data-url')}?pk=${pk}`,
                    }).done(function(html){
                        $('#description-reference-tbody').append(html)
                    });
                }
        });
     }
 }


