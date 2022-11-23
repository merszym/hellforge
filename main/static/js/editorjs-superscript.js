class Superscript {
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
        this.tag = 'SUP'; //needs to be upper case...
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
        const selectedText = range.extractContents();
        const sup = document.createElement(this.tag);
        // Append selected TextNode
        sup.classList.add(this.class);
        sup.appendChild(selectedText);
        // Insert new element
        range.insertNode(sup);
        this.api.selection.expandToTag(sup);
    }
    unwrap(range){
        const sup = this.api.selection.findParentTag(this.tag);
        this.api.selection.expandToTag(sup);
        let fullrange = window.getSelection().getRangeAt(0);
        const text = fullrange.extractContents();
        sup.remove();
        range.insertNode(text);
    }
    checkState() {
        const sup = this.api.selection.findParentTag(this.tag);
        this.state = !!sup;
    }
    get toolboxIcon() {
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"> <g> <path fill="none" d="M0 0h24v24H0z"/> <path d="M11 7v13H9V7H3V5h12v2h-4zm8.55-.42a.8.8 0 1 0-1.32-.36l-1.154.33A2.001 2.001 0 0 1 19 4a2 2 0 0 1 1.373 3.454L18.744 9H21v1h-4V9l2.55-2.42z"/> </g> </svg>'
    }
 }