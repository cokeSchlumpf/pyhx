# T-009 Canvas design at phone width

## Problem

At phone width (390 px) parts of the canvas design don't fit, seen in `samples/canvas_layout` (`/data-page`) after T-006 and T-008:

- The page header of a `DataPage` puts the title and its actions side by side; the actions take most of the row and the title breaks inside the word ("Fäll" / "e").
- The top bar keeps all items of `header_content` in one row: the brand is cut ("Canva…") and the last item runs out of the screen ("Ano…").
- Breadcrumbs above the title wrap word by word in the narrow column left of the actions.

The table itself is fine (it scrolls inside its card, the quick filters and the search wrap), so lists work on a phone, but every page with a header looks broken. Apps on the canvas design (case-sight) will be used on phones and tablets.

## Proposed outcome

- At narrow widths the page header stacks: breadcrumbs and title on top, the actions below (or as icon buttons), and a title never breaks inside a word.
- The top bar fits at phone width: the brand stays readable, and the items of `header_content` collapse (e.g. into a menu) or drop by priority instead of overflowing.
- Every page of `samples/canvas_layout` is checked at 390 px (list, detail page, dossier, forms, navigation pages) with screenshots; no horizontal scroll of the page.
- The default design (`AppShell`) is checked at the same width and only changed where it shows the same problems.
