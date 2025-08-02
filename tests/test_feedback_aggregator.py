import json
import sys
from pathlib import Path

# Ensure package root on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from aether.feedback_aggregator import load_json, update_trajectory, save_trajectory


def test_feedback_aggregation(tmp_path: Path):
    prev = {
        "a.py": {
            "total_reinforcement": 2,
            "last_change": "risk_down",
            "history": [
                {"run": 1, "change": "risk_up", "reinforcement": -1},
                {"run": 2, "change": "risk_down", "reinforcement": 3},
            ],
        }
    }
    feedback = [
        {"filename": "a.py", "change": "resolved", "reinforcement": 1},
        {"filename": "b.py", "change": "risk_up", "reinforcement": -2},
    ]
    updated = update_trajectory(feedback, prev, run_id=3)

    assert updated["a.py"]["total_reinforcement"] == 3
    assert updated["a.py"]["last_change"] == "resolved"
    assert updated["a.py"]["history"][-1] == {"run": 3, "change": "resolved", "reinforcement": 1}
    assert updated["b.py"]["total_reinforcement"] == -2

    path = tmp_path / "trajectory.json"
    save_trajectory(updated, path)
    assert json.loads(path.read_text()) == updated

    assert load_json(path) == updated
    assert load_json(tmp_path / "missing.json") == {}


def test_update_trajectory_no_feedback():
    prev = {"a.py": {"total_reinforcement": 1, "history": []}}
    updated = update_trajectory({}, prev, run_id=1)
    assert updated == prev
