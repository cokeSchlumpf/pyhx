"""Tailwind-inspired utility CSS classes with semantic naming.

Follows the same compositional approach as Tailwind CSS — small, single-purpose
classes combined to build up styles — but uses semantic size tokens (xs, sm, md,
lg, xl) instead of raw numeric values (1, 2, 4, 8, 16). This keeps the API
readable and ties all values back to the PyHX design-token scale defined in
``theme.css``.

The ``StyleAttribute`` Literal type provides compile-time validation so that
only classes that exist in the CSS are accepted by Python components.

Usage::

    from pyhx.core.primitives import styles

    y.div(**styles("flex", "gap-md", "p-lg", "bg-neutral-050"))[...]

    # Merges with an existing class_:
    y.div(**styles("flex", "gap-md", class_="hx-card"))
    # → class_="flex gap-md hx-card"

Categories:
    - **Spacing**: padding (``p-``), margin (``m-``), gap (``gap-``)
    - **Color**: background (``bg-``), text (``text-``), border (``border-``)
    - **Border**: style (``border``), radius (``rounded-``)
    - **Layout**: flexbox (``flex``, ``items-``, ``justify-``), grid
      (``hx-grid``, ``hx-grid-span-``, ``hx-grid-align-``)
    - **Typography**: size (``text-``), weight (``font-``), family (``font-``),
      line-height (``leading-``), alignment, transform
"""

from typing import Literal

from .classnames import classnames

