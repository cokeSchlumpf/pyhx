const PYHX_WYSIWYG_SYNC_DELAY_MS = 500;

class PyhxWysiwygEditor {
    constructor(root) {
        this.root = root;
        this.input = root.querySelector('[data-wysiwyg-input]');
        this.hidden = root.querySelector('[data-wysiwyg-hidden]');
        this.buttons = root.querySelectorAll('[data-wysiwyg-command]');
        this.savedRange = null;

        if (!this.input || !this.hidden) return;

        this.bind();
        this.sync();
        this.updateToolbar();
    }

    bind() {
        this.buttons.forEach((button) => {
            button.addEventListener('mousedown', (event) => {
                event.preventDefault();
            });

            button.addEventListener('click', (event) => {
                event.preventDefault();

                const command = button.dataset.wysiwygCommand;
                if (!command) return;

                this.input.focus();
                this.restoreSelection();

                document.execCommand(command, false, null);

                this.saveSelection();
                this.sync();
                this.updateToolbar();
            });
        });

        this.input.addEventListener('input', () => {
            this.saveSelection();
            this.syncDebounced();
        });

        this.input.addEventListener('focus', () => {
            this.saveSelection();
        });

        this.input.addEventListener('blur', () => {
            this.sync();
            this.triggerRefresh();
        });

        this.input.addEventListener('keyup', () => {
            this.saveSelection();
            this.updateToolbar();
        });

        this.input.addEventListener('mouseup', () => {
            this.saveSelection();
            this.updateToolbar();
        });

        this.input.addEventListener('keydown', (event) => {
            this.handleKeydown(event);
        });

        this.input.addEventListener('paste', (event) => {
            this.handlePaste(event);
        });

        this.input.addEventListener('drop', (event) => {
            event.preventDefault();
        });

        document.addEventListener('selectionchange', () => {
            if (document.activeElement === this.input) {
                this.saveSelection();
                this.updateToolbar();
            }
        });
    }

    saveSelection() {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) return;

        const range = selection.getRangeAt(0);

        if (!this.input.contains(range.commonAncestorContainer)) return;

        this.savedRange = range.cloneRange();
    }

    restoreSelection() {
        if (!this.savedRange) return;

        const selection = window.getSelection();
        if (!selection) return;

        selection.removeAllRanges();
        selection.addRange(this.savedRange);
    }

    sync() {
        clearTimeout(this._syncTimer);
        this.hidden.value = this.input.innerHTML;
        this.dispatchSync();
    }

    syncDebounced() {
        this.hidden.value = this.input.innerHTML;

        clearTimeout(this._syncTimer);
        this._syncTimer = setTimeout(
            () => this.dispatchSync(),
            PYHX_WYSIWYG_SYNC_DELAY_MS,
        );
    }

    dispatchSync() {
        this.hidden.dispatchEvent(new Event('input', { bubbles: true }));
        this.hidden.dispatchEvent(new Event('change', { bubbles: true }));
    }

    triggerRefresh() {
        if (this.hidden.value === this.root.dataset.lastValue) return;

        this.root.dataset.lastValue = this.hidden.value;

        if (window.htmx) {
            htmx.trigger(this.hidden, 'wysiwyg-refresh');
        } else {
            this.hidden.dispatchEvent(new Event('wysiwyg-refresh', { bubbles: true }));
        }
    }

    handleKeydown(event) {
        if (event.key !== 'Tab') return;

        event.preventDefault();

        this.restoreSelection();

        if (event.shiftKey) {
            document.execCommand('outdent', false, null);
        } else {
            document.execCommand('indent', false, null);
        }

        this.saveSelection();
        this.sync();
        this.updateToolbar();
    }

    handlePaste(event) {
        event.preventDefault();

        const text = event.clipboardData.getData('text/plain');

        this.restoreSelection();
        document.execCommand('insertText', false, text);

        this.saveSelection();
        this.sync();
    }

    updateToolbar() {
        this.buttons.forEach((button) => {
            const command = button.dataset.wysiwygCommand;
            if (!command) return;

            let active = false;

            try {
                active = document.queryCommandState(command);
            } catch {
                active = false;
            }

            button.classList.toggle('is-active', active);
            button.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
    }
}

// Track initialised editors on the node itself rather than a data-* attribute.
// htmx's morph swap reconciles attributes against the server HTML (which carries
// no init marker), so a `data-wysiwyg-init` guard gets stripped on every morph,
// re-initialising the editor. Re-init re-runs the constructor's `sync()`, which
// dispatches `input`/`change` on the hidden field — and under live form
// validation that change re-triggers a morph, looping forever (and leaking a
// fresh set of listeners each pass). A WeakSet keyed on the element survives
// attribute stripping, so a morph-preserved editor is initialised exactly once.
const _pyhxWysiwygInitialized = new WeakSet();

function initPyhxWysiwygEditors(root = document) {
    root.querySelectorAll('[data-wysiwyg-editor]').forEach((el) => {
        if (_pyhxWysiwygInitialized.has(el)) return;

        _pyhxWysiwygInitialized.add(el);
        new PyhxWysiwygEditor(el);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initPyhxWysiwygEditors();
});

document.addEventListener('htmx:afterSwap', (event) => {
    initPyhxWysiwygEditors(event.target);
});