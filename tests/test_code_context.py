import json
import sys
from pathlib import Path

# Ensure package root on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from aether.code_context import build_context_map


def test_build_context_map(tmp_path):
    src = tmp_path / "example.py"
    src.write_text(
        '"""Example module."""\n\n'
        'def greet(name):\n    """Say hello."""\n    print("hello", name)\n',
        encoding="utf-8",
    )

    context = build_context_map(tmp_path)

    assert "example.py" in context
    assert context["example.py"]["summary"] == "Example module."

    greet = context["example.py"]["functions"]["greet"]
    assert greet["docstring"] == "Say hello."
    assert greet["calls"] == ["print"]
    assert greet["lines"] == 3

    saved = tmp_path / ".aether" / "context_map.json"
    assert saved.exists()
    with saved.open("r", encoding="utf-8") as fh:
        saved_data = json.load(fh)
    assert saved_data == context
