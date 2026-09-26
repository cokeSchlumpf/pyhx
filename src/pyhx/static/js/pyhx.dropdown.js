/**
 * Auto-close single-select (radio) dropdowns on selection.
 *
 * Dropdowns are Pico `<details class="dropdown">` panels. Picking a radio fires a
 * native `change` (which the dropdown's own htmx binding uses to recompute the
 * summary label) but never closes the panel. For single-select that's wrong: one
 * pick is a complete choice, so collapse the panel immediately. Checkbox
 * (multi-select) dropdowns are left open on purpose — we only match radios.
 *
 * Pure presentation: we don't wait on the label round-trip; removing `open` runs
 * in parallel with the htmx swap, which targets the inner <summary> and is
 * unaffected by the wrapper's open state.
 *
 * The close is deferred to the next macrotask (setTimeout 0) on purpose. This
 * listener is registered at parse time, but htmx wires its own `change` handling
 * up later (on DOMContentLoaded), so at the document node ours would otherwise
 * fire first and collapse the panel before htmx serializes `hx-include` and sends
 * the label request — silently breaking the update. Deferring lets htmx finish
 * dispatching the change (and fire its XHR) before we touch the DOM; the panel
 * still collapses on the very next tick, so it reads as instant.
 */
document.addEventListener('change', (e) => {
    const radio = e.target.closest('details.dropdown input[type="radio"]');
    if (!radio) return;
    const details = radio.closest('details.dropdown');
    if (details) setTimeout(() => details.removeAttribute('open'), 0);
});
