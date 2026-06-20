# Handoff: task_004_improvement-plan

## Task Source

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/8
- PR: pending
- ChatGPT review file: pending

## Codex Completed

- Created branch `task_004_improvement-plan` from current `main`.
- Created GitHub Issue #8 for this planning task.
- Converted the task_003 summary follow-up targets into a concrete improvement plan.
- Prioritized the five requested review areas:
  - VASPKIT optical task numbering 710/711 server-version verification.
  - `module_provenance.yaml` schema.
  - finite-displacement phonon subtask manifest.
  - scheduler config / submit template configurability.
  - result-summary method/source labels.
- Updated `CODEX_FEEDBACK.md` for this round.

## Codex Did Not Complete

- Did not verify the installed server VASPKIT version.
- Did not edit workflow implementation files.
- Did not create schemas or implementation changes beyond the planning document.

## Changed Files

- `docs/improvement-plans/2026-06-20_task_004_improvement-plan.md`
- `docs/handoff/2026-06-20_task_004_improvement-plan.md`
- `docs/reference-summaries/README.md`
- `CODEX_FEEDBACK.md`

## Diff Reality Check

- Actual changed file count: 4
- Large files added: no
- Reference bundle changed: no
- Third-party materials or binaries changed: no
- Local workflow mirror changed: no
- Server execution source changed: no

## Scope Boundary

- Allowed files: review/planning docs, handoff docs, `CODEX_FEEDBACK.md`
- Out of scope: workflow implementation, raw reference bundle, remote/server operations, real calculation tasks
- User-approved exceptions: none

## Checks Run

- `git status --short --branch`
- `gh auth status --hostname github.com`
- `git checkout main`
- `git pull --ff-only origin main`
- `git checkout -b task_004_improvement-plan`
- `gh issue create ...`

## External Actions

- `ssh lilin`: no
- `sbatch`: no
- Remote writes/deletes: no

## Sync Truth

- Formal skill directory changed: no
- Local workflow mirror changed: no
- Server execution source changed: no

## Risks

- VASPKIT optical task numbering remains unverified against the installed server version because this task intentionally avoided server access.
- Follow-up schema tasks still need implementation and review.

## Suggested Next ChatGPT Review Focus

- Confirm whether the five requested summary-derived review targets are concrete enough to become separate implementation issues.
- Confirm that task_004 stayed planning-only and did not cross into remote/server execution or real calculation changes.
