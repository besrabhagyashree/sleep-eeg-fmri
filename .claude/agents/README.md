# Project agents

Specialist Claude Code subagents for this project. They load automatically when Claude Code is opened in this folder. Reviewers and auditors are read-only: they report problems and never change code or results.

| Agent | Job |
|---|---|
| `test-guardian` | Runs the code check, compile check and test suite; explains failures; never weakens a test |
| `code-reviewer` | Reviews every diff for the error types this project has hit (in-place mutation, leakage, wrong formulas) and the author's established-methods rule |
| `qc-auditor` | Checks every recording's quality results against the pre-registered rules and flags anomalies |
| `citation-checker` | Verifies references against Crossref |
| `results-auditor` | Re-computes key results with independent code before they are written up |
| `pipeline-runner` | Starts and monitors long pipeline jobs and diagnoses failures from logs |

They are published here for transparency about how AI tools were used in this project. The always-on safety net is the GitHub Actions test workflow, which runs on every push without AI.
