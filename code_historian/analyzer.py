import ast
import os
import re
from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple

from git import Repo

TODO_PATTERN = re.compile(r"#.*\b(TODO|FIXME)\b", re.IGNORECASE)
NULL_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'

def get_function_ranges(source: str) -> List[Tuple[str, int, int]]:
    """Return list of (name, start, end) for functions in source."""
    functions = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = getattr(node, 'end_lineno', None)
            if end is None:
                # Fallback: find max line number in body
                end = max((getattr(n, 'lineno', start) for n in ast.walk(node)), default=start)
            functions.append((node.name, start, end))
    return functions

def extract_changed_lines(patch: str) -> Set[int]:
    """Return set of line numbers changed in new file from patch text."""
    changed: Set[int] = set()
    new_line = 0
    for line in patch.splitlines():
        if line.startswith('@@'):
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                new_line = int(m.group(1)) - 1
        elif line.startswith('+'):
            new_line += 1
            changed.add(new_line)
        elif line.startswith('-'):
            # deletion: consider previous line number
            changed.add(new_line + 1)
        else:
            new_line += 1
    return changed

def scan_todos(repo_path: str) -> List[Dict[str, str]]:
    todos: List[Dict[str, str]] = []
    skip_dirs = {'.git', 'venv', 'node_modules', '__pycache__'}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if fname.endswith('.py'):
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, repo_path)
                try:
                    with open(full, 'r', encoding='utf-8') as fh:
                        for i, line in enumerate(fh, 1):
                            if TODO_PATTERN.search(line):
                                todos.append({'file': rel, 'line': i, 'text': line.strip()})
                except OSError:
                    continue
    return todos

def analyze_repository(repo_path: str) -> Dict[str, Any]:
    repo = Repo(repo_path)
    file_commit_counts: Dict[str, int] = defaultdict(int)
    function_commits: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
    test_failures: List[Dict[str, str]] = []
    temporal_churn: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for commit in repo.iter_commits():
        month = commit.committed_datetime.strftime("%Y-%m")
        for path in commit.stats.files.keys():
            file_commit_counts[path] += 1
            temporal_churn[path][month] += 1

        msg_lower = commit.message.lower()
        if 'test' in msg_lower and ('fail' in msg_lower or 'fix' in msg_lower or 'broken' in msg_lower):
            test_failures.append({'commit': commit.hexsha, 'message': commit.message.strip()})

        if commit.parents:
            diffs = commit.parents[0].diff(commit, create_patch=True)
        else:
            diffs = commit.diff(NULL_TREE, create_patch=True)

        for diff in diffs:
            path = diff.b_path or diff.a_path
            if not path or not path.endswith('.py'):
                continue
            try:
                blob = commit.tree / path
                source = blob.data_stream.read().decode('utf-8', errors='ignore')
            except Exception:
                continue
            functions = get_function_ranges(source)
            patch_text = diff.diff.decode('utf-8', errors='ignore')
            changed_lines = extract_changed_lines(patch_text)
            for line in changed_lines:
                for name, start, end in functions:
                    if start <= line <= end:
                        function_commits[(path, name)].add(commit.hexsha)

    high_churn_files = sorted(
        [{'file': f, 'commit_count': c} for f, c in file_commit_counts.items()],
        key=lambda x: x['commit_count'],
        reverse=True
    )[:10]

    high_churn_functions = [
        {'file': f, 'function': func, 'commit_count': len(commits)}
        for (f, func), commits in function_commits.items()
        if len(commits) >= 3
    ]

    todos = scan_todos(repo.working_tree_dir)

    temporal_churn_dict = {f: dict(months) for f, months in temporal_churn.items()}

    return {
        'high_churn_files': high_churn_files,
        'high_churn_functions': high_churn_functions,
        'todos': todos,
        'test_failures': test_failures,
        'temporal_churn': temporal_churn_dict,
    }
