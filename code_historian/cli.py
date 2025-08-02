import argparse
import os
from git import InvalidGitRepositoryError, NoSuchPathError, Repo
from .analyzer import analyze_repository
from .reporter import generate_reports


def main() -> None:
    parser = argparse.ArgumentParser(description="Code Historian")
    parser.add_argument('repo_path', help='Path to git repository')
    parser.add_argument('--output-dir', default='.', help='Directory for reports')
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo_path)
    if not os.path.isdir(repo_path):
        parser.error(f"{repo_path} is not a directory")
    try:
        Repo(repo_path)
    except (InvalidGitRepositoryError, NoSuchPathError):
        parser.error(f"{repo_path} is not a git repository")

    data = analyze_repository(repo_path)
    generate_reports(data, args.output_dir)


if __name__ == '__main__':
    main()
