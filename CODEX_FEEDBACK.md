# CODEX_FEEDBACK.md

## GitHub Context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/30
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/31
- Branch: `task_012_batch-c-effective-mass-mobility-fitted-result-labels`
- Task ID: `task_012_batch-c-effective-mass-mobility-fitted-result-labels`

## This Round Summary

- First squash-merged PR #28, then synced local `main`.
- Started task_012 from merged Batch A/B state.
- Implemented Batch C local-only fitted-result labels for:
  - `11_effective_mass`
  - `12_mobility`
- Reused the existing `workflow.py` result-entry schema and collection-time writer.
- Did not add a parallel fitted-label system.
- Did not run server, scheduler, VASP, VASPKIT, phonopy, ssh, sbatch, or dry-run commands.

## Implemented Changes

- Added Batch C module metadata and `build_batch_c_result_labels(...)` in `scripts/remote-workflow/workflow.py`.
- Added `cmd_collect` integration so `11_effective_mass` and `12_mobility` write `result_labels.yaml`.
- Kept result entries schema-aligned with Batch A/B:
  - `value_name`
  - `parser_or_tool`
  - `transformation.label`
  - `parent_calculation`
  - `convergence_status.task_status`
  - `uncertainty_or_fit_quality`
  - `result_status`
- Effective-mass labels record band-edge source, EM settings, `em_runs.yaml`, target run dirs, target `EIGENVAL` / `KPOINTS`, `em_target.yaml`, `results/em_summary.yaml`, and optional CSV output.
- Mobility labels record effective-mass source, structure/SCF parents, `mobility_settings.yaml`, `mobility_runs.yaml`, strain relax/SCF/edge outputs, `results/mobility_summary.yaml`, and CSV outputs.
- Fixed a local `mobility_runtime.py` template issue where `warnings` was used before initialization during collection.

## Evidence Gates

- Effective-mass results use `transformation.label = effective_mass_curvature_fit`.
- Effective-mass entries cannot be final if band-edge source, target manifest entries, target `EIGENVAL` / `KPOINTS`, fit summary, or fit-quality evidence is missing.
- Effective-mass entries record carrier, band edge, valley, direction, k-window, fit window, R2, residual, energy window, curvature-sign check, and quality status.
- Mobility results use `transformation.label = deformation_potential_mobility_fit`.
- Mobility entries cannot be final if effective-mass source, strain series, strain outputs, deformation-potential fit, elastic fit, summary, or CSV evidence is missing.
- Mobility entries record C2D, E1, effective-mass source, carrier/direction, strain range, edge-fit R2, elastic R2, masses, and quality status.

## Tests Added

- Effective mass missing evidence is not final.
- Effective mass entries include fit/source metadata and schema keys.
- Mobility missing evidence is not final.
- Mobility entries include C2D/E1/effective-mass-source/fit metadata and schema keys.
- Tests use only synthetic YAML/CSV/temp dirs and local dummy evidence files.

## Diff Reality Check

- Workflow implementation files changed:
  - `scripts/remote-workflow/workflow.py`
  - `scripts/remote-workflow/modules/base.py`
- Test files changed:
  - `scripts/remote-workflow/tests/test_provenance_labels.py`
- Documentation/update files changed:
  - `CODEX_FEEDBACK.md`
  - `docs/handoff/2026-06-22_task_012_batch-c-effective-mass-mobility-fitted-result-labels.md`
- HSE/optical/phonopy implementation changed: no.
- Config changed: no.
- Directory names changed: no.
- Large files added: no.
- Raw bundles, PDFs, images, JSON caches, source trees, or binaries added: no.
- Formal installed skill directory changed: no.

## Not Done

- No `ssh lilin`.
- No `sbatch`.
- No VASP run.
- No VASPKIT run.
- No phonopy run.
- No server dry-run.
- No remote server write/delete/sync.
- No real calculation task modification.
- No formal installed skill sync.
- No HSE, optical, or phonopy scope changes.
- No directory renaming.
- No broad scheduler or Slurm behavior changes.

## Checks Run

- `python -m py_compile scripts\remote-workflow\provenance_utils.py scripts\remote-workflow\workflow.py scripts\remote-workflow\modules\base.py scripts\remote-workflow\collect\outcar_parser.py scripts\remote-workflow\tests\test_provenance_labels.py`
- `python -m unittest discover scripts\remote-workflow\tests`

## ChatGPT Review Focus

- Confirm Batch C extends the existing Batch A/B schema instead of creating a parallel fitted-label system.
- Check effective-mass final-status gates for band-edge source, target manifest, target `EIGENVAL` / `KPOINTS`, summary, and fit-quality evidence.
- Check mobility final-status gates for effective-mass source, strain series/outputs, deformation-potential fit, elastic fit, summary, and CSV evidence.
- Check that no remote execution, scheduler behavior, installed skill sync, or unrelated HSE/optical/phonopy changes slipped in.
