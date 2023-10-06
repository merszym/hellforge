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
        //create empty <reference-tag> tag
        //const ref = document.createElement(this.tag);
        const api = this.api
        $.ajax({
            type: "GET",
            url: $('#reference-modal-get').attr('data-url'),
            }).done(function(html){
                $('#reference-modal').addClass('active')
                $('#reference-modal-content').html(html)
                $('#search-input').focus()
                $('body').off('click', '.editorjs-search-item').on('click', '.editorjs-search-item', function () {
                    //this is to wrap the selected text
                    const ref = document.createElement('reference-tag');
                    let selectedText = range.extractContents();
                    // this is to prevent that references get inserted into references
                    // happend by some weird js functionality that I dont understand...
                    if($(selectedText).find('reference-tag').length == 0){
                        // this gets the id of the selected reference
                        const id = $(this).attr('id').split('_')[1]
                        // close the modal
                        $('#reference-search-appear').html("")
                        $('#reference-modal').removeClass('active')
                        //give the <reference-tag> an id attr
                        $(ref).attr('id',id)
                        $(ref).addClass('reference')

                        // Append selected TextNode
                        $(ref).html(selectedText);
                        range.insertNode(ref);
                        // Insert new element
                        api.selection.expandToTag(ref);
                    }

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
        });
     }
 }


