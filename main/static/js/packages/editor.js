defaults = {
    'site': {
        "blocks":
        [
            {"id":1, "type": "header", "data": {"text": "Authors", "level": 5}},
            {"id":2, "type": "header", "data": {"text": "Description of the Site", "level": 2}},
            {"id":3, "type": "header", "data": {"text": "References", "level": 5}},
            {"id":4, "type": "list", "data": {"style": "unordered", "items": []}},
            {"id":5, "type": "header", "data": {"text": "Acknowledgements", "level": 5}},
        ], "version": "2.25.0"
    }
}

$.getJSON({
    url: $('#editorjs').attr("data-url"),
    success: function(response) {
        if (response.empty) {
            response = defaults[response.model]
        }
        const editor = new EditorJS({
            readOnly: $('#readonly').html() != 'False',
            placeholder: 'Start the Description here...',
            holder: 'editorjs',
            minHeight : 30,
            tools: {
                footnotes: {
                    class: FootnotesTune,
                },
                header: {
                    class: Header,
                    inlineToolbar: true,
                    config: {
                        placeholder: 'Header'
                    },
                 },
                image: {
                    class: ImageTool,
                    config: {
                      endpoints: {
                        byFile: $('#guide').attr('data-url'), // Your backend file uploader endpoint
                      }
                    }
                },
                list: {
                    class: List,
                    inlineToolbar: true,
                },
                marker: {
                    class:  Marker,
                },
                super: {
                    class: Superscript
                },
                reference: {
                    class: Reference
                },
                linkTool: LinkTool,
                table: {
                    class: Table,
                    inlineToolbar: true,
                },
            },
            tunes: ['footnotes'],
            data: response,
            onReady: () => {
                //load popups from references
                load_popups()
            }
        });
        // for read-only-mode
        if($('#saveButton').length){
            const saveButton = document.getElementById('saveButton');
            saveButton.addEventListener('click', function () {
            editor.save()
                .then((savedData) => {
                    // collect all the saved references and send them too
                    references = []
                    $('reference-tag').each(function(){
                        references.push($(this).attr('id'))
                    })
                    var reference_string = references.join(',')
                    formdata = new FormData()
                    formdata.append('references', reference_string)
                    formdata.append('data', JSON.stringify(savedData))
                    // and save the description
                    $.post({
                        processData: false,
                        contentType: false,
                        url: $('#description-save').attr("data-url"),
                        data: formdata,
                        success: function(respond){
                            window.location.replace(respond['redirect']);
                        }
                    });
                })
                .catch((error) => {
                    console.error('Saving error', error);
                });
            });
        }
    }
})
