# GitHub Collaboration Workflow

This repository uses GitHub as the bridge between ChatGPT planning/review and Codex implementation.

## Roles

- ChatGPT: reads Issues, PR diffs, `CHATGPT_REVIEW.md`, and handoff files; proposes risks, review findings, and patch suggestions.
- Codex: performs local edits, runs local checks, writes `CODEX_FEEDBACK.md`, writes handoff records, commits changes, and opens PRs.
- GitHub: stores Issues, branches, commits, PR diffs, review discussions, and merge history.
- User: approves scope, confirms high-risk actions, and decides whether to merge or request changes.

## Standard Loop

1. Confirm GitHub CLI access before reading PR/Issue comments, creating Issues, opening PRs, or pushing branches.
2. Create a GitHub Issue for one task.
3. Ask ChatGPT to write or update `CHATGPT_REVIEW.md` with the task plan and risks.
4. Codex starts from the latest `main`.
5. Codex creates a task branch named `task_000_short-name`.
6. Codex implements only the approved local changes.
7. Codex updates `CODEX_FEEDBACK.md`.
8. Codex writes `docs/handoff/YYYY-MM-DD_task_000_short-name.md`.
9. Codex records the actual changed-file count, large-file status, and scope exceptions.
10. Codex checks `git status`.
11. Codex stages only explicit files. Do not use `git add .`.
12. Codex reviews `git diff --cached`.
13. Codex commits and pushes the task branch.
14. Codex opens a PR to `main`.
15. ChatGPT reviews the PR diff and handoff file.
16. User merges or requests changes.

## GitHub CLI Preflight

In PowerShell, check authentication with:

```powershell
gh auth status --hostname github.com
```

If not logged in, run:

```powershell
gh auth login --hostname github.com --web --git-protocol https
```

If `gh` is installed but not on PATH on Windows, try the full executable path:

```powershell
& 'C:\Program Files\GitHub CLI\gh.exe' auth status --hostname github.com
```

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
- If a PR contains a reference bundle, PDF, image set, third-party source tree, or binary, list the reason, file count, size summary, and user approval in the PR and handoff.
- Keep local workflow mirror changes separate from claims about the server execution source. A local mirror edit does not change `lilin`.
- Do not run `ssh lilin`, `sbatch`, remote deletion, or remote write operations without explicit user approval.

## Diff Reality Check

Every PR should state:

- The actual changed-file count.
- Whether large files, binaries, PDFs, images, or third-party materials were added.
- Whether `vasp_references资料/` changed.
- Whether `scripts/remote-workflow/` changed.
- Whether the formal skill directory changed.
- Whether the server execution source changed. This should normally be `no`.

## Persistent Files

- `CHATGPT_REVIEW.md`: ChatGPT planning and review notes for the current task.
- `CODEX_FEEDBACK.md`: Codex execution summary for the current task.
- `docs/handoff/`: per-task execution handoff records.
- `.github/ISSUE_TEMPLATE/task.md`: GitHub Issue template.
- `.github/PULL_REQUEST_TEMPLATE.md`: GitHub PR template.
