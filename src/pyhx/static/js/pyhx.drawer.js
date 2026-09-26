/**
 * Close a drawer when its backdrop is clicked, by clicking that drawer's own
 * header close button.
 */
document.addEventListener('click', (e) => {
    const backdrop = e.target.closest('.hx-drawer__backdrop');
    if (!backdrop) return;
    const close = backdrop.closest('.hx-drawer')?.querySelector('[data-hx-drawer-close]');
    if (close && !close.disabled) close.click();
});
