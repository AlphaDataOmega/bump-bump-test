import argparse
import sys
import git
import time
from pathlib import Path

from .analyzer import analyze_repository
from .evolution import compute_risk_map, generate_evolution_log
from .memory import save_memory
from .reporter import generate_reports
from aether.feedback_aggregator import load_json, update_trajectory, save_trajectory


def main() -> None:
    parser = argparse.ArgumentParser(description="Code Historian")
    parser.add_argument('repo_path', help='Path to git repository')
    parser.add_argument('--output-dir', default='.', help='Directory for reports')
    args = parser.parse_args()

    try:
        data = analyze_repository(args.repo_path)
    except (git.exc.InvalidGitRepositoryError, FileNotFoundError):
        print(f"Error: {args.repo_path} is not a valid Git repository.", file=sys.stderr)
        sys.exit(1)

    risk_map = compute_risk_map(args.repo_path, data)
    evolution_log = generate_evolution_log(risk_map, data['todos'])

    generate_reports(data, args.output_dir)
    save_memory(args.repo_path, args.output_dir, evolution_log, risk_map)

    output_dir = Path(args.output_dir)
    run_id = int(time.time())
    trajectory_path = output_dir / "trajectory.json"

    prev = load_json(trajectory_path)
    feedback = load_json(output_dir / "evolution_feedback.json")
    updated = update_trajectory(feedback, prev, run_id)
    save_trajectory(updated, trajectory_path)


if __name__ == '__main__':
    main()
