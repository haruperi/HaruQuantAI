# Walkthrough: [Task / Feature Title]

> **Task ID:** `[FEAT-XXX | TASK-XXX]`
> **Status:** `[COMPLETED | VERIFIED]`

Append follow-up execution/correction iterations to this file.

## 1. Summary of Changes Made

Summary of changes matching the Implementation Plan:

- `[NEW]` / `[MODIFY]` / `[DELETE]` links to each changed file.

## 2. Verification Results

### Automated Test Suite

- Command run: `uv run pytest ...`
- Output summary: `XX passed in X.XXs`.

### Usage Evidence Run

- Command run: `uv run python tests/examples/...`
- Output summary / sample logs demonstrating realistic execution.

### Full Pipeline Check

- Command run: `uv run python scripts/ci_check.py`
- Output summary: Ruff formatting, Ruff linting, Mypy strict, AST checks, Pytest 80% coverage passed.

## 3. Deviations & Residuals

- Any approved deviations from the Implementation Plan, or `- NONE`.
- Working tree diff status (`git status`).
- Proposed commit message if committing this task.
- Proposed logical next steps, or `- NONE`.
