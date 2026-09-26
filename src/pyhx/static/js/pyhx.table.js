// Column resizing for the generic `.hx-table`. Mirrors pyhx.data-table.js,
// but the generic table is a pure primitive: resizing is client-side only and
// the server round-trip is opt-in via a `data-update-url` on the <table>.

let drag = null;

function parseTracks(value) {
  // Split on whitespace that is NOT inside parentheses, so grid tracks like
  // `minmax(142px, 1fr)` stay a single token.
  return value.trim().split(/\s+(?![^(]*\))/);
}

document.addEventListener("pointerdown", e => {
    const h = e.target.closest(".hx-table__col-resizer");
    if (!h) return;

    const table = h.closest(".hx-table");
    const th = h.closest("th");
    if (!table || !th) return;

    drag = {
        table,
        index: +h.dataset.colIdx,
        startX: e.clientX,
        startW: th.getBoundingClientRect().width,
        cols: parseTracks(getComputedStyle(table).getPropertyValue("--hx-table--cols")),
        updateUrl: table.dataset.updateUrl,
    };

    h.setPointerCapture(e.pointerId);
    e.preventDefault();
});

document.addEventListener("pointermove", e => {
    if (!drag) return;
    const newW = Math.max(40, Math.round(drag.startW + (e.clientX - drag.startX)));
    drag.cols[drag.index] = `${newW}px`;
    drag.table.style.setProperty("--hx-table--cols", drag.cols.join(" "));
});

document.addEventListener("pointerup", () => {
    if (!drag) return;

    // Opt-in server persistence: only when the table declares a data-update-url.
    // Otherwise the resize lives purely in the inline style set above.
    if (drag.updateUrl && window.htmx) {
        htmx.ajax("POST", drag.updateUrl, {
            source: drag.table,
            values: { column_widths: drag.cols.join(" ") },
            swap: "none",
        });
    }

    drag = null;
});
