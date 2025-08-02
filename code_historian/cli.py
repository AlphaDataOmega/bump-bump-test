import argparse
from .analyzer import analyze_repository
from .reporter import generate_reports


def main() -> None:
    parser = argparse.ArgumentParser(description="Code Historian")
    parser.add_argument('repo_path', help='Path to git repository')
    parser.add_argument('--output-dir', default='.', help='Directory for reports')
    args = parser.parse_args()

    data = analyze_repository(args.repo_path)
    generate_reports(data, args.output_dir)


if __name__ == '__main__':
    main()
