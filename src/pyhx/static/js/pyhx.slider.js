// Slider behaviour for `slider(...)`: dragging, clicking the track, keyboard.
//
// The server renders the complete state (positions, ARIA values, one hidden
// input per thumb); this script only moves it. Every change snaps to the
// step, clamps to the thumb's own bounds and its neighbours (thumbs never
// cross), then updates the thumb's position, the range, the ARIA values and
// the hidden input. The hidden input dispatches bubbling `input` events while
// a value changes and `change` once it settles (pointer released, key
// pressed) — so forms and `hx-trigger="change"` pick it up like any other
// control.
//
// Thumbs, range and inputs are looked up per event rather than cached: a
// morph swap may replace them while keeping the root.

class PyhxSlider {
    constructor(root) {
        this.root = root;
        this.drag = null;
        this.bind();
    }

    // --- DOM ----------------------------------------------------------------

    get track() {
        return this.root.querySelector('.hx-slider__track');
    }

    get thumbs() {
        return Array.from(this.root.querySelectorAll('.hx-slider__thumb[data-slider-index]'));
    }

    inputAt(index) {
        return this.root.querySelector(`input[data-slider-index="${index}"]`);
    }

    get disabled() {
        return this.root.getAttribute('aria-disabled') === 'true';
    }

    // --- Scale --------------------------------------------------------------

    get scale() {
        const data = this.root.dataset;
        return {
            min: parseFloat(data.sliderMin),
            max: parseFloat(data.sliderMax),
            step: parseFloat(data.sliderStep),
        };
    }

    values() {
        return this.thumbs.map((_, i) => parseFloat(this.inputAt(i).value));
    }

    // Lowest / highest value thumb `index` may take right now: its own bounds,
    // narrowed by its neighbours.
    bounds(index, values) {
        const thumb = this.thumbs[index];
        let lo = parseFloat(thumb.dataset.sliderMin);
        let hi = parseFloat(thumb.dataset.sliderMax);
        if (index > 0) lo = Math.max(lo, values[index - 1]);
        if (index < values.length - 1) hi = Math.min(hi, values[index + 1]);
        return { lo, hi };
    }

    snap(value) {
        const { min, step } = this.scale;
        const snapped = min + Math.round((value - min) / step) * step;
        // Trim float noise (0.30000000000000004) to the precision of the
        // scale's own numbers.
        return Number(snapped.toFixed(Math.max(decimals(min), decimals(step))));
    }

    percent(value) {
        const { min, max } = this.scale;
        return ((value - min) / (max - min)) * 100;
    }

    valueAt(clientX) {
        const rect = this.track.getBoundingClientRect();
        const { min, max } = this.scale;
        const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
        return min + ratio * (max - min);
    }

    // --- Update -------------------------------------------------------------

    // Move thumb `index` towards `target`; returns whether its value changed.
    setValue(index, target) {
        const values = this.values();
        const { lo, hi } = this.bounds(index, values);
        const value = Math.min(hi, Math.max(lo, this.snap(target)));
        if (value === values[index]) return false;

        values[index] = value;
        this.render(values);
        this.inputAt(index).dispatchEvent(new Event('input', { bubbles: true }));
        return true;
    }

    render(values) {
        this.thumbs.forEach((thumb, i) => {
            const { lo, hi } = this.bounds(i, values);
            thumb.style.setProperty('--hx-slider--position', `${this.percent(values[i])}%`);
            thumb.setAttribute('aria-valuenow', String(values[i]));
            thumb.setAttribute('aria-valuemin', String(lo));
            thumb.setAttribute('aria-valuemax', String(hi));
            this.inputAt(i).value = String(values[i]);
        });

        const range = this.root.querySelector('.hx-slider__range');
        if (!range) return;
        const [first, second] = values;
        const start = values.length === 2 ? this.percent(first) : 0;
        const end = values.length === 2 ? this.percent(second) : this.percent(first);
        range.style.setProperty('--hx-slider--start', `${start}%`);
        range.style.setProperty('--hx-slider--end', `${end}%`);
    }

    commit(index) {
        this.inputAt(index).dispatchEvent(new Event('change', { bubbles: true }));
    }

