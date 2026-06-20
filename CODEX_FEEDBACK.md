# CODEX_FEEDBACK.md

## GitHub Context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/3
- PR: pending
- Branch: `task_002_review-skill-rules`
- Task ID: `task_002_review-skill-rules`

## This Round Summary

- Started from the latest `main`.
- Created GitHub Issue #3 for `task_002: review skill rules`.
- Created local branch `task_002_review-skill-rules`.
- Reviewed `SKILL.md`, `agents/openai.yaml`, `docs/GITHUB_COLLABORATION_WORKFLOW.md`, the handoff template, and prior `CODEX_FEEDBACK.md`.
- Improved `SKILL.md` trigger conditions, operating boundaries, safety confirmation rules, and ChatGPT/Codex collaboration notes.
- Added GitHub CLI authentication preflight guidance to the collaboration workflow.
- Updated `agents/openai.yaml` so the default prompt matches the explicit SSH/Slurm/remote-write safety gates.

## Implemented Changes

- `SKILL.md` now states that the skill should also trigger for development tasks touching its rules, references, local mirror, agents, or handoff docs.
- `SKILL.md` now separates trigger/scope rules from server safety boundaries.
- `SKILL.md` now says local repository edits do not modify the installed skill, the `lilin` workflow, or real calculations unless separately requested.
- `docs/GITHUB_COLLABORATION_WORKFLOW.md` now includes a GitHub CLI preflight section with the required PowerShell login command.
- `agents/openai.yaml` now mentions local workflow review and the need for explicit confirmation before SSH, Slurm submission, remote writes, or installed-skill sync.

## Diff Reality Check

- Actual changed file count: 5.
- Large files added: no.
- Reference bundle changed: no.
- Third-party materials or binaries changed: no.
- Local workflow mirror changed: no.
- Server execution source changed: no.

## Not Implemented

- Did not run `ssh lilin`.
- Did not run `sbatch`.
- Did not delete, overwrite, or modify remote server files.
- Did not modify real calculation tasks.
- Did not sync changes into the formal installed skill directory.

## Checks Run

- `git status --short --branch`
- `C:\Program Files\GitHub CLI\gh.exe auth status --hostname github.com`
- `git fetch origin main`
- `git pull --ff-only origin main`
- `git checkout -b task_002_review-skill-rules`
- `C:\Program Files\GitHub CLI\gh.exe issue create ...`
- `git diff --stat`
- `git diff -- SKILL.md agents/openai.yaml docs/GITHUB_COLLABORATION_WORKFLOW.md CODEX_FEEDBACK.md docs/handoff/2026-06-20_task_002_review-skill-rules.md`

## Remaining Notes

- After commit and push, update this file with the PR URL.
- Ask ChatGPT to review whether the trigger description is specific enough without over-triggering on non-monolayer catalysis workflows.
