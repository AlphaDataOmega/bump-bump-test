# bump-bump-test

This repository houses the early prototype of **Code Historian**, a module that
scans a Git repository and summarizes its history for introspection.

## Usage

Run the historian against any repository:

```bash
python -m code_historian.cli /path/to/repo
```

This command generates `historian_report.json` and `historian_report.md` in the
current directory.

The report highlights high-churn files, frequently edited functions, unresolved
TODO/FIXME comments, test failures, and includes monthly churn timelines for
top files with ASCII sparklines for quick insight.

