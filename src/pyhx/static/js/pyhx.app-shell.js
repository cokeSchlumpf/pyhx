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

