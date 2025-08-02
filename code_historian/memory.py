import json
import os
import shutil
from typing import Any, Dict


def save_memory(repo_path: str, report_dir: str, evolution_log: Dict[str, Any], risk_map: Dict[str, Dict[str, float]]) -> None:
    """Persist historian outputs and evolution data to .aether directory."""
    memory_dir = os.path.join(repo_path, '.aether')
    os.makedirs(memory_dir, exist_ok=True)

    src_json = os.path.join(report_dir, 'historian_report.json')
    src_md = os.path.join(report_dir, 'historian_report.md')
    dst_json = os.path.join(memory_dir, 'historian_report.json')
    dst_md = os.path.join(memory_dir, 'historian_report.md')

    if os.path.abspath(src_json) != os.path.abspath(dst_json):
        if os.path.exists(src_json):
            shutil.copy(src_json, dst_json)
    if os.path.abspath(src_md) != os.path.abspath(dst_md):
        if os.path.exists(src_md):
            shutil.copy(src_md, dst_md)

    with open(os.path.join(memory_dir, 'evolution_log.json'), 'w', encoding='utf-8') as ef:
        json.dump(evolution_log, ef, indent=2)
    with open(os.path.join(memory_dir, 'risk_map.json'), 'w', encoding='utf-8') as rf:
        json.dump(risk_map, rf, indent=2)
