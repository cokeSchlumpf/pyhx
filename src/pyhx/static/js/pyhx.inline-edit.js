/**
 * Inline edit (`InlineEdit`): open, cancel, keys and focus.
 *
 * The edit button loads the form into its item (`hx-swap="beforeend"`); a
 * valid save replaces the item out of band, a failed save morphs the form.
 * This script only does what the server can't:
 *
 * - When a form opens, it cancels the open form of the same group (the
 *   nearest ancestor with `data-hx-inline-edit-group`, else the page) and
 *   focuses the first control.
 * - Esc cancels, Enter on a select saves (Enter in a text field submits
 *   natively). Both are handled by a listener on the form, never on the
 *   document, so other key handlers on the page are not affected.
 * - Cancel removes the form without a request and returns the focus to the
 *   item's edit button; after a save the focus goes to the new item's edit
 *   button, after a failed save to the first invalid control.
 */
(() => {
    const ITEM = '.hx-inline-edit';
    const FORM = '.hx-inline-edit__form';
    const EDIT = '.hx-inline-edit__edit';
    const CONTROL = 'input:not([type="hidden"]), select, textarea';

    const bound = new WeakSet();
    // Id of the item that was saved, whose edit button gets the focus once
    // the server's new item is swapped in.
    let focusAfterSave = null;

    const groupOf = (item) =>
        item.parentElement?.closest('[data-hx-inline-edit-group]') ?? document;

    const close = (form, { focus }) => {
        const item = form.closest(ITEM);
        form.remove();
        if (focus) item?.querySelector(EDIT)?.focus();
    };

    const bind = (form) => {
        if (bound.has(form)) return;
        bound.add(form);
        const item = form.closest(ITEM);

        form.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                event.preventDefault();
                close(form, { focus: true });
            } else if (event.key === 'Enter' && event.target.tagName === 'SELECT') {
                event.preventDefault();
                form.requestSubmit();
            }
        });

        form.addEventListener('click', (event) => {
            if (event.target.closest('[data-hx-inline-edit-cancel]')) {
                close(form, { focus: true });
            }
        });

        form.addEventListener('htmx:beforeRequest', () => {
            focusAfterSave = item?.id ?? null;
        });

        form.addEventListener('htmx:afterRequest', () => {
            // Still in the page: the save failed and the form was morphed.
            if (!form.isConnected) return;
            focusAfterSave = null;
            (form.querySelector('[aria-invalid="true"]') ?? form.querySelector(CONTROL))?.focus();
        });
    };

    const open = (form) => {
        const item = form.closest(ITEM);
        if (!item) return;
        const group = groupOf(item);
        group.querySelectorAll(FORM).forEach((other) => {
            if (other !== form && groupOf(other.closest(ITEM)) === group) {
                close(other, { focus: false });
            }
        });
        bind(form);
        form.querySelector(CONTROL)?.focus();
    };

    document.addEventListener('htmx:load', (event) => {
        const elt = event.detail.elt;
        if (!(elt instanceof Element)) return;

        if (elt.matches(FORM)) {
            open(elt);
        } else if (elt.matches(ITEM) && elt.id === focusAfterSave) {
            focusAfterSave = null;
            elt.querySelector(EDIT)?.focus();
        }
    });
})();
