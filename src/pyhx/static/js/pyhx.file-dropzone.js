class PyhxFileDropzone {
    constructor(root) {
        this.root = root;
        this.input = root.querySelector('[data-file-dropzone-input]');
        this.placeholder = root.querySelector('[data-file-dropzone-placeholder]');
        this.browseButton = root.querySelector('[data-file-dropzone-browse]');

        if (!this.input || !this.placeholder) return;

        this.defaultPlaceholder = this.placeholder.textContent;

        this.bind();
    }

    bind() {
        // A click anywhere on the root opens the native picker - including
        // the "Select File" button, which is a plain `type="button"` with no
        // native file-picking behaviour of its own. One delegated
        // listener handles every click target inside the box uniformly.
        this.root.addEventListener('click', (event) => {
            if (this.input.disabled) return;
            if (event.target === this.input) return;

            this.input.click();
        });

        this.input.addEventListener('change', () => {
            this.updatePlaceholder();
        });

        this.root.addEventListener('dragover', (event) => {
            if (this.input.disabled) return;
            // Required so `drop` fires at all - browsers treat a drop target
            // as invalid unless dragover's default (which rejects the drop)
            // is prevented.
            event.preventDefault();
            this.root.classList.add('is-drag-over');
        });

        this.root.addEventListener('dragleave', (event) => {
            // Only clear on leaving the root itself, not a child - dragleave
            // fires on every element the pointer passes over, including the
            // icon/text/button inside the box, which would otherwise flicker
            // the drag state off while still hovering the dropzone.
            if (event.target !== this.root) return;
            this.root.classList.remove('is-drag-over');
        });

        this.root.addEventListener('drop', (event) => {
            event.preventDefault();
            this.root.classList.remove('is-drag-over');
            if (this.input.disabled) return;

            const files = event.dataTransfer?.files;
            if (!files || files.length === 0) return;

            // Assigning `.files` directly (rather than re-uploading via JS)
            // keeps this a completely normal <input type="file"> as far as
            // any enclosing <form> - or htmx's multipart encoding - is
            // concerned. It doesn't fire `change` on its own, so that's
            // dispatched by hand to reuse the same placeholder-update path a
            // real picker selection takes.
            this.input.files = files;
            this.input.dispatchEvent(new Event('change', { bubbles: true }));
        });
    }

    updatePlaceholder() {
        const files = this.input.files;

        if (!files || files.length === 0) {
            this.placeholder.textContent = this.defaultPlaceholder;
            return;
        }

        this.placeholder.textContent = Array.from(files)
            .map((file) => file.name)
            .join(', ');
    }
}

// Track initialised dropzones on the node itself rather than a data-*
// attribute - see pyhx.wysiwyg-editor.js for why. A WeakSet keyed on the element survives
// attribute stripping, so a morph-preserved dropzone is initialised once.
const _pyhxFileDropzoneInitialized = new WeakSet();

function initPyhxFileDropzones(root = document) {
    root.querySelectorAll('[data-file-dropzone]').forEach((el) => {
        if (_pyhxFileDropzoneInitialized.has(el)) return;

        _pyhxFileDropzoneInitialized.add(el);
        new PyhxFileDropzone(el);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initPyhxFileDropzones();
});

document.addEventListener('htmx:afterSwap', (event) => {
    initPyhxFileDropzones(event.target);
});

document.addEventListener('htmx:load', (event) => {
    initPyhxFileDropzones(event.target);
});
