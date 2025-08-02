# AETHER Architecture

AETHER combines repository analysis, risk‑driven patch generation, autonomous rewrites and
self‑documentation.  The system is split across the **code_historian** package, which collects
metrics, and the **aether** package, which generates mutations and Git artefacts.

## Core Modules

| Module | Location | Responsibility |
| --- | --- | --- |
| `analyzer.py` | `code_historian/analyzer.py` | Scan the Git history for churn, track TODO markers and build per‑function edit metrics. |
| `evolution.py` | `code_historian/evolution.py` | Convert historian data into a risk map and evolution suggestions. |
| `reporter.py` | `code_historian/reporter.py` | Emit JSON and Markdown reports summarising churn and TODOs. |
| `memory.py` | `code_historian/memory.py` | Persist reports and risk information into the `.aether/` memory layer. |
| `feedback_aggregator.py` | `aether/feedback_aggregator.py` | Merge reinforcement feedback across runs and maintain `trajectory.json`. |
| `patch_writer.py` | `aether/patch_writer.py` | Create mirror files in `__aether_patch__/` annotated with risk suggestions. |
| `heatmap_generator.py` | `aether/heatmap_generator.py` | Produce an ASCII heatmap of risk versus churn for quick visual inspection. |
| `rewriter.py` | `aether/rewriter.py` | Apply AST strategies to generate mutated sources under `__aether_mutation__/` and write unified diffs. |
| `git_committer.py` | `aether/git_committer.py` | Stage mutated files, craft metadata‑rich commit messages and optionally create branches. |
| `pr_summary.py` | `aether/pr_summary.py` | Render `pull_request_summary.md` describing each mutation, risk score and strategy. |

## Data Flow

```
Git repository
   │
   ├─> analyze_repository()          # code_historian/analyzer.py
   │       collects churn, TODOs, test history
   │
   ├─> compute_risk_map()            # code_historian/evolution.py
   │       assigns per‑file risk metrics
   │
   ├─> save_memory()                 # code_historian/memory.py
   │       writes reports and risk_map to .aether/
   │
   ├─> write_patches()               # aether/patch_writer.py
   │       generates __aether_patch__ copies with suggestions
   │
   ├─> rewrite_from_risk_map()       # aether/rewriter.py
   │       emits rewritten files + *.diff under __aether_mutation__/
   │
   ├─> commit_mutations()            # aether/git_committer.py
   │       creates commits with risk/confidence metadata
   │
   └─> generate_summary()            # aether/pr_summary.py
           writes pull_request_summary.md for reviewers
```

## Memory and Artefacts

* `.aether/` – persistent memory containing `historian_report.*`, `risk_map.json`,
  `evolution_log.json` and reinforcement `trajectory.json`.
* `__aether_patch__/` – provisional patches with inline suggestions.
* `__aether_mutation__/` – committed mutations and `mutation_log.json`.

## Extensibility Points

* **Mutation strategies** – add new AST transforms inside `rewriter.py` and map them
  in `select_strategy`.
* **Risk model** – enhance `compute_risk_map` with additional metrics or ML‑based scoring.
* **Feedback loops** – feed richer evaluation data into `feedback_aggregator.py` to guide future runs.
* **CI integration** – invoke the historian and rewriter within continuous integration to
  automatically open pull requests.

AETHER’s modular design keeps each stage isolated yet composable, enabling future
agents or human collaborators to extend the system without disturbing its core pipeline.
