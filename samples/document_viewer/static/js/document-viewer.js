// Draft script of the document viewer (T-010); moves to static/js/pyhx.document-viewer.js once accepted.
//
// - zoom: steps, "fit to width", applied through --document-viewer--zoom on the root
// - current page: the page under the middle of the column; the toolbar shows the
//   title of its document (when it follows) and counts the pages of that document
// - prev/next run through all pages of all documents; thumbnails scroll to a page
// - annotations (marks and notes): one active per viewer; a click on one dispatches
//   "hx-document:annotation-select" ({viewer, id, kind}); anything with
//   data-hx-document-annotation="<viewer>:<id>" activates (click) and highlights
//   (hover/focus) it and carries aria-pressed while it is active
(function () {
    "use strict";

    const STEPS = [0.5, 0.75, 1, 1.25, 1.5, 2, 3];
    const PHONE = window.matchMedia("(max-width: 40rem)");

    function viewer(root) {
        if (root.hxDocumentViewer) return root.hxDocumentViewer;

        const column = root.querySelector(".hx-document-viewer__pages");
        const pages = [...root.querySelectorAll("[data-hx-document-page]")];
        let zoom = 1;
        let current = 0;
        // While a scroll started here runs (thumbnail, prev/next, activation), the
        // target is already selected and the pages passed on the way are ignored.
        let lock = null;

        function scrollTo(element, index, block) {
            lock = index;
            setCurrent(index);
            element.scrollIntoView({ block, inline: "nearest", behavior: "smooth" });
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
            zoom = Math.min(STEPS.at(-1), Math.max(STEPS[0], value));
            // keep the same place of the document in view while the pages grow or shrink
            const ratio = column && column.scrollHeight ? column.scrollTop / column.scrollHeight : 0;
            root.style.setProperty("--document-viewer--zoom", String(zoom));
            if (column) column.scrollTop = ratio * column.scrollHeight;
            text("[data-hx-document-zoom]", `${Math.round(zoom * 100)} %`);
            const out = q('[data-hx-document-action="zoom-out"]');
            const into = q('[data-hx-document-action="zoom-in"]');
            if (out) out.disabled = zoom <= STEPS[0];
            if (into) into.disabled = zoom >= STEPS.at(-1);
        }

        function fit() {
            if (!column) return;
            const style = getComputedStyle(column);
            const free = column.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
            const base = parseFloat(getComputedStyle(root).getPropertyValue("--document-viewer--page-width")) || 612;
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
            const prev = q('[data-hx-document-action="prev"]');
            const next = q('[data-hx-document-action="next"]');
            if (prev) prev.disabled = index <= 0;
            if (next) next.disabled = index >= pages.length - 1;
            root.querySelectorAll("[data-hx-document-goto]").forEach((thumb) => {
                if (thumb.dataset.hxDocumentGoto === key) {
                    thumb.setAttribute("aria-current", "page");
                    thumb.scrollIntoView({ block: "nearest" });
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

        function activate(id, { scroll = true, toggle = false } = {}) {
            const target = find(id);
            if (toggle && target && target.getAttribute("aria-pressed") === "true") {
                clear();
                return;
            }
            if (!select(id)) return;
            if (scroll) scrollTo(target, pages.indexOf(target.closest("[data-hx-document-page]")), "center");
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
        if (column) {
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
        setCurrent(0);

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

    function init(scope) {
        (scope || document).querySelectorAll("[data-hx-document-viewer]").forEach(viewer);
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
