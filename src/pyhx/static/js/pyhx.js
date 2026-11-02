/**
 * App Shell Behaviors
 */

/**
 * Initialize on DOM ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Feather Icons
    feather.replace();
});

// Re-initialize when HTMX swaps content
document.addEventListener('htmx:afterSwap', (e) => {
    // Re-render feather icons in swapped content
    feather.replace();
});

// Out-of-band and morph swaps (e.g. drawers and forms updated with
// hx-swap="none" and hx-swap-oob="morph") don't raise afterSwap; htmx:load
// fires for every element htmx inserts, so their icons are rendered too.
document.addEventListener('htmx:load', (e) => {
    feather.replace();
});
