/**
 * FilterDrawer URL param sync
 *
 * When a FilterDrawer is constructed with `url_param_keys`, its Apply/Clear
 * responses carry two headers: `HX-Url-Param-Keys` (the full set of tracked
 * keys, always) and `HX-Url-Params` (a query string of whichever of those
 * keys currently have a value). This mirrors just those keys into the
 * browser's address bar via `history.replaceState` leaving every other URL param untouched.
 */
document.addEventListener('htmx:afterSwap', (evt) => {
    const xhr = evt.detail.xhr;
    if (!xhr) return;

    const keys = xhr.getResponseHeader('HX-Url-Param-Keys');
    if (keys === null) return;

    const values = new URLSearchParams(xhr.getResponseHeader('HX-Url-Params') || '');
    const url = new URL(window.location.href);
    for (const key of keys.split(',')) {
        if (values.has(key)) {
            url.searchParams.set(key, values.get(key));
        } else {
            url.searchParams.delete(key);
        }
    }
    history.replaceState(history.state, '', url);
});
