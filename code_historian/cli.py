import argparse
import sys
import git

from .analyzer import analyze_repository
from .reporter import generate_reports


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

    generate_reports(data, args.output_dir)


if __name__ == '__main__':
    main()
