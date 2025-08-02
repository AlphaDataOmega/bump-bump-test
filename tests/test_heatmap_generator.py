import json
import sys
from pathlib import Path

# Ensure the package root is on the path when tests are executed directly.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from aether.heatmap_generator import ascii_heatmap, _bar


def test_bar_helper():
    assert _bar(0.5, width=10) == "█" * 5 + " " * 5
    assert _bar(0.0, width=3) == " " * 3
    assert _bar(1.0, width=3) == "█" * 3


def test_ascii_heatmap(tmp_path: Path):
    data = {
        "a.py": {"risk": 0.8, "commit_factor": 0.6},
        "b.py": {"risk": 0.2, "commit_factor": 0.1},
    }
    risk_map = tmp_path / "risk_map.json"
    risk_map.write_text(json.dumps(data))
    output = ascii_heatmap(risk_map, width=5)
    assert "a.py" in output and "HIGH" in output
    assert "b.py" in output and "LOW" in output
