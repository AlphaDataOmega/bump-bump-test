"""Render Markdown summary of trajectory data.

This module converts the cumulative reinforcement information stored in
``trajectory.json`` into a concise Markdown/ASCII report.  It mirrors the
terminal table layout used by other AETHER tooling and is intended for quick
human inspection of long‑term trends.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _load(path: Path) -> Dict[str, Any]:
    """Return JSON content from ``path`` if it exists."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _sparkline(history: List[Dict[str, Any]]) -> str:
    """Return a simple sparkline for ``history`` entries."""
    symbols = []
    for entry in history:
        if entry.get("change") == "resolved":
            symbols.append("✓")
            continue
        delta = entry.get("reinforcement", 0)
        if delta > 0:
            symbols.append("↑")
        elif delta < 0:
            symbols.append("↓")
        else:
            symbols.append("-")
    return "".join(symbols)


def _status(entry: Dict[str, Any]) -> str:
    """Determine long‑term status for a trajectory ``entry``."""
    last_change = entry.get("last_change")
    if last_change == "resolved":
        return "Resolved"

    history = entry.get("history", [])
    deltas = [h.get("reinforcement", 0) for h in history]
    if deltas:
        if all(d >= 0 for d in deltas):
            return "Healing"
        if all(d <= 0 for d in deltas):
            return "Regressing"
    total = entry.get("total_reinforcement", 0)
    if total > 0 and last_change == "risk_down":
        return "Healing"
    if total < 0 and last_change == "risk_up":
        return "Regressing"
    if any(d > 0 for d in deltas) and any(d < 0 for d in deltas):
        return "Oscillating"
    return "Oscillating"


def render_trajectory_summary(trajectory_path: Path, output_path: Path) -> str:
    """Render a trajectory summary and write it to ``output_path``.

    Parameters
    ----------
    trajectory_path:
        Path to ``trajectory.json``.
    output_path:
        Destination for the summary file.

    Returns
    -------
    str
        The rendered summary text.
    """
    data = _load(trajectory_path)

    title = "📈 AETHER Trajectory Summary"
    header = "File              Total Δ   Last Change   Status       History"
    divider = "─" * len(header)
    lines = [title, divider, header, divider]

    for fname, info in sorted(data.items()):
        total = info.get("total_reinforcement", 0)
        last = info.get("last_change", "")
        status = _status(info)
        history = _sparkline(info.get("history", []))
        line = f"{fname:<17} {total:>6}   {last:<12} {status:<11} {history}"
        lines.append(line)

    output = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output + "\n", encoding="utf-8")
    return output


__all__ = ["render_trajectory_summary"]
