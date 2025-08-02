import json
from pathlib import Path

from aether.pr_summary import generate_summary


def test_generate_summary(tmp_path: Path) -> None:
    log = [
        {
            "filename": "foo.py",
            "summary": "Refactor foo",
            "risk_score": 0.5,
            "confidence": "MEDIUM",
            "strategy": "split",
        }
    ]
    log_path = tmp_path / "mutation_log.json"
    log_path.write_text(json.dumps(log))
    diff_path = tmp_path / "foo.py.diff.md"
    diff_path.write_text("diff")

    summary_path = generate_summary(log_path)
    content = summary_path.read_text()
    assert "AETHER Pull Request Summary" in content
    assert "foo.py" in content
    assert "Refactor foo" in content
    assert str(diff_path) in content
