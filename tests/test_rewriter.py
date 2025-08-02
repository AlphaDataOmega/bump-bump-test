from pathlib import Path

from aether.rewriter import Confidence, rewrite_from_risk_map


def test_docstring_insertion(tmp_path: Path) -> None:
    source = "def foo(x):\n    # TODO\n    return x\n"
    module = tmp_path / "module.py"
    module.write_text(source)

    risk_map = tmp_path / "risk_map.json"
    risk_map.write_text(
        '[{"filename": "module.py", "risk_score": 0.9, "suggestions": ["add docstring"]}]'
    )

    results = rewrite_from_risk_map(risk_map, tmp_path, threshold=0.5)
    assert len(results) == 1

    mutated = tmp_path / "__aether_mutation__" / "module.py"
    assert mutated.exists()
    content = mutated.read_text()
    assert '"""TODO: documented by AETHER."""' in content
    # Ensure the original file is untouched
    assert module.read_text() == source
    assert results[0].confidence is Confidence.HIGH


def test_function_split_and_diff(tmp_path: Path) -> None:
    source = "def foo(x):\n    return x + 1\n"
    module = tmp_path / "module.py"
    module.write_text(source)

    risk_map = tmp_path / "risk_map.json"
    risk_map.write_text(
        '[{"filename": "module.py", "risk_score": 0.9, "suggestions": ["split function"]}]'
    )

    results = rewrite_from_risk_map(risk_map, tmp_path, threshold=0.5)
    assert len(results) == 1
    assert results[0].strategy == "split_function"

    mutated = tmp_path / "__aether_mutation__" / "module.py"
    diff_file = mutated.with_suffix(mutated.suffix + ".diff")
    assert mutated.exists()
    assert diff_file.exists()
    content = mutated.read_text()
    assert "_foo_impl" in content
