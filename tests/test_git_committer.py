import json
import subprocess
from pathlib import Path

from aether.git_committer import commit_mutations


def test_commit_mutations(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (repo / "base.txt").write_text("base\n")
    subprocess.run(["git", "-C", str(repo), "add", "base.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "base"], check=True)

    mutation_dir = tmp_path / "mut"
    mutation_dir.mkdir()
    (mutation_dir / "new.txt").write_text("hello\n")
    log = [{
        "filename": "new.txt",
        "summary": "Add greeting",
        "risk_score": 0.1,
        "confidence": "LOW",
        "strategy": "test",
    }]
    (mutation_dir / "mutation_log.json").write_text(json.dumps(log))

    committed = commit_mutations(mutation_dir, repo_root=repo)
    assert committed == ["new.txt"]
    assert (repo / "new.txt").read_text() == "hello\n"
    log_out = subprocess.run(
        ["git", "-C", str(repo), "log", "--oneline"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "Add greeting" in log_out
