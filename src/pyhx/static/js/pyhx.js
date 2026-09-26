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