    // The thumb a click at `value` should move: the nearest one. Among thumbs
    // stacked on the same value, the one that can actually move that way.
    nearestThumb(value) {
        const values = this.values();
        let best = 0;
        values.forEach((v, i) => {
            const distance = Math.abs(v - value);
            const bestDistance = Math.abs(values[best] - value);
            if (distance < bestDistance || (distance === bestDistance && value > v)) {
                best = i;
            }
        });
        return best;
    }

    // --- Events -------------------------------------------------------------

    bind() {
        // Listening on the root (not just the 4px track) gives a pointer
        // target as tall as a thumb.
        this.root.addEventListener('pointerdown', (event) => this.onPointerDown(event));
        this.root.addEventListener('pointermove', (event) => this.onPointerMove(event));
        this.root.addEventListener('pointerup', (event) => this.onPointerUp(event));
        this.root.addEventListener('pointercancel', (event) => this.onPointerUp(event));
        this.root.addEventListener('keydown', (event) => this.onKeyDown(event));
    }

    onPointerDown(event) {
        if (this.disabled || event.button !== 0) return;

        const thumb = event.target.closest('.hx-slider__thumb[data-slider-index]');
        const index = thumb
            ? parseInt(thumb.dataset.sliderIndex, 10)
            : this.nearestThumb(this.valueAt(event.clientX));

        // Prevent text selection and the focus jump to the root; focus the
        // thumb explicitly so the keyboard takes over after a click.
        event.preventDefault();
        const target = this.thumbs[index];
        target.focus();
        this.root.setPointerCapture(event.pointerId);
        target.toggleAttribute('data-dragging', true);

        const changed = thumb ? false : this.setValue(index, this.valueAt(event.clientX));
        this.drag = { index, pointerId: event.pointerId, changed };
    }

    onPointerMove(event) {
        if (!this.drag || event.pointerId !== this.drag.pointerId) return;
        if (this.setValue(this.drag.index, this.valueAt(event.clientX))) {
            this.drag.changed = true;
        }
    }

    onPointerUp(event) {
        if (!this.drag || event.pointerId !== this.drag.pointerId) return;

        const { index, changed } = this.drag;
        this.drag = null;
        this.thumbs[index]?.removeAttribute('data-dragging');
        if (this.root.hasPointerCapture(event.pointerId)) {
            this.root.releasePointerCapture(event.pointerId);
        }
        if (changed) this.commit(index);
    }

    onKeyDown(event) {
        const thumb = event.target.closest('.hx-slider__thumb[data-slider-index]');
        if (!thumb || this.disabled) return;

        const index = parseInt(thumb.dataset.sliderIndex, 10);
        const values = this.values();
        const { lo, hi } = this.bounds(index, values);
        const { step } = this.scale;
        const current = values[index];

        const targets = {
            ArrowRight: current + step,
            ArrowUp: current + step,
            ArrowLeft: current - step,
            ArrowDown: current - step,
            PageUp: current + step * 10,
            PageDown: current - step * 10,
            Home: lo,
            End: hi,
        };
        if (!(event.key in targets)) return;

        event.preventDefault();
        if (this.setValue(index, targets[event.key])) this.commit(index);
    }
}

function decimals(number) {
    const text = String(number);
    const dot = text.indexOf('.');
    return dot === -1 ? 0 : text.length - dot - 1;
}

// Track initialised sliders on the node itself rather than a data-*
// attribute - see pyhx.wysiwyg-editor.js for why. A WeakSet keyed on the
// element survives attribute stripping, so a morph-preserved slider is
// initialised once.
const _pyhxSliderInitialized = new WeakSet();

function initPyhxSliders(root = document) {
    // `htmx:load` fires on the swapped-in element itself, which may be the
    // slider root - querySelectorAll alone only finds descendants.
    const roots = Array.from(root.querySelectorAll('[data-slider]'));
    if (root.matches?.('[data-slider]')) roots.push(root);

    roots.forEach((el) => {
        if (_pyhxSliderInitialized.has(el)) return;

        _pyhxSliderInitialized.add(el);
        new PyhxSlider(el);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initPyhxSliders();
});

document.addEventListener('htmx:afterSwap', (event) => {
    initPyhxSliders(event.target);
});

document.addEventListener('htmx:load', (event) => {
    initPyhxSliders(event.target);
});
