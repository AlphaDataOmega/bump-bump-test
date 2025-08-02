import sys
from pathlib import Path

# Ensure package root on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from aether.rewrite_enhancer import gather_rewrite_hints


def test_gather_rewrite_hints():
    context = {
        "mod.py": {
            "summary": "",
            "functions": {
                "big": {"docstring": "", "calls": ["a", "b", "c", "d", "e"], "lines": 45},
                "mystery": {"docstring": "", "calls": [], "lines": 3},
                "helper": {"docstring": "", "calls": ["print"], "lines": 10},
                "process_data": {"docstring": "Convert value.", "calls": [], "lines": 5},
            },
        }
    }

    hints = gather_rewrite_hints(context)

    assert [h.function for h in hints] == [
        "big",
        "mystery",
        "helper",
        "process_data",
    ]
    assert hints[0].docstring == "big calls a, b, c, d, e."
    assert hints[1].docstring == "mystery performs no calls."
    assert hints[2].docstring == "helper calls print."
    assert hints[3].rename_to == "convert_process_data"
