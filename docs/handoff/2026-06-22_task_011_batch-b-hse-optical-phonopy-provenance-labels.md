# task_011 handoff: Batch B HSE / optical / phonopy provenance labels

## Scope

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/26
- Branch: `task_011_batch-b-hse-optical-phonopy-provenance-labels`
- Base: synced `main` after Batch A / PR #23 merge.
- Scope: local-only workflow implementation for `05_hse_scf`, `05_hse_band`, `08_optical`, and `09_phonopy_fd`.

## Changed Files

- `scripts/remote-workflow/workflow.py`
- `scripts/remote-workflow/modules/base.py`
- `scripts/remote-workflow/tests/test_provenance_labels.py`
- `CODEX_FEEDBACK.md`
- `docs/handoff/2026-06-22_task_011_batch-b-hse-optical-phonopy-provenance-labels.md`

## Implementation Notes

- Reused Batch A result-entry shape rather than adding a parallel label system.
- Added Batch B collection-time `result_labels.yaml` generation.
- Preserved actual directories and exposed normalized labels:
  - `08_optical` -> `07_optical`
  - `09_phonopy_fd` -> `08_phonopy_fd`
- Added Batch B prepared-stage provenance in `module_provenance.yaml`.
- Added local-only `displacement_manifest.yaml` metadata for finite-displacement phonopy prepare.
- Did not change scheduler submission behavior or run commands.

## Safety Gates

- HSE-SCF cannot be final without parent evidence, output evidence, and convergence evidence.
- HSE-band cannot be final without parent HSE-SCF `CHGCAR`, band output, and band-gap output.
- Optical cannot be final without VASPKIT 710 converted 2D outputs.
- VASPKIT 711 is explicitly marked bulk-only/invalid for monolayer absorption final labels.
- Phonopy cannot be final without displacement manifest, `FORCE_SETS`, and phonon summary evidence.

## Tests

- Added local-only tests for:
  - HSE-band missing parent/output evidence is not final.
  - Optical missing converted 2D outputs is not final.
  - VASPKIT 710 vs 711 policy.
  - Phonopy missing `FORCE_SETS` / summary evidence is not final.
  - Batch B schema-aligned result keys.

## Checks Run

- `python -m py_compile scripts\remote-workflow\provenance_utils.py scripts\remote-workflow\workflow.py scripts\remote-workflow\modules\base.py scripts\remote-workflow\collect\outcar_parser.py scripts\remote-workflow\tests\test_provenance_labels.py`
- `python -m unittest discover scripts\remote-workflow\tests`
- `git diff --check`

## Explicitly Not Done

- No `ssh lilin`.
- No `sbatch`.
- No VASP, VASPKIT, or phonopy run.
- No server dry-run.
- No remote server write/delete/sync.
- No formal installed skill sync.
- No effective-mass or mobility implementation.
- No directory renaming.
- No raw bundle, PDF, image, JSON cache, source tree, or binary artifact.

## ChatGPT Review Focus

- Verify Batch B extends Batch A schema cleanly.
- Check HSE parent `CHGCAR` and `WAVECAR` policies.
- Check VASPKIT 251 and 710 provenance.
- Check 711 bulk-only guardrail.
- Check optical raw VASP response vs converted 2D spectra separation.
- Check phonopy manifest and final-status evidence gates.
- Check no effective-mass/mobility or server/scheduler scope creep.
