import json
import sys
from pathlib import Path

# Ensure package root is on the path when tests run directly
sys.path.append(str(Path(__file__).resolve().parents[1]))

from aether.trajectory_report import render_trajectory_summary


def test_render_trajectory_summary(tmp_path: Path):
    data = {
        "a.py": {
            "total_reinforcement": 2,
            "last_change": "risk_down",
            "history": [
                {"run": 1, "change": "risk_up", "reinforcement": -1},
                {"run": 2, "change": "resolved", "reinforcement": 3},
            ],
        }
    }
    traj = tmp_path / "trajectory.json"
    traj.write_text(json.dumps(data))
    summary_path = tmp_path / "summary.md"

    output = render_trajectory_summary(traj, summary_path)

    assert "a.py" in output
    assert "Healing" in output
    assert "↓✓" in output
    assert summary_path.read_text() == output + "\n"

