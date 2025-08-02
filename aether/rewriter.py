"""Perform automated code rewrites based on risk suggestions.

This module parses a ``risk_map.json`` file and produces mutated copies of
high‑risk source files.  Each rewrite is written under ``__aether_mutation__``
so the original sources remain untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import ast
import difflib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .patch_writer import load_risk_map


class Confidence(str, Enum):
    """Confidence levels assigned to mutations."""

    HIGH = "HIGH_CONFIDENCE"
    LOW = "LOW_CONFIDENCE"


@dataclass
class RewriteResult:
    """Outcome of a rewrite operation."""

    original: Path
    mutated: Path
    strategy: str
    confidence: Confidence


def select_strategy(entry: Dict[str, Any]) -> Optional[str]:
    """Pick a rewrite strategy based on ``entry`` hints.

    The function looks at the ``suggestions`` field for keywords and returns a
    strategy identifier or ``None`` if no strategy matches.
    """

    suggestions = " ".join(entry.get("suggestions", [])).lower()
    if "docstring" in suggestions:
        return "insert_docstring"
    if "todo" in suggestions:
        return "complete_todo"
    if "split" in suggestions:
        return "split_function"
    return None


def _insert_docstring(source: str) -> str:
    """Insert placeholder docstrings into functions lacking them."""

    tree = ast.parse(source)
    lines = source.splitlines()

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if not ast.get_docstring(node):
                indent = " " * (node.col_offset + 4)
                doc = f'{indent}"""TODO: documented by AETHER."""  # [AETHER_REWRITE]'
                insert_line = node.body[0].lineno - 1
                lines.insert(insert_line, doc)
                break
    return "\n".join(lines) + "\n"


def _complete_todo(source: str) -> str:
    """Mark TODO comments as handled by AETHER."""

    replaced: List[str] = []
    for line in source.splitlines():
        if "TODO" in line:
            line = line.replace("TODO", "TODO handled by AETHER")
        replaced.append(line)
    return "\n".join(replaced) + "\n"


def _split_function(source: str) -> str:
    """Move the body of the first function into a helper."""

    tree = ast.parse(source)
    lines = source.splitlines()

    target: Optional[ast.FunctionDef] = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            target = node
            break
    if not target or target.end_lineno is None:
        return source

    indent = " " * target.col_offset
    helper_name = f"_{target.name}_impl"
    args = [a.arg for a in target.args.args]
    call_args = ", ".join(args)

    start = target.lineno - 1
    end = target.end_lineno

    body_lines = lines[target.lineno:end]
    wrapper: List[str] = [lines[start]]
    wrapper.append(
        f"{indent}    \"\"\"Split by AETHER into {helper_name}\"\"\"  # [AETHER_REWRITE]"
    )
    call_line = f"{indent}    return {helper_name}({call_args})" if call_args else f"{indent}    return {helper_name}()"
    wrapper.append(call_line)

    helper_def = [f"{indent}def {helper_name}({', '.join(args)}):"]
    helper_def.extend(body_lines)

    mutated_lines = lines[:start] + wrapper + lines[end:] + ["", *helper_def]
    return "\n".join(mutated_lines) + "\n"


def _write_diff(original: str, mutated: str, path: Path) -> None:
    """Write a unified diff between ``original`` and ``mutated`` to ``path``."""

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        mutated.splitlines(keepends=True),
        fromfile="original",
        tofile="mutated",
    )
    path.write_text("".join(diff), encoding="utf-8")


def rewrite_file(entry: Dict[str, Any], project_root: Path) -> Optional[RewriteResult]:
    """Apply a rewrite strategy to the file described by ``entry``."""

    strategy = select_strategy(entry)
    if not strategy:
        return None

    src_path = project_root / entry.get("filename", "")
    if not src_path.exists():
        return None

    with src_path.open("r", encoding="utf-8") as fh:
        original = fh.read()

    if strategy == "insert_docstring":
        mutated_src = _insert_docstring(original)
    elif strategy == "complete_todo":
        mutated_src = _complete_todo(original)
    elif strategy == "split_function":
        mutated_src = _split_function(original)
    else:
        mutated_src = original

    mut_path = project_root / "__aether_mutation__" / entry.get("filename", "")
    mut_path.parent.mkdir(parents=True, exist_ok=True)
    with mut_path.open("w", encoding="utf-8") as fh:
        fh.write(mutated_src)

    diff_path = mut_path.with_suffix(mut_path.suffix + ".diff")
    _write_diff(original, mutated_src, diff_path)

    risk = float(entry.get("risk_score", 0))
    confidence = Confidence.HIGH if risk > 0.85 else Confidence.LOW

    return RewriteResult(src_path, mut_path, strategy, confidence)


def rewrite_from_risk_map(
    risk_map_path: Path, project_root: Path, *, threshold: float = 0.7
) -> List[RewriteResult]:
    """Run rewrites for all qualifying entries in ``risk_map_path``."""

    entries = load_risk_map(risk_map_path)
    results: List[RewriteResult] = []
    for entry in entries:
        if float(entry.get("risk_score", 0)) < threshold:
            continue
        res = rewrite_file(entry, project_root)
        if res:
            results.append(res)
    return results


__all__ = [
    "RewriteResult",
    "Confidence",
    "select_strategy",
    "rewrite_file",
    "rewrite_from_risk_map",
]
