$.getJSON({
    url: $('#editorjs').attr("data-url"),
    success: function(respond) {
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
                $.ajax({
                    type: "post",
                    url: $('#description-save').attr("data-url"),
                    data: JSON.stringify(savedData).trim(),
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