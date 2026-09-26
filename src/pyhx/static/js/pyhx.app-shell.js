/* declare TOOLTIP_URL; */

function init_tooltips(root = document) {
  root.querySelectorAll('[title]').forEach(el => {
    if (el.dataset.tooltip_configured) return;
    el.dataset.tooltip_configured = '1';

    el.addEventListener('mouseenter', () => {
      const label = el.getAttribute('title');
      htmx.ajax('POST', TOOLTIP_URL, { values: { label }, swap: 'none' });
    });
    el.addEventListener('mouseleave', () => {
      htmx.ajax('POST', TOOLTIP_URL, { values: { label: '' }, swap: 'none' });
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
    init_tooltips()
});

// Re-initialize when HTMX swaps content
document.addEventListener('htmx:afterSwap', (e) => {
    init_tooltips(e.target)
});


// ---------------------------------------------------------------------------
// HTMX error → notification
//
// Clones the hidden <template id="hx-notification__error-template"> rendered
// by the `notifications()` mount, fills its title/content text nodes, and
// prepends it to #hx-notifications. Works for both server-side errors
// (responseError) and client-side ones (sendError, timeout, swapError),
// including the case where the server itself is unreachable — no roundtrip
// is needed because the template is already in the DOM.
// ---------------------------------------------------------------------------

function showErrorNotification({title, content, appearance = 'danger', timeout = 6000}) {
    const tpl = document.getElementById('hx-notification__error-template');
    const container = document.getElementById('hx-notifications');
    if (!tpl || !container) return;

    const card = tpl.content.firstElementChild.cloneNode(true);
    card.classList.remove('hx-notification--danger');
    card.classList.add(`hx-notification--${appearance}`);
    card.querySelector('.hx-notification__title').textContent = title || '';
    card.querySelector('.hx-notification__content').textContent = content || '';

    container.prepend(card);
    if (window.feather) window.feather.replace();
    if (timeout) setTimeout(() => card.remove(), timeout);
}

document.addEventListener('htmx:responseError', (e) => {
    const xhr = e.detail.xhr;
    showErrorNotification({
        title: `Request failed (${xhr.status})`,
        content: xhr.statusText || 'The server returned an error.',
    });
});

document.addEventListener('htmx:sendError', () => {
    showErrorNotification({
        title: 'Connection lost',
        content: 'Could not reach the server. Check your network and try again.',
    });
});

document.addEventListener('htmx:timeout', () => {
    showErrorNotification({
        title: 'Request timed out',
        appearance: 'warning',
    });
});

document.addEventListener('htmx:swapError', () => {
    showErrorNotification({
        title: 'Render failed',
        content: 'The browser could not apply the server response.',
    });
});