StyleAttribute = Literal[
    # Padding
    "p-none",
    "p-xs",
    "p-sm",
    "p-md",
    "p-lg",
    "p-xl",
    "p-2xl",
    "px-none",
    "px-xs",
    "px-sm",
    "px-md",
    "px-lg",
    "px-xl",
    "px-2xl",
    "py-none",
    "py-xs",
    "py-sm",
    "py-md",
    "py-lg",
    "py-xl",
    "py-2xl",
    "pt-none",
    "pt-xs",
    "pt-sm",
    "pt-md",
    "pt-lg",
    "pt-xl",
    "pt-2xl",
    "pr-none",
    "pr-xs",
    "pr-sm",
    "pr-md",
    "pr-lg",
    "pr-xl",
    "pr-2xl",
    "pb-none",
    "pb-xs",
    "pb-sm",
    "pb-md",
    "pb-lg",
    "pb-xl",
    "pb-2xl",
    "pl-none",
    "pl-xs",
    "pl-sm",
    "pl-md",
    "pl-lg",
    "pl-xl",
    "pl-2xl",
    # Margin
    "m-none",
    "m-xs",
    "m-sm",
    "m-md",
    "m-lg",
    "m-xl",
    "m-2xl",
    "mx-none",
    "mx-xs",
    "mx-sm",
    "mx-md",
    "mx-lg",
    "mx-xl",
    "mx-2xl",
    "mx-auto",
    "my-none",
    "my-xs",
    "my-sm",
    "my-md",
    "my-lg",
    "my-xl",
    "my-2xl",
    "mt-none",
    "mt-xs",
    "mt-sm",
    "mt-md",
    "mt-lg",
    "mt-xl",
    "mt-2xl",
    "mr-none",
    "mr-xs",
    "mr-sm",
    "mr-md",
    "mr-lg",
    "mr-xl",
    "mr-2xl",
    "mb-none",
    "mb-xs",
    "mb-sm",
    "mb-md",
    "mb-lg",
    "mb-xl",
    "mb-2xl",
    "ml-none",
    "ml-xs",
    "ml-sm",
    "ml-md",
    "ml-lg",
    "ml-xl",
    "ml-2xl",
    # Gap
    "gap-none",
    "gap-xs",
    "gap-sm",
    "gap-md",
    "gap-lg",
    "gap-xl",
    "gap-2xl",
    # Background color
    "bg-primary",
    "bg-secondary",
    "bg-purple",
    "bg-danger",
    "bg-warning",
    "bg-success",
    "bg-info",
    "bg-neutral-050",
    "bg-neutral-100",
    "bg-neutral-200",
    "bg-neutral-300",
    "bg-white",
    "bg-black",
    "bg-transparent",
    # Text color
    "text-primary",
    "text-secondary",
    "text-purple",
    "text-danger",
    "text-warning",
    "text-success",
    "text-info",
    "text-neutral-500",
    "text-neutral-700",
    "text-neutral-800",
    "text-neutral-900",
    "text-white",
    "text-black",
    "text-muted",
    "text-gradient-brand",
    # Border color
    "border-primary",
    "border-secondary",
    "border-purple",
    "border-danger",
    "border-warning",
    "border-success",
    "border-info",
    "border-neutral-200",
    "border-neutral-300",
    "border-neutral-400",
    # Border style
    "border",
    "border-t",
    "border-b",
    "border-l",
    "border-r",
    "border-dashed",
    "border-b-0",
    # Border radius
    "rounded-none",
    "rounded-sm",
    "rounded-md",
    "rounded-lg",
    "rounded-xl",
    "rounded-full",
    "rounded-l-none",
    "rounded-l-sm",
    "rounded-l-md",
    "rounded-l-lg",
    "rounded-r-none",
    "rounded-r-sm",
    "rounded-r-md",
    "rounded-r-lg",
    "rounded-t-md",
    "rounded-b-md",
    # Overflow
    "overflow-hidden",
    # Display
    "block",
    "inline-block",
    "inline",
    "flex",
    "inline-flex",
    "grid",
    "inline-grid",
    "contents",
    "hidden",
    # Flexbox layout
    "flex-row",
    "flex-col",
    "flex-wrap",
    "flex-nowrap",
    "flex-1",
    "flex-auto",
    "flex-none",
    "items-start",
    "items-center",
    "items-end",
    "items-stretch",
    "items-baseline",
    "justify-start",
    "justify-center",
    "justify-end",
    "justify-between",
    # Grid (hx-grid component)
    "hx-grid",
    "hx-grid-span-1",
    "hx-grid-span-2",
    "hx-grid-span-3",
    "hx-grid-span-4",
    "hx-grid-span-5",
    "hx-grid-span-6",
    "hx-grid-span-7",
    "hx-grid-span-8",
    "hx-grid-span-9",
    "hx-grid-span-10",
    "hx-grid-span-11",
    "hx-grid-span-12",
    "hx-grid-span-full",
    "hx-grid-align-top",
    "hx-grid-align-center",
    "hx-grid-align-bottom",
    "hx-grid-align-stretch",
    # Font size
    "text-xs",
    "text-sm",
    "text-base",
    "text-lg",
    "text-xl",
    "text-2xl",
    "text-3xl",
    # Font weight
    "font-light",
    "font-normal",
    "font-medium",
    "font-semibold",
    "font-bold",
    # Font family
    "font-sans",
    "font-heading",
    "font-mono",
    # Line height
    "leading-tight",
    "leading-normal",
    "leading-relaxed",
    # Text alignment
    "text-left",
    "text-center",
    "text-right",
    # Text transform
    "uppercase",
    "lowercase",
    "capitalize",
    # White-space
    "whitespace-normal",
    "whitespace-nowrap",
    "whitespace-pre",
    "whitespace-pre-line",
    "whitespace-pre-wrap",
    # Text overflow
    "truncate",
    "text-ellipsis",
    "text-clip",
    # Text decoration
    "underline",
    "overline",
    "line-through",
    "no-underline",
    # Vertical alignment
    "align-top",
    "align-middle",
    "align-bottom",
]


def styles(*styles: StyleAttribute, **kwargs) -> dict:
    """Merge utility class names into kwargs.

    Mirrors :func:`classnames` and :func:`merge_styles` in shape — positional
    arguments are the data, ``**kwargs`` are the spread-target, the return
    is a kwargs dict ready to spread onto an element. The utility class
    names are joined with any existing ``class_`` in kwargs.

    Args:
        *styles: ``StyleAttribute`` class names to apply.
        **kwargs: Additional element attributes. If ``class_`` is present,
            its value is merged with the utility class names.

    Returns:
        A copy of kwargs with ``class_`` set to the merged class string.

    Examples:
        >>> styles("flex", "gap-md", "p-lg")
        {'class_': 'flex gap-md p-lg'}

        >>> styles("flex", "gap-md", class_="hx-card", id="x")
        {'class_': 'flex gap-md hx-card', 'id': 'x'}
    """
    return classnames(list(styles), **kwargs)
