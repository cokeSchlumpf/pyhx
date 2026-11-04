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

// Texts in the language of the page, from the template's data-text-*
// attributes; the English fallbacks apply when a page renders an older template.
function errorText(key, fallback) {
    const tpl = document.getElementById('hx-notification__error-template');
    return (tpl && tpl.dataset[key]) || fallback;
}

// A short plain-text answer is a message of the app for its users (e.g. why a
// request was refused); any other body (HTML, JSON, a trace) is never shown.
const MAX_MESSAGE_LENGTH = 300;

function responseMessage(xhr) {
    const type = (xhr.getResponseHeader('Content-Type') || '').toLowerCase();
    const text = (xhr.responseText || '').trim();
    if (!type.startsWith('text/plain') || !text || text.length > MAX_MESSAGE_LENGTH) return null;
    return text;
}

document.addEventListener('htmx:responseError', (e) => {
    const xhr = e.detail.xhr;
    showErrorNotification({
        title: errorText('textRequestFailed', 'Request failed ({status})').replace('{status}', xhr.status),
        content: responseMessage(xhr) || errorText('textServerError', 'The server returned an error.'),
    });
});

document.addEventListener('htmx:sendError', () => {
    showErrorNotification({
        title: errorText('textConnectionLost', 'Connection lost'),
        content: errorText('textConnectionLostDetail', 'Could not reach the server. Check your network and try again.'),
    });
});

document.addEventListener('htmx:timeout', () => {
    showErrorNotification({
        title: errorText('textTimeout', 'Request timed out'),
        appearance: 'warning',
    });
});

document.addEventListener('htmx:swapError', () => {
    showErrorNotification({
        title: errorText('textSwapFailed', 'Display failed'),
        content: errorText('textSwapFailedDetail', 'The browser could not apply the server response.'),
    });
});
