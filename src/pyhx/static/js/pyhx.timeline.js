// Timeline behaviour for `timeline(...)`: axis, markers, filter and span.
//
// The server renders the chips, the slider, the density strip and the data
// (events as JSON, one icon template per category, texts as data-text-*).
// This script keeps the state - the shown categories and the span - and
// lays out the axis whenever it changes or the timeline's width changes:
// ticks in a unit that fits, period bars, and markers that never overlap.
// A marker is a button with `hx-get` to the app's URL with the keys of its
// events; the app answers with the drawer's content.
//
// `ticks` and `place` are pure functions, exposed on `window.PyhxTimeline`.

(() => {
    const DAY_MS = 86400000;
    // Distance between two tick labels, in px: the first that gives at least
    // three ticks (narrow axes accept closer, shorter labels).
    const TICK_GAPS = [68, 48, 40];
    // The icons' places: [side, distance from the axis in px].
    const PLACES = [[-1, 64], [1, 64], [-1, 116], [1, 116]];
    // Two icons in one place need this much room, in px.
    const ICON_GAP = 40;
    // Dots closer than this always share a marker, in px.
    const DOT_JOIN = 10;
    const PAD = 24;

    const toDay = (iso) => {
        const [y, m, d] = iso.split('-').map(Number);
        return Math.round(Date.UTC(y, m - 1, d) / DAY_MS);
    };
    const parts = (day) => {
        const t = new Date(day * DAY_MS);
        return [t.getUTCFullYear(), t.getUTCMonth(), t.getUTCDate()];
    };
    const dayOf = (y, m, d = 1) => Math.round(Date.UTC(y, m, d) / DAY_MS);
    const iso = (day) => new Date(day * DAY_MS).toISOString().slice(0, 10);

    // --- Pure layout ---------------------------------------------------------

    // The ticks between `from` and `to` (days) on an axis `width` px wide:
    // the finest of days, weeks, months, quarters and years whose ticks are
    // at least `gap` apart (several years per tick if even years don't fit),
    // with the first gap of TICK_GAPS that gives three ticks.
    function ticks(from, to, width) {
        let result;
        for (const gap of TICK_GAPS) {
            result = ticksWithGap(from, to, width, gap);
            if (result.ticks.length >= 3) break;
        }
        return result;
    }

    function ticksWithGap(from, to, width, gap) {
        const perDay = width / Math.max(1, to - from);
        const units = [['day', 1], ['week', 7], ['month', 30.44], ['quarter', 91.31], ['year', 365.25]];
        const found = units.find(([, days]) => days * perDay >= gap);
        const unit = found ? found[0] : 'year';
        const years = found ? 1 : Math.ceil(gap / (365.25 * perDay));
        const [y0, m0] = parts(from);
        let day;
        if (unit === 'day') day = from;
        else if (unit === 'week') day = from + ((8 - new Date(from * DAY_MS).getUTCDay()) % 7);
        else if (unit === 'month') day = dayOf(y0, m0);
        else if (unit === 'quarter') day = dayOf(y0, Math.floor(m0 / 3) * 3);
        else day = dayOf(y0 - (y0 % years), 0);
        const out = [];
        for (let guard = 0; day <= to && guard < 1000; guard++) {
            const [y, m, d] = parts(day);
            if (day >= from) out.push({ day, unit, major: m === 0 && d <= (unit === 'week' ? 7 : 1) });
            if (unit === 'day') day += 1;
            else if (unit === 'week') day += 7;
            else if (unit === 'month') day = dayOf(y, m + 1);
            else if (unit === 'quarter') day = dayOf(y, m + 3);
            else day = dayOf(y + years, 0);
        }
        return { unit, ticks: out };
    }

    // Markers for `points` ([{x, event}] sorted by x): from left to right,
    // each point takes the first of the four places whose last icon is at
    // least ICON_GAP away, or joins the marker before.
    function place(points) {
        const last = PLACES.map(() => -Infinity);
        const markers = [];
        let current = null;
        for (const p of points) {
            if (current && p.x - current.x < DOT_JOIN) {
                current.events.push(p.event);
                continue;
            }
            const free = PLACES.findIndex((_, i) => p.x - last[i] >= ICON_GAP);
            if (free < 0 && current) {
                current.events.push(p.event);
                continue;
            }
            const slot = Math.max(0, free);
            last[slot] = p.x;
            current = { x: p.x, slot, events: [p.event] };
            markers.push(current);
        }
        return markers;
    }

    // --- The component -------------------------------------------------------

    class PyhxTimeline {
        constructor(root) {
            this.root = root;
            this.axis = root.querySelector('[data-timeline-axis]');
            this.events = JSON.parse(root.querySelector('script[data-timeline-events]').textContent)
                .map((e) => ({ ...e, from: toDay(e.start), to: e.end ? toDay(e.end) : toDay(e.start) }));
            this.icons = new Map(
                Array.from(root.querySelectorAll('template[data-timeline-icon]'))
                    .map((t) => [t.dataset.timelineIcon, t]),
            );
            this.colors = new Map(this.chips.map((c) => [c.dataset.timelineCategory, c.style.getPropertyValue('--timeline--color')]));
            this.defaults = (root.dataset.timelineDefault || '').split(',').filter(Boolean);
            this.query = root.dataset.timelineQuery ? JSON.parse(root.dataset.timelineQuery) : null;
            this.url = root.dataset.timelineOpenUrl;
            this.lang = document.documentElement.lang || undefined;
            this.open = null;
            this.bind();
            this.render();
        }

        // --- State ----------------------------------------------------------

        get chips() {
            return Array.from(this.root.querySelectorAll('[data-timeline-category]'));
        }

        get slider() {
            return this.root.querySelector('.hx-timeline__range [data-slider]');
        }

        get shown() {
            return this.chips.filter((c) => c.getAttribute('aria-pressed') === 'true').map((c) => c.dataset.timelineCategory);
        }

        get bounds() {
            const s = this.slider.dataset;
            return [Number(s.sliderMin), Number(s.sliderMax)];
        }

        get span() {
            const inputs = this.slider.querySelectorAll('input[type=hidden]');
            return [Number(inputs[0].value), Number(inputs[1].value)];
        }

        // --- Events ---------------------------------------------------------

        bind() {
            this.root.addEventListener('click', (event) => {
                const chip = event.target.closest('[data-timeline-category]');
                const action = event.target.closest('[data-timeline-action]');
                const marker = event.target.closest('.hx-timeline__icon');
                if (chip) {
                    chip.setAttribute('aria-pressed', chip.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
                    this.changed();
                } else if (action) {
                    this.act(action.dataset.timelineAction);
                } else if (marker) {
                    this.open = marker.dataset.timelineKeys;
                    this.markOpen();
                    this.watchDrawer();
                }
            });
            this.slider.addEventListener('input', () => this.changed());
            new ResizeObserver(() => this.render()).observe(this.axis);
        }

        // Follow the drawer while a marker is open: once it is empty again,
        // no marker is open any more. (Its close button is swapped out with
        // the content, so htmx events of the close don't reach the document.)
        watchDrawer() {
            const drawer = document.getElementById('drawer-content')?.closest('.hx-drawer');
            if (!drawer || this.drawerObserver) return;
            this.drawerObserver = new MutationObserver(() => {
                if (drawer.querySelector(':scope > aside > section > *')) return;
                this.drawerObserver.disconnect();
                this.drawerObserver = null;
                this.open = null;
                this.markOpen();
            });
            this.drawerObserver.observe(drawer, { childList: true, subtree: true });
        }

        act(action) {
            if (action === 'reset') {
                this.slider.dispatchEvent(new CustomEvent('hx-slider:set', { detail: { values: this.bounds } }));
                return;
            }
            const wanted = action === 'all' ? null : this.defaults;
            this.chips.forEach((c) => c.setAttribute(
                'aria-pressed', !wanted || wanted.includes(c.dataset.timelineCategory) ? 'true' : 'false',
            ));
            this.changed();
        }

        changed() {
            this.render();
            this.writeUrl();
        }

        writeUrl() {
            if (!this.query) return;
            const url = new URL(window.location.href);
            const shown = this.shown;
            const [from, to] = this.span;
            const [lo, hi] = this.bounds;
            const same = shown.length === this.defaults.length && shown.every((k) => this.defaults.includes(k));
            const set = (name, value, keep) => (keep ? url.searchParams.set(name, value) : url.searchParams.delete(name));
            set(this.query.categories, shown.join(','), !same);
            set(this.query.start, iso(from), from !== lo);
            set(this.query.end, iso(to), to !== hi);
            window.history.replaceState(window.history.state, '', url);
        }

        // --- Rendering ------------------------------------------------------

        text(name, values = {}) {
            const template = this.root.dataset[`text${name[0].toUpperCase()}${name.slice(1)}`] || '';
            return template.replace(/\{(\w+)\}/g, (_, key) => (key in values ? values[key] : `{${key}}`));
        }

        format(day, unit, withYear) {
            const options = { timeZone: 'UTC' };
            if (unit === 'year') options.year = 'numeric';
            else if (unit === 'quarter' || unit === 'month') {
                options.month = 'short';
                if (withYear) options.year = 'numeric';
            } else {
                options.day = 'numeric';
                options.month = 'short';
                if (withYear) options.year = 'numeric';
            }
            return new Intl.DateTimeFormat(this.lang, options).format(new Date(day * DAY_MS));
        }

        date(day) {
            return new Intl.DateTimeFormat(this.lang, { timeZone: 'UTC', dateStyle: 'medium' }).format(new Date(day * DAY_MS));
        }

        render() {
            const width = this.axis.clientWidth;
            if (!width) return;
            const [from, to] = this.span;
            const shown = new Set(this.shown);
            const inner = width - 2 * PAD;
            const x = (day) => PAD + ((day - from) / Math.max(1, to - from)) * inner;
            const visible = this.events.filter((e) => shown.has(e.category) && e.to >= from && e.from <= to);
            // A period that began before the span sits at the axis' start.
            const markers = place(visible.map((e) => ({ x: Math.max(PAD, x(e.from)), event: e })));

            const nodes = [];
            const { unit, ticks: list } = ticks(from, to, inner);
            // The year at each January and at the first tick; on a narrow axis
            // at the first tick only if no January shows it.
            const anyMajor = list.some((t) => t.major);
            list.forEach((t, i) => {
                const withYear = t.major || (i === 0 && (!anyMajor || inner >= 480));
                nodes.push(this.tick(x(t.day), t.major, this.format(t.day, unit, withYear)));
            });
            nodes.push(Object.assign(document.createElement('span'), { className: 'hx-timeline__line' }));
            visible.filter((e) => e.end).forEach((e, i) => {
                const a = Math.max(PAD, x(e.from));
                const b = Math.min(PAD + inner, x(e.to));
                const bar = document.createElement('span');
                bar.className = 'hx-timeline__period';
                bar.dataset.lane = String(i % 2);
                bar.title = e.label;
                bar.style.setProperty('--timeline--x', `${a}px`);
                bar.style.setProperty('--timeline--width', `${Math.max(2, b - a)}px`);
                bar.style.setProperty('--timeline--color', this.colors.get(e.category));
                nodes.push(bar);
            });
            markers.forEach((m) => nodes.push(this.marker(m)));
            if (!visible.length) {
                const empty = document.createElement('p');
                empty.className = 'hx-timeline__empty';
                empty.textContent = this.text('empty');
                nodes.push(empty);
            }
            this.axis.replaceChildren(...nodes);
            const fresh = Array.from(this.axis.querySelectorAll('[hx-get]'));
            if (window.htmx) fresh.forEach((n) => window.htmx.process(n));

            this.chips.forEach((c) => {
                const key = c.dataset.timelineCategory;
                const n = this.events.filter((e) => e.category === key && e.to >= from && e.from <= to).length;
                c.querySelector('.hx-timeline__chip-count').textContent = String(n);
            });
            this.root.querySelector('.hx-timeline__summary').textContent = this.text('summary', {
                shown: visible.length, total: this.events.length, markers: markers.length,
            });
            this.renderRange(from, to, shown);
        }

        tick(px, major, label) {
            const tick = document.createElement('span');
            tick.className = 'hx-timeline__tick';
            if (major) tick.dataset.major = '';
            tick.style.setProperty('--timeline--x', `${px}px`);
            const text = document.createElement('span');
            text.className = 'hx-timeline__tick-label';
            text.textContent = label;
            tick.append(text);
            return tick;
        }

        marker(m) {
            const categories = new Set(m.events.map((e) => e.category));
            const single = categories.size === 1 ? [...categories][0] : null;
            const warn = m.events.some((e) => e.warn);
            const keys = m.events.map((e) => e.key);
            const [side, distance] = PLACES[m.slot];

            const root = document.createElement('div');
            root.className = 'hx-timeline__marker';
            root.dataset.side = side < 0 ? 'above' : 'below';
            if (warn) root.dataset.warn = '';
            if (!single) root.dataset.mixed = '';
            root.style.setProperty('--timeline--x', `${m.x}px`);
            root.style.setProperty('--timeline--distance', `${distance}px`);
            if (single) root.style.setProperty('--timeline--color', this.colors.get(single));

            const stem = document.createElement('span');
            stem.className = 'hx-timeline__stem';
            const dot = document.createElement('span');
            dot.className = 'hx-timeline__dot';

            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'hx-timeline__icon';
            button.dataset.timelineKeys = keys.join(',');
            const query = keys.map((k) => `key=${encodeURIComponent(k)}`).join('&');
            button.setAttribute('hx-get', `${this.url}${this.url.includes('?') ? '&' : '?'}${query}`);
            button.setAttribute('hx-target', '#drawer-content');
            button.setAttribute('hx-swap', 'none');
            button.setAttribute('aria-expanded', this.open === button.dataset.timelineKeys ? 'true' : 'false');
            const first = m.events[0];
            const lastEvent = m.events[m.events.length - 1];
            const dates = first.from === lastEvent.from
                ? this.date(first.from) : `${this.date(first.from)} – ${this.date(lastEvent.from)}`;
            let label = m.events.length === 1 ? first.label : this.text('group', { n: m.events.length, dates });
            if (warn) label = `${label}, ${this.text('warn')}`;
            button.setAttribute('aria-label', label);
            button.title = label;

            if (single) {
                const template = this.icons.get(single);
                if (template) button.append(this.icon(template));
            } else {
                const count = document.createElement('span');
                count.className = 'hx-timeline__count';
                count.textContent = String(m.events.length);
                button.append(count);
            }
            if (single && m.events.length > 1) {
                const badge = document.createElement('span');
                badge.className = 'hx-timeline__badge';
                badge.setAttribute('aria-hidden', 'true');
                badge.textContent = String(m.events.length);
                button.append(badge);
            }
            if (warn) {
                const flag = document.createElement('span');
                flag.className = 'hx-timeline__flag';
                flag.setAttribute('aria-hidden', 'true');
                flag.textContent = '!';
                button.append(flag);
            }
            root.append(stem, dot, button);
            return root;
        }

        // A category's icon: Feather icons in a template aren't replaced by
        // `feather.replace()`, so they are turned into SVG here.
        icon(template) {
            const node = template.content.firstElementChild.cloneNode(true);
            const name = node.getAttribute?.('data-feather');
            if (name && window.feather?.icons[name]) {
                const holder = document.createElement('span');
                holder.innerHTML = window.feather.icons[name].toSvg({ 'aria-hidden': 'true', focusable: 'false' });
                return holder.firstElementChild;
            }
            return node;
        }

        markOpen() {
            this.axis.querySelectorAll('.hx-timeline__icon').forEach((b) => {
                b.setAttribute('aria-expanded', this.open === b.dataset.timelineKeys ? 'true' : 'false');
            });
        }

        renderRange(from, to, shown) {
            const label = this.root.querySelector('[data-timeline-span-label]');
            if (label) label.textContent = `${this.date(from)} – ${this.date(to)}`;
            this.root.querySelectorAll('[data-timeline-bound]').forEach((b) => {
                b.textContent = this.date(Number(b.dataset.timelineBound));
            });
            const bars = Array.from(this.root.querySelectorAll('[data-timeline-month]'));
            const counts = bars.map((bar) => {
                const [a, b] = bar.dataset.timelineMonth.split(',').map(Number);
                return this.events.filter((e) => shown.has(e.category) && e.from >= a && e.from < b).length;
            });
            const most = Math.max(1, ...counts);
            bars.forEach((bar, i) => {
                const [a, b] = bar.dataset.timelineMonth.split(',').map(Number);
                bar.style.setProperty('--timeline--height', `${Math.round((100 * counts[i]) / most)}%`);
                if (b > from && a < to) bar.dataset.inSpan = '';
                else delete bar.dataset.inSpan;
            });
            this.slider.querySelectorAll('[role=slider]').forEach((thumb, i) => {
                thumb.setAttribute('aria-valuetext', this.date(i ? to : from));
            });
        }
    }

    // --- Initialisation ------------------------------------------------------

    const initialized = new WeakSet();

    function init(root = document) {
        const roots = Array.from(root.querySelectorAll?.('[data-timeline]') ?? []);
        if (root.matches?.('[data-timeline]')) roots.push(root);
        roots.forEach((el) => {
            if (initialized.has(el)) return;
            initialized.add(el);
            new PyhxTimeline(el);
        });
    }

    window.PyhxTimeline = { ticks, place, init };
    document.addEventListener('DOMContentLoaded', () => init());
    document.addEventListener('htmx:afterSwap', (event) => init(event.target));
    document.addEventListener('htmx:load', (event) => init(event.target));
})();
