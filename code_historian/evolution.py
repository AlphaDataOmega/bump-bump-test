import os
from typing import Any, Dict, List

from git import Repo


def compute_risk_map(repo_path: str, data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Assign a risk score to each Python file in the repository."""
    repo = Repo(repo_path)
    files = [f for f in repo.git.ls_files().splitlines() if f.endswith('.py')]
    commit_counts = data.get('file_commit_counts', {})
    function_counts = data.get('function_edit_counts', {})
    todo_counts = data.get('todo_counts', {})

    max_commit = max(commit_counts.values(), default=1)
    max_function = max(function_counts.values(), default=1)
    max_todo = max(todo_counts.values(), default=1)

    risk_map: Dict[str, Dict[str, float]] = {}
    for f in files:
        commit_factor = commit_counts.get(f, 0) / max_commit if max_commit else 0.0
        function_factor = function_counts.get(f, 0) / max_function if max_function else 0.0
        todo_factor = todo_counts.get(f, 0) / max_todo if max_todo else 0.0
        base = os.path.basename(f).replace('.py', '')
        has_tests = any(base in os.path.basename(tf) and 'test' in os.path.basename(tf) for tf in files)
        test_factor = 0.0 if has_tests else 1.0
        risk = (commit_factor + function_factor + todo_factor + test_factor) / 4.0
        risk_map[f] = {
            'commit_factor': round(commit_factor, 3),
            'function_factor': round(function_factor, 3),
            'todo_factor': round(todo_factor, 3),
            'test_factor': test_factor,
            'risk': round(risk, 3),
        }
    return risk_map


def generate_evolution_log(risk_map: Dict[str, Dict[str, float]], todos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Produce evolution suggestions and prioritized TODOs."""
    suggestions: List[Dict[str, Any]] = []
    for path, metrics in risk_map.items():
        if metrics['risk'] >= 0.6:
            reasons = []
            if metrics['test_factor'] > 0:
                reasons.append('missing tests')
            if metrics['commit_factor'] > 0.5:
                reasons.append('high churn')
            if metrics['todo_factor'] > 0.5:
                reasons.append('many TODOs')
            if metrics['function_factor'] > 0.5:
                reasons.append('frequent function edits')
            reason_text = ', '.join(reasons) if reasons else 'elevated risk'
            suggestions.append({'file': path, 'risk': metrics['risk'], 'reason': reason_text})

    todo_priorities: List[Dict[str, Any]] = []
    for todo in todos:
        score = risk_map.get(todo['file'], {}).get('risk', 0.0)
        todo_priorities.append({**todo, 'risk': score})
    todo_priorities.sort(key=lambda x: x['risk'], reverse=True)

    return {
        'suggestions': suggestions,
        'todo_priorities': todo_priorities,
    }

