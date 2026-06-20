# CODEX_FEEDBACK.md

## GitHub Context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/1
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/2
- Branch: `task_001_review-github-bridge`
- Task ID: `task_001_review-github-bridge`

## This Round Summary

- Read ChatGPT's PR review from PR #2.
- Applied local-only documentation and template changes that do not require extra user confirmation.
- Did not run `ssh lilin`, `sbatch`, or any remote write/delete operation.
- Did not modify real calculation tasks.
- Did not remove `vasp_references资料/`; ChatGPT marked that as requiring user confirmation.

## Implemented Changes

- Backfilled PR #2 URL in `CHATGPT_REVIEW.md`, `CODEX_FEEDBACK.md`, and the handoff file.
- Strengthened `.gitignore` so future full reference bundles, generated caches, PDFs, images, binaries, and vendored tools require explicit approval.
- Added diff reality, scope boundary, and sync truth fields to:
  - `.github/PULL_REQUEST_TEMPLATE.md`
  - `.github/ISSUE_TEMPLATE/task.md`
  - `docs/handoff/TEMPLATE.md`
- Updated `docs/GITHUB_COLLABORATION_WORKFLOW.md` to require actual changed-file count, large-file status, reference-bundle status, and local-mirror/server-source clarity.
- Updated `docs/VASP_REFERENCES_INDEX.md` with current PR file-count risk and future reference-bundle policy.
- Updated `SKILL.md` so server SSH inspection is no longer default required reading.
- Updated `agents/openai.yaml` default prompt to prefer local context first and require confirmation before SSH, Slurm, or remote writes.

## Diff Reality Check

- Actual changed files relative to `main` before this follow-up: 404.
- Tracked files under `vasp_references资料/`: 399.
- Full bundle size before git compression: about 58 MB.
- Largest known file before upload: about 14.7 MB.
- Large files/reference bundle changed: yes, from the earlier commit in this PR.
- Local workflow mirror changed: no in this follow-up.
- Server execution source changed: no.

## Not Implemented

- Did not split or remove `vasp_references资料/`.
- Did not rewrite PR history.
- Did not update the formal installed skill directory at `C:\Users\11658\.codex\skills\vasp-2d-monolayer`.
- Did not sync anything to `lilin`.

## User Confirmation Still Needed

- Whether to keep the full reference bundle in PR #2.
- Whether third-party PDFs, images, source trees, config files, and binaries may remain in git history.
- Whether the private repository will stay private.
- Whether Codex may remove or restructure `vasp_references资料/` in a follow-up commit.

## Checks Run

- `git status --short --branch`
- `gh` via full path: `C:\Program Files\GitHub CLI\gh.exe auth status -h github.com`
- `gh` via full path: `C:\Program Files\GitHub CLI\gh.exe pr view 2 --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev`
- GitHub PR comments were also read through the Codex GitHub plugin.
- Local diffs reviewed before staging.
