"""Generate ASCII heatmap from risk metrics.

This module reads a ``risk_map.json`` file produced by the historian and
renders an ASCII table highlighting per-file risk and churn.  Each row shows
simple bar charts so hotspots are easy to spot.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


def load_risk_map(path: Path) -> Dict[str, Dict[str, float]]:
    """Return risk map data from ``path``.

    The JSON structure may be either a mapping of filenames to metric dictionaries
    or a list of objects that include a ``filename`` field.  In all cases a
    ``dict`` mapping filenames to metric dictionaries is returned.
    """
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        result: Dict[str, Dict[str, float]] = {}
        for entry in data:
            name = entry.get("filename")
            if name:
                result[name] = {k: v for k, v in entry.items() if k != "filename"}
        return result
    return data


def _bar(value: float, *, width: int = 10) -> str:
    """Return a bar of ``width`` characters representing ``value``."""
    value = max(0.0, min(1.0, value))
    filled = int(round(value * width))
    return "█" * filled + " " * (width - filled)


def _priority(risk: float) -> str:
    """Map numeric risk to a textual priority level."""
    if risk >= 0.7:
        return "HIGH"
    if risk >= 0.4:
        return "MED"
    return "LOW"


def ascii_heatmap(risk_map_path: Path, *, width: int = 10) -> str:
    """Render an ASCII heatmap for ``risk_map_path``.

    Parameters
    ----------
    risk_map_path:
        Path to the ``risk_map.json`` file produced by Code Historian.
    width:
        Width of the bar charts for risk and churn.

    Returns
    -------
    str
        A string containing the formatted table.
    """
    risk_map = load_risk_map(risk_map_path)
    header = f"{'File':<40} {'Risk':<{width + 6}} {'Churn':<{width + 6}} Priority"
    lines = [header, "-" * len(header)]

    for file, metrics in sorted(risk_map.items(), key=lambda x: x[1].get('risk', 0), reverse=True):
        risk = float(metrics.get('risk', 0.0))
        churn = float(metrics.get('commit_factor', 0.0))
        line = (
            f"{file:<40} "
            f"{_bar(risk, width=width)} {risk:>5.2f} "
            f"{_bar(churn, width=width)} {churn:>5.2f} "
            f"{_priority(risk)}"
        )
        lines.append(line)

    return "\n".join(lines)


__all__ = ["ascii_heatmap", "load_risk_map"]
