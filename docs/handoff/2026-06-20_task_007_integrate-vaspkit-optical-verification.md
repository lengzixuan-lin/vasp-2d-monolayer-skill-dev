# Handoff: task_007_integrate-vaspkit-optical-verification

## Task Source

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/16
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/17
- ChatGPT review file: pending

## Codex Completed

- Synced local `main` with `origin/main`.
- Created branch `task_007_integrate-vaspkit-optical-verification`.
- Read Issue #16, `references/workflow-modules.md`, and `references/vaspkit-optical-verification.md`.
- Updated the `references/workflow-modules.md` optical section to link the task_006 verification note.
- Made the optical review rule explicit:
  - VASP `LOPTICS` is the raw dielectric-response step.
  - VASPKIT `710` is the verified 2D converted-spectra step.
  - VASPKIT `711` is bulk-only and must not be used for monolayer optical absorption summaries.
- Added optical provenance expectations for VASPKIT path/version, task number, `POSCAR`, `vasprun.xml` or `REAL.in`/`IMAG.in`, `LOPTICS`, `NBANDS`, and generated 2D output files.
- Updated `CODEX_FEEDBACK.md`.

## Codex Did Not Complete

- Did not edit workflow implementation files.
- Did not run or inspect anything on the server.
- Did not sync into the formal installed skill directory.

## Changed Files

- `references/workflow-modules.md`
- `docs/handoff/2026-06-20_task_007_integrate-vaspkit-optical-verification.md`
- `CODEX_FEEDBACK.md`

## Diff Reality Check

- Actual changed file count: 3
- Large files added: no
- Reference bundle changed: no
- Third-party materials or binaries changed: no
- Local workflow mirror changed: no
- Server execution source changed: no
- `scripts/remote-workflow/**` changed: no

## Scope Boundary

- Allowed files: workflow documentation, handoff, `CODEX_FEEDBACK.md`
- Out of scope: server access, scheduler jobs, VASP/VASPKIT runs, server dry-runs, remote writes/deletes/sync, real calculation tasks, workflow implementation files, raw reference bundle, formal installed skill sync
- User-approved exceptions: none

## Checks Run

- `git status --short --branch`
- `git fetch origin main`
- `git checkout main`
- `git pull --ff-only origin main`
- `git checkout -b task_007_integrate-vaspkit-optical-verification`
- `gh issue view 16 --comments --json ...`
- `git diff --check`
- `git diff --cached`
- `git commit -m "task_007: integrate vaspkit optical verification"`
- `git push -u origin task_007_integrate-vaspkit-optical-verification`
- `gh pr create ...`

## External Actions

- `ssh lilin`: no
- `sbatch`: no
- VASP/VASPKIT run: no
- Server dry-run: no
- Remote writes/deletes/sync: no
- Real calculation tasks changed: no

## Sync Truth

- Formal skill directory changed: no
- Local workflow mirror changed: no
- Server execution source changed: no

## Risks

- This is documentation-only; workflow implementation still needs a later reviewed task before any code behavior changes.

## Suggested Next ChatGPT Review Focus

- Confirm `references/workflow-modules.md` now links task_006 verification clearly.
- Confirm the `710` 2D / `711` bulk-only boundary is explicit.
- Confirm optical provenance requirements are specific enough for future result summaries.
- Confirm no server, workflow implementation, or real calculation changes were introduced.
