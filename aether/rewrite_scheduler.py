"""Schedule code rewrites based on reinforcement trajectory.

This module analyses the per-file reinforcement history produced by
:mod:`aether.feedback_aggregator` and decides which files should be
rewritten next.  Files that have shown no positive reinforcement over a
number of recent runs are considered stagnant and are scheduled for a
rewrite.  A simple ``cadence`` counter is maintained for each file to
record how many runs have passed since it was last scheduled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple, Any


@dataclass
class Schedule:
    """Result of scheduling rewrites for a run."""

    files: List[str]
    trajectory: Dict[str, Any]


def schedule_rewrites(
    trajectory: Dict[str, Any],
    run_id: int,
    *,
    stagnation_runs: int = 3,
) -> Schedule:
    """Determine which files should be rewritten for ``run_id``.

    Parameters
    ----------
    trajectory:
        Mapping of file names to reinforcement history and metadata.  The
        structure follows the output of
        :func:`aether.feedback_aggregator.update_trajectory`.
    run_id:
        Identifier for the current run.  When a file is scheduled the
        ``last_scheduled_run`` field is set to this value and the
        ``cadence`` counter is reset.
    stagnation_runs:
        Number of most recent runs to inspect for positive reinforcement.
        If none of the ``stagnation_runs`` most recent reinforcement values
        are greater than zero the file is considered stagnant.

    Returns
    -------
    Schedule
        Object containing the list of files to rewrite and the updated
        trajectory mapping including cadence information.
    """

    updated = {k: v.copy() for k, v in trajectory.items()}
    to_rewrite: List[str] = []

    for fname, info in updated.items():
        history = info.get("history", [])
        # Increment cadence; reset when scheduled for rewrite
        cadence = int(info.get("cadence", 0)) + 1
        info["cadence"] = cadence

        recent = history[-stagnation_runs:]
        if not any(h.get("reinforcement", 0) > 0 for h in recent):
            to_rewrite.append(fname)
            info["cadence"] = 0
            info["last_scheduled_run"] = run_id

    return Schedule(to_rewrite, updated)


__all__ = ["Schedule", "schedule_rewrites"]
