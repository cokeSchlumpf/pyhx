/**
 * Close the group dropdowns of the CanvasShell tabs like a menu.
 *
 * A group is a native `<details>` (it works without this script; `name` keeps
 * at most one open), which stays open until its summary is clicked again.
 * This closes it on a click outside it and on Escape, returning focus to its
 * summary. Loaded only with `main_navigation="tabs"`.
 */
const OPEN_GROUP = '.hx-canvas-nav[data-hx-placement="tabs"] details[open]';

document.addEventListener('click', (e) => {
    for (const details of document.querySelectorAll(OPEN_GROUP)) {
        if (!details.contains(e.target)) details.removeAttribute('open');
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    const details = document.querySelector(OPEN_GROUP);
    if (!details) return;
    details.removeAttribute('open');
    details.querySelector('summary')?.focus();
});
