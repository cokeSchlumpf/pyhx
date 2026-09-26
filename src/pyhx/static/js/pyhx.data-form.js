/**
 * DataForm live-validation bridge.
 *
 * DataForm revalidates by listening for `change`/`input`/`focusout` events that
 * bubble up from named fields inside the form (see data_form.py). The drawer
 * pickers (drawer_radio, drawer_select) commit their value via an htmx
 * out-of-band swap of the on-page control — and OOB swaps replace DOM nodes
 * silently, without firing a `change` event. So the value updates but validation
 * never re-runs.
 *
 * This bridges the gap: when a control marked `data-pyhx-revalidate="<field>"` is
 * swapped in, dispatch a bubbling native `change` from its field input, so the
 * enclosing form revalidates exactly as if a native <select> had changed.
 */
function pyhxNotifyRevalidate(root) {
    if (!root || !root.querySelectorAll) return;

    const controls = [];
    if (root.matches && root.matches('[data-pyhx-revalidate]')) controls.push(root);
    root.querySelectorAll('[data-pyhx-revalidate]').forEach((el) => controls.push(el));

    controls.forEach((el) => {
        const field = el.getAttribute('data-pyhx-revalidate');
        // Prefer the real field input (so DataForm's `_trigger` marks the field
        // touched); fall back to any named input (e.g. the config-json hidden
        // input) when the value was cleared and the field input is absent.
        const target =
            (field && el.querySelector(`input[name="${CSS.escape(field)}"]`)) ||
            el.querySelector('input[name]');
        if (target) target.dispatchEvent(new Event('change', { bubbles: true }));
    });
}

document.addEventListener('htmx:afterSwap', (e) => pyhxNotifyRevalidate(e.target));
document.addEventListener('htmx:oobAfterSwap', (e) =>
    pyhxNotifyRevalidate(e.detail && e.detail.target ? e.detail.target : e.target),
);
