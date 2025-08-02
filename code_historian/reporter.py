import json
import os
from typing import Any, Dict, List

SPARK_CHARS = "▁▂▃▄▅▆▇"


def sparkline(values: List[int]) -> str:
    if not values:
        return ""
    max_val = max(values)
    if max_val == 0:
        return ""
    scale = len(SPARK_CHARS) - 1
    return ''.join(SPARK_CHARS[int(v / max_val * scale)] for v in values)


def generate_reports(data: Dict[str, Any], output_dir: str) -> None:
    json_path = os.path.join(output_dir, "historian_report.json")
    md_path = os.path.join(output_dir, "historian_report.md")

    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(data, jf, indent=2)

    lines = ["# Code Historian Report\n"]

    lines.append("## High Churn Files\n")
    if data['high_churn_files']:
        lines.append('| File | Commit Count |\n')
        lines.append('| --- | ---: |\n')
        for item in data['high_churn_files']:
            lines.append(f"| {item['file']} | {item['commit_count']} |\n")
    else:
        lines.append('No file changes detected.\n')

    lines.append('\n## Functions with 3+ Changes\n')
    if data['high_churn_functions']:
        lines.append('| File | Function | Commit Count |\n')
        lines.append('| --- | --- | ---: |\n')
        for item in data['high_churn_functions']:
            lines.append(f"| {item['file']} | {item['function']} | {item['commit_count']} |\n")
    else:
        lines.append('No functions with 3+ changes.\n')

    lines.append('\n## TODOs / FIXMEs\n')
    if data['todos']:
        lines.append('| File | Line | Text |\n')
        lines.append('| --- | ---: | --- |\n')
        for todo in data['todos']:
            lines.append(f"| {todo['file']} | {todo['line']} | {todo['text']} |\n")
    else:
        lines.append('No TODOs or FIXMEs found.\n')

    lines.append('\n## Test Failures\n')
    if data['test_failures']:
        lines.append('| Commit | Message |\n')
        lines.append('| --- | --- |\n')
        for t in data['test_failures']:
            lines.append(f"| {t['commit']} | {t['message']} |\n")
    else:
        lines.append('No test failures found.\n')

    lines.append('\n## Temporal Churn\n')
    for item in data['high_churn_files']:
        file_path = item['file']
        churn = data['temporal_churn'].get(file_path, {})
        if not churn:
            continue
        months = sorted(churn.items())
        counts = [count for _, count in months]
        spark = sparkline(counts)
        top_month, top_count = max(churn.items(), key=lambda x: x[1])
        lines.append(f"File: {file_path}\n")
        lines.append(f"Monthly Churn: {spark}\n")
        lines.append(f"Top Month: {top_month} ({top_count} commits)\n\n")

    lines.append('\n## Summary\n')
    for file_item in data['high_churn_files']:
        file_path = file_item['file']
        summary = f"{file_path} changed {file_item['commit_count']} times."
        funcs = [f for f in data['high_churn_functions'] if f['file'] == file_path]
        if funcs:
            func_desc = ', '.join(f"{f['function']} ({f['commit_count']})" for f in funcs)
            summary += f" Functions changed: {func_desc}."
        lines.append(f"- {summary}\n")

    with open(md_path, 'w', encoding='utf-8') as mf:
        mf.writelines(lines)
