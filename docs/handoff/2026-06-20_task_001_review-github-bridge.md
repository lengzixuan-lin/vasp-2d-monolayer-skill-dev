# Handoff: task_001_review-github-bridge

## Task Source

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/1
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/2
- ChatGPT review: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/2#pullrequestreview-4536381171
- ChatGPT review file: `CHATGPT_REVIEW.md`

## Codex Completed

- Read ChatGPT's review comment from PR #2.
- Backfilled PR #2 URL into review, feedback, and handoff records.
- Strengthened `.gitignore` for future reference-bundle and binary safety.
- Expanded PR, Issue, and handoff templates with diff reality, scope boundary, and sync truth fields.
- Updated collaboration workflow docs with actual diff checks and local-mirror/server-source separation.
- Updated `docs/VASP_REFERENCES_INDEX.md` with current bundle risks and future policy.
- Updated `SKILL.md` so SSH-based server inspection is user-confirmed server verification, not default required reading.
- Updated `agents/openai.yaml` to require confirmation before SSH, Slurm, or remote writes.

## Codex Did Not Complete

- Did not remove, split, or rewrite `vasp_references资料/`; ChatGPT listed this as requiring user confirmation.
- Did not modify the formal installed skill directory under `C:\Users\11658\.codex\skills\vasp-2d-monolayer`.
- Did not run `ssh lilin`, `sbatch`, or any remote write/delete operation.
- Did not modify real calculation tasks.

## Changed Files

- `.gitignore`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/task.md`
- `SKILL.md`
- `agents/openai.yaml`
- `CHATGPT_REVIEW.md`
- `CODEX_FEEDBACK.md`
- `docs/GITHUB_COLLABORATION_WORKFLOW.md`
- `docs/VASP_REFERENCES_INDEX.md`
- `docs/handoff/TEMPLATE.md`
- `docs/handoff/2026-06-20_task_001_review-github-bridge.md`

## Diff Reality Check

- Actual changed file count relative to `main` before this follow-up: 404.
- Tracked files under `vasp_references资料/`: 399.
- Large files added: yes, from the earlier reference-bundle commit in this PR.
- Reference bundle changed: yes, from the earlier commit in this PR.
- Third-party materials or binaries changed: yes, from the earlier reference-bundle commit in this PR.
- Local workflow mirror changed: no in this follow-up.
- Server execution source changed: no.

## Scope Boundary

- Allowed files: bridge docs, templates, feedback/handoff files, `SKILL.md`, `agents/openai.yaml`, `.gitignore`.
- Out of scope: remote server changes, Slurm submission, real calculation tasks, formal installed skill sync.
- User-approved exceptions: earlier upload of `vasp_references资料/`; whether to keep it now still needs user confirmation.

## Checks Run

- `git status --short --branch`
- `git diff --stat origin/main...HEAD`
- `git ls-files "vasp_references资料/*"`
- `C:\Program Files\GitHub CLI\gh.exe auth status -h github.com`
- `C:\Program Files\GitHub CLI\gh.exe pr view 2 --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev`
- GitHub PR comments read through the Codex GitHub plugin.

## External Actions

- `ssh lilin`: not run.
- `sbatch`: not run.
- Remote writes/deletes: not run.

## Sync Truth

- Formal skill directory changed: no.
- Local workflow mirror changed: no in this follow-up.
- Server execution source changed: no.

## Risks

- PR #2 still contains the full reference bundle unless the user confirms removal or split.
- The current `.gitignore` reduces future accidental additions but does not untrack files already committed.
- The repository should remain private unless the user separately confirms copyright and redistribution boundaries.

## Suggested Next ChatGPT Review Focus

- Check whether the updated templates and docs resolve the scope, safety, and traceability issues.
- Decide whether PR #2 can keep the reference bundle with explicit risk notes or should split it into a separate PR.
- Confirm that `SKILL.md` now treats server verification as user-confirmed rather than default required reading.
