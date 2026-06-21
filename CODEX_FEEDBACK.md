# CODEX_FEEDBACK.md

## GitHub Context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/22
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/23
- Branch: `task_010_batch-a-core-provenance-baseline-labels`
- Task ID: `task_010_batch-a-core-provenance-baseline-labels`

## This Round Summary

- Merged PR #21 with squash merge and continued from synced `main`.
- Read Issue #22 and confirmed this is the first local-only Batch A workflow implementation task.
- Limited implementation scope to core provenance plus baseline labels for:
  - `00_input`
  - `01_opt`
  - `02_scf`
  - `03_pbeband`
  - `04_dos`
- Did not run server, scheduler, VASP, VASPKIT, or dry-run commands.

## Implemented Changes

- Added `scripts/remote-workflow/provenance_utils.py` for local file records and SHA256 hashes.
- Extended the existing `Module.write_module_provenance(...)`; no parallel module provenance writer was introduced.
- Enriched prepared-stage `module_provenance.yaml` with:
  - `schema_version`
  - actual directory and normalized module label
  - method label and calculation purpose
  - parent-file policy and local file evidence
  - generated input records for POSCAR, INCAR, KPOINTS, POTCAR, `sub.vasp`, and related metadata
  - VASP/VASPKIT/Slurm environment references from config
  - dependency intent/status available at prepare time
  - restart/overwrite intent
  - post-processing intent
  - review state
- Moved normal-module provenance writing to after `sub.vasp`, `kpoints_summary.yaml`, and `OPTCELL` generation.
- Added `00_input/module_provenance.yaml` writing from `cmd_new` after POSCAR, metadata, structure audit, manifest, and workflow status exist.
- Added Batch A `result_labels.yaml` emission during `cmd_collect`, not `cmd_submit`.
- Preserved current directory names, including `03_pbeband`, while exposing normalized label `03_band`.
- Replaced shell-grep collection with existing `OutcarParser` where available.
- Added local unit tests for result-label safety behavior.

## Safety Behavior

- Missing or unfinished Batch A outputs are labeled `blocked`, `diagnostic`, or `pending_review`, not `final`.
- Missing `BAND_GAP` for completed `03_pbeband` is labeled diagnostic.
- Prepared but uncollected modules get pending-review labels rather than final labels.
- `result_labels.yaml` is written from collection-time evidence only.

## ChatGPT Review Follow-up

- Read the PR #23 ChatGPT review.
- Aligned Batch A result entries with the accepted task_008 schema:
  - `value_name` replaces transitional `name`.
  - `parser_or_tool.name` replaces transitional `parser`.
  - `transformation.label` replaces string-only transformation labels.
  - `parent_calculation` is emitted for Batch A result entries.
  - `convergence_status.task_status` is emitted for each result entry.
- Added unit-test assertions for the schema-aligned result keys.
- Batch A parent calculations are:
  - `01_opt` -> `00_input`
  - `02_scf` -> `01_opt`
  - `03_band` -> `02_scf`
  - `04_dos` -> `02_scf`

## Diff Reality Check

- Workflow implementation files changed:
  - `scripts/remote-workflow/workflow.py`
  - `scripts/remote-workflow/modules/base.py`
- New helper/test files:
  - `scripts/remote-workflow/provenance_utils.py`
  - `scripts/remote-workflow/tests/test_provenance_labels.py`
- Documentation/update files changed:
  - `CODEX_FEEDBACK.md`
  - `docs/handoff/2026-06-20_task_010_batch-a-core-provenance-baseline-labels.md`
- `config/**` changed: no.
- HSE/optical/phonopy/effective-mass/mobility implementation changed intentionally: no.
- Directory names changed: no.
- Large files added: no.
- Raw bundles, PDFs, images, JSON caches, source trees, or binaries added: no.
- Formal installed skill directory changed: no.

## Not Implemented

- Did not run `ssh lilin`.
- Did not run `sbatch`.
- Did not run VASP.
- Did not run VASPKIT.
- Did not run server-side workflow dry-runs.
- Did not delete, overwrite, move, sync, or write remote server files.
- Did not modify real calculation tasks.
- Did not implement Batch B/C scope.
- Did not implement HSE, optical, phonopy, effective-mass, or mobility result labels.
- Did not rename workflow module directories.
- Did not broadly change scheduler or Slurm behavior.

## Checks Run

- `git status --short --branch`
- `C:\Program Files\GitHub CLI\gh.exe pr view 21 --json ...`
- `C:\Program Files\GitHub CLI\gh.exe pr merge 21 --squash --delete-branch`
- `C:\Program Files\GitHub CLI\gh.exe issue view 22 --comments --json ...`
- `git checkout -b task_010_batch-a-core-provenance-baseline-labels`
- `python -m py_compile scripts\remote-workflow\provenance_utils.py scripts\remote-workflow\workflow.py scripts\remote-workflow\modules\base.py scripts\remote-workflow\collect\outcar_parser.py scripts\remote-workflow\tests\test_provenance_labels.py`
- `python -m unittest discover scripts\remote-workflow\tests`
- `git diff --check`
- `git diff --cached --check`
- `git commit -m "task_010: add batch a provenance and labels"`
- `git push -u origin task_010_batch-a-core-provenance-baseline-labels`
- `C:\Program Files\GitHub CLI\gh.exe pr create ...`
- `gh pr view 23 --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev --json ...`
- `gh api repos/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pulls/23/comments --paginate`
- `python -m py_compile scripts\remote-workflow\provenance_utils.py scripts\remote-workflow\workflow.py scripts\remote-workflow\modules\base.py scripts\remote-workflow\collect\outcar_parser.py scripts\remote-workflow\tests\test_provenance_labels.py`
- `python -m unittest discover scripts\remote-workflow\tests`

## Remaining Notes

- This PR is the Batch A baseline only.
- Future Batch B should add HSE/optical/phonopy-specific provenance and labels.
- Future Batch C should add effective-mass/mobility fitted-result labels.
