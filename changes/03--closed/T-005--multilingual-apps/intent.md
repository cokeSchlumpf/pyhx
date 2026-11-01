# T-005 Multilingual apps

## Problem

Some apps built with pyhx have to be offered in several languages, and today they can't be: the UI texts of pyhx itself (labels of components, page templates, the login pages) are hard-coded English strings, and apps have no supported way to mark and translate their own texts. Only number and date formatting in data tables follows the browser language (`negotiate_locale()` from `Accept-Language`); a user can't choose a language, nothing remembers it, and login mails don't know which language to use. CaseSight (T-003 of `app--casesight`) is the first app that needs it; the next apps will too, so pyhx should offer one pattern for all of them.

## Proposed outcome

- The language of a request is chosen in this order: the language stored in the session, the language of the signed-in user (commons 1.4, `RegisteredUser.locale`), the browser languages, the app's default; which languages an app offers is configured in `[app.pyhx.core]`.
- Apps mark texts with gettext-style functions and ship `.po` catalogs; an app's catalog overrides pyhx's, pyhx's covers its own texts in German, Italian and French; texts with variables (also markup) are translated as whole sentences.
- A language switcher stores the choice in the session and, for signed-in users, on the user; HTMX pages reload completely so nothing mixes languages.
- Number, date and relative time formatting follows the same language, through helpers apps can use too.
- A command updates catalogs from the code and checks them (missing, fuzzy, placeholders), usable in `poe check` of pyhx and of apps.
- A guide in the docs and the `user_auth` sample show it all.
- Not part of this change: translated validation errors and error pages (T-004 of `app--casesight`), right-to-left languages, the user's timezone, cache headers.

## Affected users and systems

- **Apps on pyhx:** can become multilingual; apps that do nothing keep working, but pyhx's own texts follow the browser language among the offered languages (default en, de, it, fr) and relative times are worded by Babel.
- **The auth addon:** registers the switch endpoint, passes the language to login mails.
- **commons:** pyhx requires commons 1.4.0 (T-007 of `lib--python-commons`).

## Constraints

- Backwards compatible within `versions/1` (a `feat`, minor release); no API removed.
- The language is resolved per request, safe under concurrent requests, no global state.
- Derived from the accepted spec of T-003 of `app--casesight` (R1–R16, R18, R26, R28, R29 and its deviation D1): [spec](https://github.com/cokeSchlumpf/app--casesight/blob/feature/multilingual-app/changes/02--open/T-003--multilingual-app/spec.md), [plan](https://github.com/cokeSchlumpf/app--casesight/blob/feature/multilingual-app/changes/02--open/T-003--multilingual-app/plan.md); its acceptance was delegated by the developer as long as this change stays within it.

## Open questions

None.
