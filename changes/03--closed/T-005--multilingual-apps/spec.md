# T-005 Multilingual apps: spec

Requirements are numbered for this change; the number in brackets is the requirement of T-003 of `app--casesight` it comes from.

## Requirements

### Languages

- **R1** An app configures the languages it offers and its default in `[app.pyhx.core]` (`supported_locales`, `default_locale` of `LocaleSettings`); without configuration the defaults stay `["en", "de", "it", "fr"]` and `"en"`. (T-003 R1)
- **R2** The language of a request is the first of: the session language, the language of the signed-in user, the browser languages of `Accept-Language` by weight, the default; a regional variant counts as its language, a value not offered is skipped. (T-003 R2)
- **R3** It is resolved once per request (page or fragment) and used for all texts and formatting of that request; `negotiate_locale()` returns it, so data tables follow it. (T-003 R3)
- **R4** Outside a request the default applies, unless code sets one for a block with `use_locale()`. (T-003 R4)
- **R5** `<html lang>` is the request language. (T-003 R5)

### Switching

- **R6** `locale_switch()` returns the data of a language switcher (headless): the endpoint, the page to return to, the offered languages by their own name and the current one; the app renders it. (T-003 R6; see Outcome D5)
- **R7** Choosing a language stores it in the session and, for a signed-in registered user, on the user; HTMX requests get `HX-Refresh`, others a redirect to a relative `next` on the same origin (else `/`); a language not offered is rejected with 400 and nothing stored. (T-003 R7)
- **R8** Signing in and out keeps the session language. (T-003 R8)

### Translating

- **R9** `_`, `_n`, `_p` and `_l` (lazy) mark and translate texts; the English source text is the key. (T-003 R9)
- **R10** Placeholders are named and filled after translation; `t(…)` returns nodes so a placeholder can be markup, with the text escaped. (T-003 R10)
- **R11** Lookup order: the app's catalog, pyhx's catalog, the source text; missing catalogs or entries never fail a request. (T-003 R11)
- **R12** pyhx ships de, it and fr catalogs for every user-facing text of its components, page templates and authentication pages. (T-003 R12)
- **R13** `DrawerSelectLabels`, `DrawerRadioLabels`, `ConditionalSelectLabels` show their defaults in the request language, also after restoring serialized state; explicit labels are shown as set; `CalendarLabels` default to Babel's names. (T-003 R13)
- **R14** Relative times in data tables are formatted in the request language. (T-003 R14)
- **R15** `format_number`, `format_currency`, `format_percent`, `format_date`, `format_datetime`, `format_time`, `format_relative_time` format in the request language (and timezone) without a `locale` argument; the data tables use them. (T-003 R29)

### Catalog tooling and documentation

- **R16** `python -m pyhx.i18n update` extracts marked texts into the catalogs of all offered languages; `python -m pyhx.i18n check` fails, naming the entries, on outdated catalogs, empty or fuzzy entries and placeholder differences; `poe check` of pyhx runs the check on pyhx's catalogs. (T-003 R15)
- **R17** Guide `docs/guides/i18n.md` in the nav under "Building Apps"; `docs/guides/user-authentication.md` describes the language on sign-in and in login mails and is added to the nav; the `LocaleSettings` docstring is updated. (T-003 R16)
- **R18** `CLAUDE.md` has a project rule: user-facing texts are marked, and a change adding or changing texts updates the de, it, fr catalogs so `poe check` passes. (T-003 R26)
- **R19** `samples/user_auth` shows language selection for anonymous visitors and signed-in users (a second account with a stored language), the switcher, an app catalog with an override of a pyhx text, markup in a placeholder, a plural and a data table; `tests/samples/user_auth/` covers the flows. (T-003 R28)

### Login mails

- **R20** The email login passes the language for the requesting user (R2 with that user) to `LoginTokenService.request_login(locale=…)` of commons 1.4. (T-003 R18)

## Design

As designed in the spec of T-003 (section "pyhx"), with its deviation D1:

- New package `pyhx.i18n`: `resolve_locale(ctx, user=None)`, `use_locale()` (a `ContextVar`), `_`, `_n`, `_p`, `_l`, `t`, the format helpers and the catalog loader; `python -m pyhx.i18n update|check` in `pyhx/i18n/__main__.py`.
- `RequestContext.locale`: cached property calling `resolve_locale`; `negotiate_locale()` returns it inside a request.
- Catalogs: `.po` read at runtime with `babel.messages.pofile.read_po`, cached per language; app catalog `locale/<lang>/LC_MESSAGES/messages.po` under the project root (as `commons.settings` finds it) or `WebApp(locale_dir=…)`; pyhx catalog `src/pyhx/locale/<lang>/LC_MESSAGES/pyhx.po` as fallback.
- `*Labels`: fields `str | None = None`, `resolved()` at render time; `CalendarLabels` fields `None` by default and filled from `babel.dates`.
- Relative time with `babel.dates.format_timedelta(add_direction=True)`; `humanize` removed from the dependencies.
- Switch endpoint `POST /_pyhx/locale` registered by `configure_user_session` (D1 of T-003: it owns the session and the users repository); `locale_switch()` returns `None` without a session (D5).
- `skeleton.py` sets `lang`.
- The placeholder check compares `string.Formatter().parse` fields (Babel 2.18 checks only `%` formats).

