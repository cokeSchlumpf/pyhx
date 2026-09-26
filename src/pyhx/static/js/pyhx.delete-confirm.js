/**
 * Enable a typed delete-confirmation button once the input matches the
 * expected value.
 *
 * Used by ``DataSection``'s typed delete-confirmation mode: the input
 * carries `data-expected-value` (the string the user must retype) and
 * `data-confirm-button` (the id of the button to toggle).
 */
document.addEventListener('input', (e) => {
    const input = e.target.closest('[data-expected-value]');
    if (!input || !input.dataset.confirmButton) return;
    const button = document.getElementById(input.dataset.confirmButton);
    if (!button) return;
    button.disabled = input.value !== input.dataset.expectedValue;
});
