# GitHub Collaboration Workflow

This repository uses GitHub as the bridge between ChatGPT planning/review and Codex implementation.

## Roles

- ChatGPT: reads Issues, PR diffs, `CHATGPT_REVIEW.md`, and handoff files; proposes risks, review findings, and patch suggestions.
- Codex: performs local edits, runs local checks, writes `CODEX_FEEDBACK.md`, writes handoff records, commits changes, and opens PRs.
- GitHub: stores Issues, branches, commits, PR diffs, review discussions, and merge history.
- User: approves scope, confirms high-risk actions, and decides whether to merge or request changes.

## Standard Loop

1. Create a GitHub Issue for one task.
2. Ask ChatGPT to write or update `CHATGPT_REVIEW.md` with the task plan and risks.
3. Codex starts from the latest `main`.
4. Codex creates a task branch named `task_000_short-name`.
5. Codex implements only the approved local changes.
6. Codex updates `CODEX_FEEDBACK.md`.
7. Codex writes `docs/handoff/YYYY-MM-DD_task_000_short-name.md`.
8. Codex checks `git status`.
9. Codex stages only explicit files. Do not use `git add .`.
10. Codex reviews `git diff --cached`.
11. Codex commits and pushes the task branch.
12. Codex opens a PR to `main`.
13. ChatGPT reviews the PR diff and handoff file.
14. User merges or requests changes.

## Command Pattern

```bash
git checkout main
git pull origin main
git checkout -b task_000_short-name

# edit files

git status
git add <explicit-file-1> <explicit-file-2>
git diff --cached
git commit -m "task_000: short summary"
git push -u origin task_000_short-name
```

Create the PR after push, then give ChatGPT the PR link for review.

## Safety Rules

- Do not use `git add .`.
- Do not commit tokens, SSH keys, `.env` files, credentials, or machine-local configuration.
- Do not commit VASP runtime outputs such as `OUTCAR`, `WAVECAR`, `CHGCAR`, `vasprun.xml`, or Slurm logs.
- Do not commit large local reference bundles unless the user explicitly approves.
- Do not run `ssh lilin`, `sbatch`, remote deletion, or remote write operations without explicit user approval.

## Persistent Files

- `CHATGPT_REVIEW.md`: ChatGPT planning and review notes for the current task.
- `CODEX_FEEDBACK.md`: Codex execution summary for the current task.
- `docs/handoff/`: per-task execution handoff records.
- `.github/ISSUE_TEMPLATE/task.md`: GitHub Issue template.
- `.github/PULL_REQUEST_TEMPLATE.md`: GitHub PR template.