## Alternatives considered

See the spec of T-003: Fluent, typed catalogs, starlette-babel, semantic keys, compiled `.mo` files, switching without a reload.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Backwards compatible within `versions/1` | R1 (defaults), R2 (browser language as before without session/user), R11 (source text fallback); behavior changes listed under concerns |
| Per request, concurrency-safe, no global state | R3, R4, R14 (`humanize` removed) |
| Within the spec of T-003 | R1–R20 map to it (brackets) |

## Open questions

None.

## Areas of concern

1. **Behavior changes for existing apps** (R12, R13, R14): pyhx texts appear translated when the browser asks for de/it/fr; relative times change wording slightly ("1 minute ago" instead of "a minute ago"). Listed in the PR; no API breaks. Owner: agent.
2. **Open redirect and input** (R7): `next` and `locale` come from the client; only relative paths and offered languages are accepted; tested. Owner: agent.
3. **Catalogs in the installed package** (R11, R12): `.po` files must be included when pyhx is installed from Git; a test loads them from the package path. Owner: agent.

## Out of scope

- Validation errors and error pages, right-to-left languages, the user's timezone, `Vary` and cache headers, language-specific mail templates.

## Outcome

Implemented as specified, with these deviations and findings (from the plan, removed at close-out):

- **D1** `_l` returns pyhx's own `LazyText` (`pyhx.core.primitives.lazy_text`) instead of Babel's `LazyProxy`, which htpy rejects as a child and as an attribute; `LazyText` renders as escaped text and translates on `str()`/`format()`. Page titles and navigation labels accept it (`Text = str | LazyText`) and become `str` when the page is rendered.
- **D2** In `samples/user_auth/main.py` the switcher sits at the top of the page (`AppShell` has no header slot); `samples/user_auth/canvas.py` shows it in the header of `CanvasShell`.
- **D3** Component parameters with English defaults default to `None` and get the translated default at render time (Boolean controls, taglist, dropdown and file dropzone placeholders, `drawer_action_table` title, `page_header` navigation label); `DataForm.submit_label` and the `DataFormDrawer` labels also accept a callable; the internal option tuples of `filter_options.py` became functions. Explicit values behave as before.
- **D4** `safe_next` (now in `_session.py`, shared by login and switcher) also rejects `/\…`, which browsers read as a protocol-relative URL; this also closes it for the login redirect.
- **D5** No switcher component: in the developer's review, a ready-made button row (`c.locale_switcher()`) was replaced by the headless `pyhx.i18n.locale_switch()`, since apps render the switcher in their own design; the sample builds its own buttons on it.
- **D6** `AppShell` and `CanvasShell` get a settings menu (`settings=`, default `(LanguageSetting(),)`): a gear in the header opening a `<details>` dropdown, one section per entry; `LanguageSetting` shows the languages as codes (EN | DE | IT | FR) in the existing `segment_control` (normal size), on top of `locale_switch()`, and submits on change (htmx); `SettingsLinks(SettingsLink(label, href, icon))` adds plain menu entries (the sample shows Profile and Sign out above the language). It replaces the AppShell's settings button, which did nothing, and is left out without a session, with one language or with `settings=()`. Designed in the developer's review (design canvas "pyhx Settings Menu"); screenshots in `screenshots/`.
- **F1** The change was started as T-004; the parallel change "login secondary links" was merged as T-004 first, so this one is T-005.
- **F2** pyhx's texts: about 160 marked in 27 files, 123 entries per catalog (de, it, fr), translated with an LLM; "Sign in" and "Sign In" both exist as source texts (different buttons, same translations).
- **F3** Catalog files are part of the wheel (checked with `poetry build`); `poe check` runs the catalog check for pyhx and for the sample.
- **F4** `humanize` is no longer a dependency; relative times are worded by Babel ("1 minute ago" instead of "a minute ago").

Rollout: PR #20, released as pyhx 1.3.0 on `versions/1` after the developer's review and merge; requires commons 1.4.0 (T-007 of `lib--python-commons`).

Open after this change: translated validation errors and error pages (T-004 of `app--casesight`); CaseSight adopts it in T-003 of `app--casesight`.
