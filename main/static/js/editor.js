site_default = {
    "blocks":
    [
        {"id":1, "type": "header", "data": {"text": "Authors", "level": 5}},
        {"id":2, "type": "header", "data": {"text": "Description of the Site", "level": 2}},
        {"id":3, "type": "header", "data": {"text": "References", "level": 5}},
        {"id":4, "type": "list", "data": {"style": "unordered", "items": []}},
        {"id":5, "type": "header", "data": {"text": "Acknowledgements", "level": 5}},
    ], "version": "2.25.0"
}

$.getJSON({
    url: $('#editorjs').attr("data-url"),
    success: function(respond) {
        if (respond.empty) {
            if (respond.model === 'site'){
                respond = site_default
            }
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
                linkTool: LinkTool,
                table: {
                    class: Table,
                    inlineToolbar: true,
                },
            },
            tunes: ['footnotes'],
            data: respond
        });

        const saveButton = document.getElementById('saveButton');

        saveButton.addEventListener('click', function () {
        editor.save()
            .then((savedData) => {
                $.post({
                    dataType:"json",
                    url: $('#description-save').attr("data-url"),
                    data: {'data': JSON.stringify(savedData)},
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
})