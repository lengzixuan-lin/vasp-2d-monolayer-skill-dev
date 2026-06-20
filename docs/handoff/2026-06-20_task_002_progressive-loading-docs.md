# Handoff: task_002_progressive-loading-docs

## Task Source

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/5
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/4
- ChatGPT review source: Issue #5 body

## Codex Completed

- Read Issue #5 progressive-loading review instructions.
- Refactored `SKILL.md` into a shorter skill entrypoint.
- Added `references/workflow-modules.md` for module order, dependencies, required files, KPOINTS rules, module notes, and method labels.
- Added `references/server-boundary.md` for local/server truth, confirmation gates, GitHub CLI preflight, sync truth, and submission boundary.
- Reduced duplication in `references/monolayer-audit.md`.
- Updated `CODEX_FEEDBACK.md`.

## Codex Did Not Complete

- Did not edit `scripts/remote-workflow/**`.
- Did not run server verification, server dry runs, or remote sync.
- Did not modify real calculation tasks.
- Did not sync the development repository into the formal installed skill directory.

## Changed Files

- `SKILL.md`
- `agents/openai.yaml`
- `docs/GITHUB_COLLABORATION_WORKFLOW.md`
- `CODEX_FEEDBACK.md`
- `docs/handoff/2026-06-20_task_002_review-skill-rules.md`
- `docs/handoff/2026-06-20_task_002_progressive-loading-docs.md`
- `references/monolayer-audit.md`
- `references/server-boundary.md`
- `references/workflow-modules.md`

## Diff Reality Check

- Actual changed file count relative to `main`: 9.
- Large files added: no.
- Reference bundle changed: no.
- Third-party materials or binaries changed: no.
- `references/` changed: yes, focused Markdown references only.
- `scripts/remote-workflow/` changed: no.
- Local workflow mirror changed: no.
- Server execution source changed: no.

## Scope Boundary

- Allowed files: skill entrypoint, reference docs, agent metadata, collaboration docs, feedback, and handoff records.
- Out of scope: workflow scripts, SSH, Slurm submission, server sync, remote writes/deletes, real calculation projects, installed-skill sync, raw reference bundles.
- User-approved exceptions: none.

## Checks Run

- `git status --short --branch`
- `C:\Program Files\GitHub CLI\gh.exe issue list --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev --state open --limit 20`
- `C:\Program Files\GitHub CLI\gh.exe pr list --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev --state open --limit 20`
- `C:\Program Files\GitHub CLI\gh.exe issue view 5 --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev --json number,title,body,comments,labels,url`
- `C:\Program Files\GitHub CLI\gh.exe pr view 4 --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev --json number,title,body,comments,reviews,url`
- `rg --files references docs`
- `rg -n "^## " references/monolayer-audit.md`
- `git diff --stat`
- `git diff --check`
- `git diff --name-only -- scripts/remote-workflow`
- `C:\Program Files\GitHub CLI\gh.exe pr edit 4 ...`

## External Actions

- `ssh lilin`: no
- `sbatch`: no
- Server dry run: no
- Remote writes/deletes: no
- GitHub Issue read: yes, Issue #5
- GitHub PR body updated: yes

## Sync Truth

- Formal skill directory changed: no
- Local workflow mirror changed: no
- Server execution source changed: no
- Real calculation tasks changed: no

## Risks

- The reference split is documentation-only; ChatGPT should verify no important safety rule became too hidden.
- `SKILL.md` now relies more on progressive loading, so required-reading pointers must stay clear.

## Suggested Next ChatGPT Review Focus

- Whether `SKILL.md` stayed concise without losing essential safety gates.
- Whether `references/workflow-modules.md` contains enough module/dependency detail for practical reviews.
- Whether `references/server-boundary.md` clearly prevents unapproved SSH, Slurm, remote write, sync, and real-calculation actions.
- Whether `references/monolayer-audit.md` is now focused on audit and submission readiness.
