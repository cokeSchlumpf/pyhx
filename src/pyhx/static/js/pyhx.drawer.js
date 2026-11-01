/**
 * Drawer behaviour shared by every page template:
 *
 * - A click on the backdrop closes the drawer, by clicking that drawer's own
 *   header close button.
 * - Esc closes the topmost open drawer the same way (the popup drawer first).
 * - When a drawer opens (its panel's section gets content), focus moves into
 *   the panel; when it closes, focus returns to the element that had it
 *   before, if that element is still on the page.
 */
(() => {
    const isOpen = (drawer) => !!drawer.querySelector(':scope > aside > section > *');

    const close = (drawer) => {
        const button = drawer.querySelector('[data-hx-drawer-close]');
        if (button && !button.disabled) button.click();
    };

    document.addEventListener('click', (e) => {
        const backdrop = e.target.closest('.hx-drawer__backdrop');
        if (backdrop) close(backdrop.closest('.hx-drawer'));
    });

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape' || e.defaultPrevented) return;
        // An open dropdown (<details>) in the drawer closes first.
        if (e.target.closest?.('details[open]')) return;
        const open = [...document.querySelectorAll('.hx-drawer')].filter(isOpen);
        if (!open.length) return;
        // Later in the DOM is higher in the stack (the popup drawer comes last).
        close(open[open.length - 1]);
        e.preventDefault();
    });

    const state = new WeakMap(); // drawer -> {open, returnTo}

    const sync = (drawer) => {
        const before = state.get(drawer) ?? { open: false, returnTo: null };
        const now = isOpen(drawer);
        if (now === before.open) return;
        if (now) {
            const active = document.activeElement;
            const returnTo = active && active !== document.body && !drawer.contains(active) ? active : null;
            state.set(drawer, { open: true, returnTo });
            drawer.querySelector(':scope > aside')?.focus({ preventScroll: true });
        } else {
            state.set(drawer, { open: false, returnTo: null });
            const panel = drawer.querySelector(':scope > aside');
            const focusWasInside = !document.activeElement || document.activeElement === document.body
                || panel?.contains(document.activeElement);
            if (focusWasInside && before.returnTo?.isConnected) before.returnTo.focus({ preventScroll: true });
        }
    };

    const watch = () => {
        document.querySelectorAll('.hx-drawer').forEach((drawer) => {
            if (state.has(drawer)) return;
            state.set(drawer, { open: isOpen(drawer), returnTo: null });
            new MutationObserver(() => sync(drawer)).observe(drawer, { childList: true, subtree: true });
        });
    };

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', watch);
    else watch();
})();
