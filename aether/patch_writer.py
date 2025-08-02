"""Utilities for writing patch suggestions for high-risk files.

This module reads `.aether/risk_map.json` and generates patched copies of
high-risk files with suggestion comments inserted.  The patched files are
written to a mirror directory under `__aether_patch__` so the original source
is left untouched.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Dict, Any


def load_risk_map(path: Path) -> Iterable[Dict[str, Any]]:
    """Load risk map entries from ``path``.

    The risk map is expected to be a JSON object or list containing entries
    with ``filename``, ``risk_score`` and ``suggestions`` fields.  A best effort
    is made to normalise the structure into an iterable of dictionaries.
    """
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        return data.values()
    return data


def write_patches(risk_map_path: Path, project_root: Path, *, threshold: float = 0.7) -> list[Path]:
    """Generate patch files for high-risk entries.

    Parameters
    ----------
    risk_map_path:
        Path to the ``risk_map.json`` file.
    project_root:
        Root of the project so file paths can be resolved.
    threshold:
        Minimum ``risk_score`` required to generate a patch.

    Returns
    -------
    list[Path]
        Paths to the generated patch files.
    """
    entries = load_risk_map(risk_map_path)
    patched_files: list[Path] = []
    patch_root = project_root / "__aether_patch__"

    for entry in entries:
        filename = entry.get("filename")
        risk = entry.get("risk_score", 0)
        suggestions = entry.get("suggestions", [])

        if not filename or risk < threshold:
            continue

        source_path = project_root / filename
        if not source_path.exists():
            continue

        patch_path = patch_root / filename
        patch_path.parent.mkdir(parents=True, exist_ok=True)

        with source_path.open("r", encoding="utf-8") as fh:
            original = fh.read()

        suggestion_lines = [f"# [AETHER SUGGESTION]: {s}" for s in suggestions]
        suggestion_block = "\n".join(suggestion_lines)

        with patch_path.open("w", encoding="utf-8") as fh:
            if suggestion_block:
                fh.write(suggestion_block + "\n\n")
            fh.write(original)

        patched_files.append(patch_path)

    return patched_files


__all__ = ["write_patches", "load_risk_map"]
