# task_012 handoff: Batch C effective-mass / mobility fitted-result labels

## Scope

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/30
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/31
- Branch: `task_012_batch-c-effective-mass-mobility-fitted-result-labels`
- Base: synced `main` after PR #28 / Batch B squash merge.
- Scope: local-only workflow implementation for `11_effective_mass` and `12_mobility`.

## Changed Files

- `scripts/remote-workflow/workflow.py`
- `scripts/remote-workflow/modules/base.py`
- `scripts/remote-workflow/tests/test_provenance_labels.py`
- `CODEX_FEEDBACK.md`
- `docs/handoff/2026-06-22_task_012_batch-c-effective-mass-mobility-fitted-result-labels.md`

## Implementation Notes

- Reused the existing Batch A/B `result_labels.yaml` path and `_result_entry(...)` shape.
- Added Batch C metadata and `build_batch_c_result_labels(...)` in `workflow.py`.
- Added collection-time label generation for `11_effective_mass` and `12_mobility`.
- Did not add a parallel fitted-label schema or manager-specific alternate writer.
- Kept all implementation local-only; no submit, ssh, sbatch, VASP, VASPKIT, phonopy, or server dry-run was executed.

## Effective Mass Labels

- `parent_calculation` links `02_scf + 03_pbeband`, or the actual configured `charge_parent + edge_source`.
- Records:
  - `effective_mass_settings.yaml`
  - `00_edge_source/band_edge.yaml`
  - `em_runs.yaml`
  - target run dirs
  - target `EIGENVAL`
  - target `KPOINTS`
  - target `em_target.yaml`
  - `results/em_summary.yaml`
  - optional `results/em_summary.csv`
- Uses `transformation.label = effective_mass_curvature_fit`.
- Records carrier, band edge, valley, direction, k-window, fit window, R2, residual, fit-energy window, curvature sign, uncertainty placeholder, and quality status.
- Missing band-edge source, target manifest entry, target `EIGENVAL` / `KPOINTS`, fit summary, or fit-quality evidence makes the entry diagnostic, not final.

## Mobility Labels

- `parent_calculation` links `11_effective_mass + 02_scf + 01_opt`.
- Records:
  - `mobility_settings.yaml`
  - `mobility_runs.yaml`
  - effective-mass source summary
  - parent structure / SCF source records
  - strain relax `CONTCAR`
  - strain SCF `CHGCAR`
  - strain SCF `LOCPOT`
  - strain edge `EIGENVAL`
  - strain edge `KPOINTS`
  - `results/mobility_summary.yaml`
  - `results/mobility_summary.csv`
  - `results/mobility_points.csv`
- Uses `transformation.label = deformation_potential_mobility_fit`.
- Records C2D, E1, effective-mass source, transport/DOS masses, carrier/direction, strain range, deformation-potential fit R2, elastic fit R2, uncertainty placeholder, and quality status.
- Missing effective-mass source, strain series/output evidence, deformation-potential fit, elastic fit, mobility summary, or CSV evidence makes the entry diagnostic, not final.

## Tests

- Added local-only synthetic tests for:
  - Effective mass missing evidence is not final.
  - Effective mass entries include fit/source metadata and schema keys.
  - Mobility missing evidence is not final.
  - Mobility entries include C2D/E1/effective-mass-source/fit metadata and schema keys.
- Tests use temp dirs, YAML/CSV placeholders, and dummy local evidence files only.

## Checks Run

- `python -m py_compile scripts\remote-workflow\provenance_utils.py scripts\remote-workflow\workflow.py scripts\remote-workflow\modules\base.py scripts\remote-workflow\collect\outcar_parser.py scripts\remote-workflow\tests\test_provenance_labels.py`
- `python -m unittest discover scripts\remote-workflow\tests`

## Explicitly Not Done

- No `ssh lilin`.
- No `sbatch`.
- No VASP, VASPKIT, or phonopy run.
- No server dry-run.
- No remote server write/delete/sync.
- No real calculation task modification.
- No formal installed skill sync.
- No HSE/optical/phonopy implementation changes.
- No directory renaming.
- No raw bundle, PDF, image, JSON cache, source tree, or binary artifact.

## ChatGPT Review Focus

- Verify Batch C extends Batch A/B schema cleanly.
- Check effective-mass evidence gates and parent/source metadata.
- Check mobility evidence gates and C2D/E1/effective-mass-source metadata.
- Check that tests remain local-only and synthetic.
- Check no unrelated HSE/optical/phonopy/scheduler/remote-execution changes.
