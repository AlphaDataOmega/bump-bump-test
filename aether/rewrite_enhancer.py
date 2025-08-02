"""Analyse context map to propose code rewrite hints.

This module consumes the context map produced by
:mod:`aether.code_context` and derives high level hints for potential
rewrites.  The goal is to highlight functions that would benefit from
additional documentation or structural changes based on simple
heuristics.

Returned hints include auto generated docstrings for functions that lack
one and rename suggestions when the function name appears misaligned with
its documented purpose.  Functions are scored so consumers can prioritise
more complex or under‑documented code for mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class RewriteHint:
    """Suggested actions for a function.

    Attributes
    ----------
    file:
        File containing the function.
    function:
        Name of the function within ``file``.
    score:
        Aggregate priority score based on heuristics.
    docstring:
        Auto generated docstring when the function lacks one.
    rename_to:
        Suggested new name when the current name appears to mismatch the
        documented purpose.
    """

    file: str
    function: str
    score: int
    docstring: Optional[str] = None
    rename_to: Optional[str] = None


def _auto_docstring(name: str, calls: Iterable[str]) -> str:
    """Generate a simple docstring from ``name`` and ``calls``."""

    calls = list(calls)
    if calls:
        return f"{name} calls {', '.join(calls)}."
    return f"{name} performs no calls."


def _rename_suggestion(name: str, docstring: str) -> Optional[str]:
    """Return a naive rename suggestion based on ``docstring``.

    The first word of the docstring is used as a verb.  If that verb does
    not appear in the function name a new name is suggested by prefixing
    the verb to the existing name.
    """

    if not docstring:
        return None
    first = docstring.split()[0].lower()
    if first in name.lower():
        return None
    return f"{first}_{name}"


def gather_rewrite_hints(context_map: Dict[str, Any]) -> List[RewriteHint]:
    """Analyse ``context_map`` and return rewrite hints.

    Functions are scored using the following heuristics:

    * missing docstring → +1
    * 5 or more function calls → +1
    * more than 40 lines of code → +1
    * missing docstring and no calls ("unknown purpose") → +1
    """

    hints: List[RewriteHint] = []
    for file, info in context_map.items():
        functions = info.get("functions", {})
        for fname, meta in functions.items():
            doc = meta.get("docstring", "").strip()
            calls = meta.get("calls", [])
            lines = int(meta.get("lines", 0))

            score = 0
            generated_doc: Optional[str] = None

            if not doc:
                score += 1
                generated_doc = _auto_docstring(fname, calls)
            if len(calls) >= 5:
                score += 1
            if lines > 40:
                score += 1
            if not doc and not calls:
                score += 1

            rename = _rename_suggestion(fname, doc)

            if score > 0 or rename:
                hints.append(
                    RewriteHint(
                        file=file,
                        function=fname,
                        score=score,
                        docstring=generated_doc,
                        rename_to=rename,
                    )
                )

    hints.sort(key=lambda h: h.score, reverse=True)
    return hints


__all__ = ["RewriteHint", "gather_rewrite_hints"]
