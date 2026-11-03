/**
 * Dialog behaviour shared by every page template (see dialog.css):
 *
 * - While the dialog is open, every other child of <body> is inert, except the
 *   drawers and the notifications: a drawer opened from the dialog works
 *   above it. On close, only the `inert` set here is removed again.
 * - When the dialog opens, focus moves to the element with `autofocus` in it,
 *   or to the dialog; when it closes, focus returns to the element that had it
 *   before, or to the page's <main>. When an answer replaces the content,
 *   focus is put back into the dialog if it left it.
 * - Escape clicks the dialog's close button, only when the dialog has one and
 *   no drawer is open above it (pyhx.drawer.js closes that drawer first). A
 *   click on the backdrop does nothing.
 * - The browser never closes the dialog on its own (`cancel`), and the dialog's
 *   form is never submitted natively: every action is an htmx request.
 */
(() => {
    const KEEP = '.hx-dialog, .hx-drawer, .hx-notifications, template, script';

    const dialogOf = (mount) => mount.querySelector(':scope > dialog');
    const isOpen = (mount) => !!dialogOf(mount)?.hasAttribute('open');
    const isDrawerOpen = () => [...document.querySelectorAll('.hx-drawer')]
        .some((drawer) => drawer.querySelector(':scope > aside > section > *'));

    const focusInto = (dialog) => {
        (dialog.querySelector('[autofocus]') ?? dialog).focus({ preventScroll: true });
    };

    const focusMain = () => {
        const main = document.querySelector('main');
        if (!main) return;
        if (!main.hasAttribute('tabindex')) main.setAttribute('tabindex', '-1');
        main.focus({ preventScroll: true });
    };

    const state = new WeakMap(); // mount -> {open, returnTo, inerted}

    const sync = (mount) => {
        const before = state.get(mount) ?? { open: false, returnTo: null, inerted: [] };
        const dialog = dialogOf(mount);
        const now = isOpen(mount);
        const active = document.activeElement;

        if (now && before.open) {
            // New content in the open dialog (e.g. an error after an answer).
            const focusLeft = !active || active === document.body
                || (!dialog.contains(active) && !active.closest('.hx-drawer'));
            if (focusLeft) focusInto(dialog);
            return;
        }
        if (now === before.open) return;

        if (now) {
            const returnTo = active && active !== document.body && !mount.contains(active) ? active : null;
            const inerted = [...document.body.children].filter((el) => !el.matches(KEEP) && !el.inert);
            inerted.forEach((el) => { el.inert = true; });
            state.set(mount, { open: true, returnTo, inerted });
            focusInto(dialog);
        } else {
            before.inerted.forEach((el) => { el.inert = false; });
            state.set(mount, { open: false, returnTo: null, inerted: [] });
            const focusLost = !document.activeElement || document.activeElement === document.body
                || mount.contains(document.activeElement);
            if (!focusLost) return;
            if (before.returnTo?.isConnected && !before.returnTo.closest('[inert]')) {
                before.returnTo.focus({ preventScroll: true });
            } else {
                focusMain();
            }
        }
    };

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape' || e.defaultPrevented) return;
        // An open dropdown (<details>) in the dialog closes first.
        if (e.target.closest?.('details[open]')) return;
        // A drawer above the dialog closes first (pyhx.drawer.js), whatever
        // the order of the two listeners.
        if (isDrawerOpen()) return;
        const mount = [...document.querySelectorAll('.hx-dialog')].find(isOpen);
        if (!mount) return;
        e.preventDefault();
        // A required dialog has no close button: Escape does nothing.
        const button = mount.querySelector('[data-hx-dialog-close]');
        if (button && !button.disabled) button.click();
    });

    // `cancel` doesn't bubble: listen in the capture phase.
    document.addEventListener('cancel', (e) => {
        if (e.target.closest?.('.hx-dialog')) e.preventDefault();
    }, true);

    // Enter in a field without a submit button would submit the form natively
    // and load the page again; actions are htmx requests on their buttons.
    document.addEventListener('submit', (e) => {
        if (e.target.closest?.('.hx-dialog')) e.preventDefault();
    }, true);

    const watch = () => {
        document.querySelectorAll('.hx-dialog').forEach((mount) => {
            if (state.has(mount)) return;
            state.set(mount, { open: false, returnTo: null, inerted: [] });
            new MutationObserver(() => sync(mount)).observe(mount, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['open'],
            });
            // A page delivered with the dialog open.
            sync(mount);
        });
    };

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', watch);
    else watch();
})();
