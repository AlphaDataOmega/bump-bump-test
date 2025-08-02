import sys
from pathlib import Path

# Ensure package root on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from aether.rewrite_scheduler import schedule_rewrites


def test_schedule_rewrites_stagnation():
    trajectory = {
        "a.py": {
            "history": [
                {"run": 1, "reinforcement": -1},
                {"run": 2, "reinforcement": 0},
            ],
            "cadence": 2,
        },
        "b.py": {
            "history": [
                {"run": 1, "reinforcement": 1},
                {"run": 2, "reinforcement": -1},
            ],
            "cadence": 2,
        },
        "c.py": {"history": []},
    }

    sched = schedule_rewrites(trajectory, run_id=3, stagnation_runs=2)

    assert set(sched.files) == {"a.py", "c.py"}
    assert sched.trajectory["a.py"]["cadence"] == 0
    assert sched.trajectory["b.py"]["cadence"] == 3
    assert sched.trajectory["c.py"]["cadence"] == 0
    assert sched.trajectory["c.py"]["last_scheduled_run"] == 3
