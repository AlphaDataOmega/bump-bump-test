"""Extract lightweight semantic context from Python files.

This module parses Python source files to build a minimal mapping of
high‑level semantics for each file.  For every module the top‑level
docstring is recorded as a short summary and information about declared
functions is gathered.  Function context includes its docstring, a list
of called functions and the number of source lines the function spans.

The resulting mapping can be written to ``.aether/context_map.json``
where it can be consumed by other AETHER components.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def _called_functions(node: ast.AST) -> List[str]:
    """Return sorted unique names of functions called within ``node``."""
    calls = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            func = n.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)
    return sorted(calls)


def extract_file_context(path: Path) -> Dict[str, object]:
    """Extract semantic context information from ``path``.

    Parameters
    ----------
    path:
        Location of the Python source file to analyse.

    Returns
    -------
    dict
        Mapping containing a ``summary`` of the module and metadata for
        each function definition found.
    """

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    doc = ast.get_docstring(tree) or ""
    summary = doc.strip().splitlines()[0] if doc else ""

    functions: Dict[str, Dict[str, object]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_doc = ast.get_docstring(node) or ""
            lines = getattr(node, "end_lineno", node.lineno) - node.lineno + 1
            functions[node.name] = {
                "docstring": func_doc.strip(),
                "calls": _called_functions(node),
                "lines": lines,
            }

    return {"summary": summary, "functions": functions}


def build_context_map(root: Path, *, output_path: Optional[Path] = None) -> Dict[str, object]:
    """Build a context map for all ``*.py`` files under ``root``.

    The map is also written to ``output_path`` which defaults to
    ``root/.aether/context_map.json``.
    """

    context: Dict[str, Dict[str, object]] = {}
    for file in sorted(root.rglob("*.py")):
        # Skip hidden directories except ``.aether``
        if any(part.startswith(".") and part != ".aether" for part in file.relative_to(root).parts[:-1]):
            continue
        context[str(file.relative_to(root))] = extract_file_context(file)

    out_dir = root / ".aether"
    out_dir.mkdir(exist_ok=True)
    out = output_path or (out_dir / "context_map.json")
    with out.open("w", encoding="utf-8") as fh:
        json.dump(context, fh, indent=2, sort_keys=True)
    return context


__all__ = ["extract_file_context", "build_context_map"]
