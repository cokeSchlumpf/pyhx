// Document viewer (c.document_viewer, pyhx/components/layouts/document_viewer.py).
//
// - zoom: steps, "fit to width", applied through --document-viewer--zoom on the root
// - current page: the page under the middle of the column; the toolbar shows the
//   title of its document (when it follows) and counts the pages of that document
// - prev/next run through all pages of all documents; thumbnails scroll to a page
// - annotations (marks and notes): one active per viewer; a click on one dispatches
//   "hx-document:annotation-select" ({viewer, id, kind}); anything with
//   data-hx-document-annotation="<viewer>:<id>" activates (click) and highlights
//   (hover/focus) it and carries aria-pressed while it is active
// - start: data-hx-document-start="<document>:<page>" opens at that page,
//   data-hx-document-selected="<annotation>" selects that annotation (and wins)
// - document switcher (dv.files): filters its list while typing, ↑/↓ and Enter,
//   closes on a click outside and on Escape
// - every change of the current page dispatches "hx-document:page" ({viewer, page})
// - paged (data-hx-document-paged, the source picker): one page at a time, shown by
//   toggling `hidden` instead of scrolling; fit fits the whole page
// - source picker (c.source_picker): see its section at the end
(function () {
    "use strict";

    const STEPS = [0.5, 0.75, 1, 1.25, 1.5, 2, 3];
    const PHONE = window.matchMedia("(max-width: 40rem)");

    function viewer(root) {
        if (root.hxDocumentViewer) return root.hxDocumentViewer;

        const column = root.querySelector(".hx-document-viewer__pages");
        const pages = [...root.querySelectorAll("[data-hx-document-page]")];
        const paged = root.hasAttribute("data-hx-document-paged");
        let zoom = 1;
        let current = 0;
        // While a scroll started here runs (thumbnail, prev/next, activation), the
        // target is already selected and the pages passed on the way are ignored.
        let lock = null;

        function scrollTo(element, index, block, behavior = "smooth") {
            if (paged) {
                pages.forEach((page, i) => { page.hidden = i !== index; });
                setCurrent(index);
                if (column) column.scrollTop = 0;
                return;
            }
            lock = index;
            setCurrent(index);
            if (behavior === "auto" && column) {
                // where the viewer opens: move only the page column, not the page around the viewer
                const offset = element.getBoundingClientRect().top - column.getBoundingClientRect().top;
                const centre = (column.clientHeight - element.getBoundingClientRect().height) / 2;
                column.scrollTop += block === "center" ? offset - centre : offset - parseFloat(getComputedStyle(column).paddingTop);
            } else {
                element.scrollIntoView({ block, inline: "nearest", behavior });
            }
            clearTimeout(lock_timer);
            lock_timer = setTimeout(release, 1200);
        }

        let lock_timer = null;
        function release() {
            lock = null;
            clearTimeout(lock_timer);
        }

        const q = (selector) => root.querySelector(selector);
        const text = (selector, value) => {
            const el = q(selector);
            if (el) el.textContent = value;
        };

        function setZoom(value) {
            // paged: fitting a whole page into a small picker may need less than the smallest step
            zoom = Math.min(STEPS.at(-1), Math.max(paged ? 0.25 : STEPS[0], value));
            // keep the same place of the document in view while the pages grow or shrink
            const ratio = column && column.scrollHeight ? column.scrollTop / column.scrollHeight : 0;
            root.style.setProperty("--document-viewer--zoom", String(zoom));
            if (column) column.scrollTop = ratio * column.scrollHeight;
            text("[data-hx-document-zoom]", `${Math.round(zoom * 100)} %`);
            const out = q('[data-hx-document-action="zoom-out"]');
            const into = q('[data-hx-document-action="zoom-in"]');
            if (out) out.disabled = zoom <= STEPS[0] + 0.001;
            if (into) into.disabled = zoom >= STEPS.at(-1);
        }

        function fit() {
            if (!column) return;
            const style = getComputedStyle(column);
            const free = column.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
            const base = parseFloat(getComputedStyle(root).getPropertyValue("--document-viewer--page-width")) || 612;
            const shown = paged && pages[current];
            if (shown && shown.offsetWidth) {
                // the whole page: its width and its height fit into the column
                const height = column.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
                const ratio = shown.offsetHeight / shown.offsetWidth;
                setZoom(Math.min(free / base, height / (base * ratio)));
                return;
            }
            setZoom(free / base);
        }

        function step(direction) {
            const next = direction > 0 ? STEPS.find((s) => s > zoom + 0.001) : [...STEPS].reverse().find((s) => s < zoom - 0.001);
            if (next) setZoom(next);
        }

        function setCurrent(index) {
            const page = pages[index];
            if (!page) return;
            current = index;
            const key = page.dataset.hxDocumentPage;
            const document_ = page.closest("[data-hx-document-id]");
            text("[data-hx-document-current]", key.split(":").at(-1));
            if (document_) {
                text("[data-hx-document-count]", String(document_.querySelectorAll("[data-hx-document-page]").length));
                text("[data-hx-document-title]", document_.dataset.title);
                text("[data-hx-document-subtitle]", document_.dataset.subtitle);
            }
            root.dispatchEvent(new CustomEvent("hx-document:page", { bubbles: true, detail: { viewer: root.id, page: key } }));
            const prev = q('[data-hx-document-action="prev"]');
            const next = q('[data-hx-document-action="next"]');
            if (prev) prev.disabled = index <= 0;
            if (next) next.disabled = index >= pages.length - 1;
            root.querySelectorAll("[data-hx-document-goto]").forEach((thumb) => {
                if (thumb.dataset.hxDocumentGoto === key) {
                    thumb.setAttribute("aria-current", "page");
                    // keep it in view within the rail only, never scrolling the page around the viewer
                    const rail = thumb.closest(".hx-document-viewer__thumbnails");
                    if (rail) {
                        const t = thumb.getBoundingClientRect();
                        const r = rail.getBoundingClientRect();
                        if (t.top < r.top) rail.scrollTop += t.top - r.top;
                        else if (t.bottom > r.bottom) rail.scrollTop += t.bottom - r.bottom;
                    }
                } else {
                    thumb.removeAttribute("aria-current");
                }
            });
        }

        function goTo(index) {
            const page = pages[index];
            if (page) scrollTo(page, index, "start");
        }

        const indexOf = (key) => pages.findIndex((p) => p.dataset.hxDocumentPage === key);
        const find = (id) => root.querySelector(`[data-hx-document-annotation-id="${CSS.escape(id)}"]`);

        // One annotation is selected at a time (aria-pressed); while one is,
        // CSS lets the other marks recede (spotlight, via :has). Selecting the
        // selected one again, or Esc, clears the selection.
        function select(id) {
            root.querySelectorAll('[data-hx-document-annotation-id][aria-pressed="true"]').forEach((b) => b.setAttribute("aria-pressed", "false"));
            document.querySelectorAll(`[data-hx-document-annotation^="${CSS.escape(root.id)}:"]`).forEach((link) => {
                link.setAttribute("aria-pressed", String(id !== null && link.dataset.hxDocumentAnnotation === `${root.id}:${id}`));
            });
            const target = id === null ? null : find(id);
            if (target) target.setAttribute("aria-pressed", "true");
            return target;
        }

        function clear() {
            select(null);
        }

        function activate(id, { scroll = true, toggle = false, behavior = "smooth" } = {}) {
            const target = find(id);
            if (toggle && target && target.getAttribute("aria-pressed") === "true") {
                clear();
                return;
            }
            if (!select(id)) return;
            if (scroll) scrollTo(target, pages.indexOf(target.closest("[data-hx-document-page]")), "center", behavior);
        }

        function hover(id, on) {
            const target = find(id);
            if (target) target.toggleAttribute("data-hover", on);
        }

        root.addEventListener("click", (event) => {
            const action = event.target.closest("[data-hx-document-action]");
            if (action) {
                const name = action.dataset.hxDocumentAction;
                if (name === "prev") goTo(current - 1);
                if (name === "next") goTo(current + 1);
                if (name === "zoom-in") step(1);
                if (name === "zoom-out") step(-1);
                if (name === "fit") fit();
                return;
            }
            const thumb = event.target.closest("[data-hx-document-goto]");
            if (thumb) {
                goTo(indexOf(thumb.dataset.hxDocumentGoto));
                return;
            }
            const annotation = event.target.closest("[data-hx-document-annotation-id]");
            if (annotation) {
                const id = annotation.dataset.hxDocumentAnnotationId;
                activate(id, { scroll: false, toggle: true });
                root.dispatchEvent(new CustomEvent("hx-document:annotation-select", { bubbles: true, detail: { viewer: root.id, id, kind: annotation.dataset.kind } }));
            }
        });

        // current page: the page under the middle of the column, checked once per frame while scrolling
        if (column && !paged) {
            let queued = false;
            column.addEventListener("scrollend", release);
            column.addEventListener("scroll", () => {
                if (queued || lock !== null) return;
                queued = true;
                requestAnimationFrame(() => {
                    queued = false;
                    const middle = column.getBoundingClientRect().top + column.clientHeight / 2;
                    let index = 0;
                    pages.forEach((page, i) => {
                        if (page.getBoundingClientRect().top <= middle) index = i;
                    });
                    if (index !== current) setCurrent(index);
                });
            }, { passive: true });
        }

        // pages without a size start with an assumed (A4) ratio; take the real one
        // from the image once it has loaded, for the page and its thumbnail
        function correctRatio(page, img) {
            if (!img.naturalWidth || !img.naturalHeight) return;
            const ratio = `${img.naturalWidth} / ${img.naturalHeight}`;
            page.style.aspectRatio = ratio;
            page.removeAttribute("data-hx-document-ratio");
            const thumb = q(`[data-hx-document-goto="${CSS.escape(page.dataset.hxDocumentPage)}"] img`);
            if (thumb) thumb.style.aspectRatio = ratio;
        }
        root.querySelectorAll('[data-hx-document-ratio="assumed"] > img').forEach((img) => {
            if (img.complete) correctRatio(img.parentElement, img);
        });
        root.addEventListener("load", (event) => {
            const page = event.target.parentElement;
            if (event.target.tagName === "IMG" && page && page.dataset.hxDocumentRatio === "assumed") correctRatio(page, event.target);
        }, true);

        root.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && root.querySelector('[data-hx-document-annotation-id][aria-pressed="true"]')) clear();
        });

        // pinch zoom on touch devices: two fingers on the page column scale the zoom;
        // one finger keeps scrolling natively (touch-action: pan-x pan-y)
        if (column) {
            let pinch = null;
            const distance = (t) => Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
            column.addEventListener("touchstart", (event) => {
                if (event.touches.length === 2) pinch = { distance: distance(event.touches), zoom };
            }, { passive: true });
            column.addEventListener("touchmove", (event) => {
                if (!pinch || event.touches.length !== 2) return;
                event.preventDefault();
                setZoom(pinch.zoom * (distance(event.touches) / pinch.distance));
            }, { passive: false });
            column.addEventListener("touchend", () => { pinch = null; }, { passive: true });
        }

        if (PHONE.matches) fit();
        else setZoom(1);
        // paged: the whole page in view (after setCurrent, which fit measures)
        if (paged) requestAnimationFrame(fit);
        // where the viewer opens: the selected annotation, else the start page, else the first page
        const start = Math.max(0, indexOf(root.dataset.hxDocumentStart || ""));
        const selected = root.dataset.hxDocumentSelected;
        setCurrent(start);
        requestAnimationFrame(() => {
            if (selected && find(selected)) activate(selected, { behavior: "auto" });
            else if (start > 0) scrollTo(pages[start], start, "start", "auto");
        });

        root.hxDocumentViewer = { activate, clear, hover, goTo: (key) => goTo(indexOf(key)), setZoom, fit };
        return root.hxDocumentViewer;
    }

    function resolve(link) {
        const value = link.dataset.hxDocumentAnnotation || "";
        const split = value.indexOf(":");
        const root = split > 0 && document.getElementById(value.slice(0, split));
        return root && root.matches("[data-hx-document-viewer]") ? [viewer(root), value.slice(split + 1)] : [null, null];
    }

    document.addEventListener("click", (event) => {
        const link = event.target.closest("[data-hx-document-annotation]");
        if (!link) return;
        const [v, id] = resolve(link);
        if (v) v.activate(id, { toggle: true });
    });

    for (const [type, on] of [["mouseover", true], ["mouseout", false], ["focusin", true], ["focusout", false]]) {
        document.addEventListener(type, (event) => {
            const link = event.target.closest && event.target.closest("[data-hx-document-annotation]");
            if (!link) return;
            const [v, id] = resolve(link);
            if (v) v.hover(id, on);
        });
    }

    // ------------------------------------------------------------------ document switcher

    const SWITCHER = ".hx-document-viewer__files-menu";
    const searchable = (text) => text.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
    const shownEntries = (menu) => [...menu.querySelectorAll("a[data-hx-document-search]:not([hidden])")];

    function filter(menu, value) {
        const term = searchable(value.trim());
        let matches = 0;
        menu.querySelectorAll("[data-hx-document-search]").forEach((entry) => {
            const match = !term || entry.dataset.hxDocumentSearch.includes(term);
            entry.hidden = !match;
            if (match) matches += 1;
        });
        menu.querySelectorAll(".hx-document-viewer__files-group").forEach((group) => {
            group.hidden = !group.querySelector("[data-hx-document-search]:not([hidden])");
        });
        const count = menu.querySelector("[data-hx-document-files-matches]");
        if (count) count.textContent = count.dataset.template.replace("{n}", String(matches));
    }

    function close(menu, focus) {
        menu.removeAttribute("open");
        if (focus) menu.querySelector("summary")?.focus();
    }

    document.addEventListener("input", (event) => {
        const input = event.target.closest && event.target.closest("[data-hx-document-files-search]");
        if (input) filter(input.closest(SWITCHER), input.value);
    });

    // opening it puts the focus into the search field
    document.addEventListener("toggle", (event) => {
        const menu = event.target;
        if (menu.matches && menu.matches(SWITCHER) && menu.open) {
            menu.querySelector("[data-hx-document-files-search]")?.focus();
        }
    }, true);

    document.addEventListener("click", (event) => {
        for (const menu of document.querySelectorAll(`${SWITCHER}[open]`)) {
            if (!menu.contains(event.target)) close(menu, false);
        }
    });

    // captured, so Escape closes the switcher before the viewer clears its selection
    document.addEventListener("keydown", (event) => {
        const menu = event.target.closest && event.target.closest(`${SWITCHER}[open]`);
        if (!menu) {
            if (event.key === "Escape") {
                const open = document.querySelector(`${SWITCHER}[open]`);
                if (open) {
                    event.stopPropagation();
                    close(open, true);
                }
            }
            return;
        }
        if (event.key === "Escape") {
            event.preventDefault();
            event.stopPropagation();
            close(menu, true);
            return;
        }
        if (event.key !== "ArrowDown" && event.key !== "ArrowUp" && event.key !== "Enter") return;
        const entries = shownEntries(menu);
        const at = entries.indexOf(document.activeElement);
        if (event.key === "Enter") {
            // in the search field Enter opens the first entry shown; on an entry the link opens itself
            if (at === -1 && entries.length) {
                event.preventDefault();
                entries[0].click();
            }
            return;
        }
        event.preventDefault();
        if (!entries.length) return;
        if (event.key === "ArrowDown") entries[Math.min(entries.length - 1, at + 1)].focus();
        else if (at <= 0) menu.querySelector("[data-hx-document-files-search]")?.focus();
        else entries[at - 1].focus();
    }, true);

    // ------------------------------------------------------------------ source picker
    //
    // c.source_picker: a paged viewer whose current page is the choice. A pointer drag
    // on the page draws one box (the area); a drag on it moves it, on a corner handle
    // resizes it. On the focused box arrow keys move it, Shift + arrows resize it,
    // Delete/Backspace/Escape remove it; Escape anywhere in the picker removes the box
    // (and, prevented, doesn't close a surrounding dialog). Another page removes the box.
    // The choice is kept in the hidden inputs <name>_document, _page and _box
    // ("x,y,width,height", fractions with four decimals, empty for the whole page);
    // every change dispatches "hx-source-picker:change" ({picker, document, page, box}).

    const MIN = 0.01;
    const STEP = 0.01;
    const HANDLES = ["nw", "ne", "sw", "se"];
    const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
    const pct = (value) => `${(value * 100).toFixed(4)}%`;
    const fixed = (value) => Math.round(value * 10000) / 10000;

    function corners(a, b) {
        const x = Math.min(a.x, b.x);
        const y = Math.min(a.y, b.y);
        return { x, y, width: Math.max(a.x, b.x) - x, height: Math.max(a.y, b.y) - y };
    }

    function parseBox(value) {
        const parts = (value || "").split(",").map(Number);
        if (!value || parts.length !== 4 || parts.some((n) => !Number.isFinite(n))) return null;
        const [x, y, width, height] = parts;
        return { x, y, width, height };
    }

    // the box with four decimals, still within the page
    function rounded(box) {
        const x = fixed(box.x);
        const y = fixed(box.y);
        return { x, y, width: Math.min(fixed(box.width), fixed(1 - x)), height: Math.min(fixed(box.height), fixed(1 - y)) };
    }

    function picker(root) {
        if (root.hxSourcePicker) return root.hxSourcePicker;
        const view = viewer(root);
        const name = root.dataset.hxSourcePicker;
        const footer = root.querySelector(".hx-source-picker__footer");
        const input = (part) => [...footer.querySelectorAll('input[type="hidden"]')].find((i) => i.name === `${name}_${part}`);
        const status = footer.querySelector("[data-hx-source-picker-status]");
        const clearButton = footer.querySelector("[data-hx-source-picker-clear]");
        let box = null;
        let area = null;
        let key = null;
        let drag = null;

        const shownPage = () => root.querySelector("[data-hx-document-page]:not([hidden])");

        function makeArea() {
            const element = document.createElement("div");
            element.className = "hx-source-picker__area";
            element.tabIndex = 0;
            element.setAttribute("role", "group");
            element.setAttribute("aria-label", footer.dataset.textAreaLabel);
            element.title = footer.dataset.textAreaKeys;
            for (const handle of HANDLES) {
                const span = document.createElement("span");
                span.className = "hx-source-picker__handle";
                span.dataset.handle = handle;
                element.appendChild(span);
            }
            return element;
        }

        function render() {
            const page = shownPage();
            if (!box || !page) {
                if (area) area.remove();
                area = null;
            } else {
                if (!area || !area.isConnected) area = makeArea();
                if (area.parentElement !== page) page.appendChild(area);
                Object.assign(area.style, { left: pct(box.x), top: pct(box.y), width: pct(box.width), height: pct(box.height) });
            }
            root.toggleAttribute("data-hx-source-picker-area", !!(box && page));
            if (clearButton) clearButton.disabled = !box;
        }

        // the inputs, the status line and the event, after every change of the choice
        function commit() {
            const page = shownPage();
            if (!page) return;
            const pageKey = page.dataset.hxDocumentPage;
            const split = pageKey.lastIndexOf(":");
            const documentId = pageKey.slice(0, split);
            const number = Number(pageKey.slice(split + 1));
            const title = page.closest("[data-hx-document-id]")?.dataset.title || documentId;
            const value = box ? rounded(box) : null;
            input("document").value = documentId;
            input("page").value = String(number);
            input("box").value = value ? [value.x, value.y, value.width, value.height].map((n) => n.toFixed(4)).join(",") : "";
            if (status) status.textContent = (box ? footer.dataset.textArea : footer.dataset.textWhole).replace("{document}", title).replace("{page}", String(number));
            root.dispatchEvent(new CustomEvent("hx-source-picker:change", { bubbles: true, detail: { picker: root.id, document: documentId, page: number, box: value } }));
        }

        function set(next) {
            box = next;
            render();
            commit();
        }

        // the state from the inputs: on load, and when the server sent the picker again
        function sync() {
            const target = `${input("document").value}:${input("page").value}`;
            key = target;
            // also when the page is shown already: the viewer's pager follows
            view.goTo(target);
            key = shownPage()?.dataset.hxDocumentPage || target;
            box = parseBox(input("box").value);
            render();
        }

        function point(page, event) {
            const rect = page.getBoundingClientRect();
            return { x: clamp((event.clientX - rect.left) / rect.width, 0, 1), y: clamp((event.clientY - rect.top) / rect.height, 0, 1) };
        }

        root.addEventListener("hx-document:page", (event) => {
            if (event.target !== root || event.detail.page === key) return;
            key = event.detail.page;
            set(null);
        });

        root.addEventListener("pointerdown", (event) => {
            if (drag) {
                // a second finger (pinch zoom): give up the drag
                box = drag.from;
                drag = null;
                render();
                return;
            }
            const page = event.target.closest(".hx-document-viewer__page");
            if (!page || page.hidden || event.button !== 0 || !root.contains(page)) return;
            const handle = event.target.closest("[data-handle]");
            const mode = handle ? handle.dataset.handle : event.target.closest(".hx-source-picker__area") ? "move" : "draw";
            drag = { page, mode, id: event.pointerId, start: point(page, event), from: box };
            page.setPointerCapture(event.pointerId);
            event.preventDefault();
        });

        root.addEventListener("pointermove", (event) => {
            if (!drag || event.pointerId !== drag.id) return;
            const p = point(drag.page, event);
            const from = drag.from;
            if (drag.mode === "draw") {
                box = corners(drag.start, p);
            } else if (drag.mode === "move") {
                box = {
                    x: clamp(from.x + p.x - drag.start.x, 0, 1 - from.width),
                    y: clamp(from.y + p.y - drag.start.y, 0, 1 - from.height),
                    width: from.width,
                    height: from.height,
                };
            } else {
                // a corner follows the pointer, the opposite one stays
                const left = drag.mode.includes("w") ? p.x : from.x;
                const right = drag.mode.includes("e") ? p.x : from.x + from.width;
                const top = drag.mode.startsWith("n") ? p.y : from.y;
                const bottom = drag.mode.startsWith("s") ? p.y : from.y + from.height;
                box = corners({ x: left, y: top }, { x: right, y: bottom });
            }
            render();
        });

        root.addEventListener("pointerup", (event) => {
            if (!drag || event.pointerId !== drag.id) return;
            const { from } = drag;
            drag = null;
            // a click or a tiny drag keeps the box there was
            if (!box || box.width < MIN || box.height < MIN) box = from;
            render();
            if (box !== from) commit();
            if (area) area.focus({ preventScroll: true });
        });

        root.addEventListener("pointercancel", (event) => {
            if (!drag || event.pointerId !== drag.id) return;
            box = drag.from;
            drag = null;
            render();
        });

        root.addEventListener("keydown", (event) => {
            if (!box) return;
            if (event.key === "Escape" || (event.target === area && (event.key === "Delete" || event.key === "Backspace"))) {
                // prevented: a surrounding dialog stays open (pyhx.dialog.js)
                event.preventDefault();
                const hadFocus = event.target === area;
                set(null);
                if (hadFocus) root.querySelector(".hx-document-viewer__pages")?.focus({ preventScroll: true });
                return;
            }
            if (event.target !== area || !event.key.startsWith("Arrow")) return;
            event.preventDefault();
            const dx = event.key === "ArrowRight" ? STEP : event.key === "ArrowLeft" ? -STEP : 0;
            const dy = event.key === "ArrowDown" ? STEP : event.key === "ArrowUp" ? -STEP : 0;
            if (event.shiftKey) {
                set({ ...box, width: clamp(box.width + dx, MIN, 1 - box.x), height: clamp(box.height + dy, MIN, 1 - box.y) });
            } else {
                set({ ...box, x: clamp(box.x + dx, 0, 1 - box.width), y: clamp(box.y + dy, 0, 1 - box.height) });
            }
        });

        if (clearButton) clearButton.addEventListener("click", () => set(null));

        // with a document switcher (files): an entry or previous/next replaces the picker
        // with the one its href returns, so the page (or the dialog) stays
        root.addEventListener("click", (event) => {
            const link = event.target.closest(".hx-document-viewer__files a[href]");
            if (!link || !root.contains(link) || !window.htmx) return;
            event.preventDefault();
            const id = root.id;
            const switcher = !!link.closest(SWITCHER);
            window.htmx.ajax("GET", link.getAttribute("href"), { target: root, swap: "outerHTML" }).then(() => {
                // the focus stays on the control that was used
                const next = document.getElementById(id);
                const control = switcher ? next?.querySelector(`${SWITCHER} > summary`) : null;
                (control || next?.querySelector(".hx-document-viewer__pages"))?.focus({ preventScroll: true });
            });
        });

        root.hxSourcePicker = { sync, clear: () => set(null) };
        return root.hxSourcePicker;
    }

    // the elements matching `selector` in `scope`, the scope itself included (a swapped-in viewer)
    function within(scope, selector) {
        const root = scope || document;
        const found = [...root.querySelectorAll(selector)];
        return root.matches && root.matches(selector) ? [root, ...found] : found;
    }

    function init(scope) {
        within(scope, "[data-hx-document-viewer]").forEach(viewer);
        // also when the server sent a picker again (e.g. a dialog with an error): the state of its inputs
        within(scope, "[data-hx-source-picker]").forEach((root) => picker(root).sync());
    }

    window.pyhx = window.pyhx || {};
    window.pyhx.documentViewer = (id) => {
        const root = document.getElementById(id);
        return root ? viewer(root) : null;
    };

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => init());
    else init();
    document.addEventListener("htmx:load", (event) => init(event.target));
})();
