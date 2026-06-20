# CODEX_FEEDBACK.md

## GitHub Context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/20
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/21
- Branch: `task_009_implementation-readiness-provenance-result-labels`
- Task ID: `task_009_implementation-readiness-provenance-result-labels`

## This Round Summary

- Confirmed PR #19 was merged and continued from the synced task_009 branch.
- Read Issue #20 and confirmed the task is documentation/planning-only.
- Inspected the local `scripts/remote-workflow/**` and `config/**` mirror without running server or calculation commands.
- Mapped module preparation, rendering, parent-file policy, submission, collection, parser sources, provenance insertion points, and result-label insertion points.
- Added an implementation-readiness plan for future provenance/result-label PRs.

## Implemented Changes

- Added `docs/implementation-plans/2026-06-20_task_009_provenance-result-label-implementation-readiness.md`.
- Added a module-by-module mapping table for:
  - `00_input`
  - `01_opt`
  - `02_scf`
  - `03_band` / current `03_pbeband`
  - `04_dos`
  - `05_hse_scf`
  - `05_hse_band`
  - `06_potential` / current monolayer `07_vacuum`
  - `07_optical` / current `08_optical`
  - `08_phonopy_fd` / current `09_phonopy_fd`
  - `11_effective_mass`
  - `12_mobility`
- Identified where future implementation should generate or extend `module_provenance.yaml`.
- Identified where future implementation should generate `result_labels.yaml` or equivalent summary labels.
- Documented existing and missing dependency, convergence, restart, overwrite, and parser-source information.
- Added ChatGPT-requested VASPKIT/JAMIP-derived audit anchors to make future implementation traceability explicit.
- Proposed three implementation batches:
  - Batch A: core provenance writer plus `00_input`, `01_opt`, `02_scf`, `03_pbeband`, `04_dos`.
  - Batch B: HSE, optical, and phonopy finite-displacement provenance/result labels.
  - Batch C: effective-mass and mobility fitted-result labels.
- Added `docs/handoff/2026-06-20_task_009_implementation-readiness-provenance-result-labels.md`.

## Diff Reality Check

- Actual changed file count: 3.
- Documentation/planning files changed: yes.
- Large files added: no.
- Reference bundle changed: no.
- Third-party materials or binaries changed: no.
- `scripts/remote-workflow/**` implementation changed: no.
- `config/**` changed: no.
- Local workflow mirror behavior changed: no.
- Server execution source changed: no.
- Formal installed skill directory changed: no.

## Not Implemented

- Did not run `ssh lilin`.
- Did not run `sbatch`.
- Did not run VASP.
- Did not run VASPKIT.
- Did not run server-side workflow dry-runs.
- Did not delete, overwrite, move, sync, or write remote server files.
- Did not modify real calculation tasks.
- Did not edit workflow implementation files.
- Did not implement schema writers or parsers.
- Did not sync changes into the formal installed skill directory.

## Checks Run

- `git status --short --branch`
- `rg -n ... scripts/remote-workflow/workflow.py`
- `rg -n ... scripts/remote-workflow/modules/base.py`
- `rg -n ... scripts/remote-workflow/submit/slurm.py`
- `rg -n ... scripts/remote-workflow/collect/outcar_parser.py`
- `git diff --check`
- `git diff --cached --check`
- `git commit -m "task_009: map provenance result label implementation plan"`
- `git push -u origin task_009_implementation-readiness-provenance-result-labels`
- `C:\Program Files\GitHub CLI\gh.exe pr create ...`
- `C:\Program Files\GitHub CLI\gh.exe pr view 21 --comments --json ...`
- `git fetch origin main`

## Remaining Notes

- This PR is documentation/planning-only.
- Future implementation should probably preserve current directory names and expose normalized names through provenance/result-label fields unless a separate naming migration is approved.
