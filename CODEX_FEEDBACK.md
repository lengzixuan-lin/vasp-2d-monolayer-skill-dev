# CODEX_FEEDBACK.md

## GitHub Context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/26
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/28
- Branch: `task_011_batch-b-hse-optical-phonopy-provenance-labels`
- Task ID: `task_011_batch-b-hse-optical-phonopy-provenance-labels`

## This Round Summary

- Started from synced `main` after PR #23 / Batch A was squash-merged.
- Implemented Batch B local-only provenance/result-label support for:
  - `05_hse_scf`
  - `05_hse_band`
  - `08_optical`
  - `09_phonopy_fd`
- Extended the existing Batch A result-label shape and collection-time writer.
- Did not introduce a parallel provenance/result-label system.
- Did not run server, scheduler, VASP, VASPKIT, phonopy, or dry-run commands.

## Implemented Changes

- Added Batch B module metadata in `scripts/remote-workflow/workflow.py`.
- Added Batch B result-label collection for HSE-SCF, HSE-band, optical, and finite-displacement phonopy.
- Preserved real module directories while exposing normalized labels:
  - `08_optical` -> `07_optical`
  - `09_phonopy_fd` -> `08_phonopy_fd`
- Kept Batch B entries schema-aligned with Batch A:
  - `value_name`
  - `parser_or_tool`
  - `transformation.label`
  - `parent_calculation`
  - `convergence_status.task_status`
  - `result_status`
- Extended prepared-stage `module_provenance.yaml` records in `modules/base.py` for Batch B modules.
- Added `displacement_manifest.yaml` generation for `09_phonopy_fd` prepare metadata only.

## Module-Specific Behavior

- HSE-SCF records parent `02_scf` intent, parent `CONTCAR` / `CHGCAR` / `POTCAR` evidence, and a no-blind-reuse `WAVECAR` policy.
- HSE-SCF records HSE INCAR/template settings such as `AEXX`, `HFSCREEN`, `LHFCALC`, `PRECFOCK`, and `ALGO`.
- HSE-SCF labels require output, parent evidence, and convergence evidence before they can be final.
- HSE-band uses `parent_calculation = 05_hse_scf`.
- HSE-band records required parent HSE-SCF `CHGCAR`, VASPKIT 251 runtime KPOINTS provenance, and VASPKIT 252 band-gap extraction provenance.
- HSE-band records that `WAVECAR` must not be blindly reused after KPOINTS/NBANDS/method changes.
- HSE-band missing `EIGENVAL`, parent `CHGCAR`, or `BAND_GAP` is diagnostic, not final.
- Optical keeps actual directory `08_optical` and exposes normalized label `07_optical`.
- Optical separates raw VASP `LOPTICS` response from VASPKIT-converted 2D spectra.
- Optical records `NBANDS`, `LOPTICS`, `POSCAR`, `vasprun.xml`, optional `REAL.in` / `IMAG.in`, and expected 2D outputs.
- Optical records VASPKIT 710 as the accepted 2D conversion task.
- Optical records VASPKIT 711 as bulk-only/invalid for monolayer optical absorption final labels.
- Optical missing converted 2D outputs is diagnostic, not final.
- Phonopy keeps actual directory `09_phonopy_fd` and exposes normalized label `08_phonopy_fd`.
- Phonopy uses `parent_calculation = 01_opt`.
- Phonopy records supercell dim, displacement distance, symprec, DOS mesh, path, and band-point settings where available.
- Phonopy labels require displacement manifest, `FORCE_SETS`, and phonon summary evidence before final status.

## Tests Added

- HSE-band missing parent/output evidence is not final.
- Optical missing converted 2D outputs is not final.
- VASPKIT 710 is treated as 2D conversion.
- VASPKIT 711 is treated as bulk-only/invalid for monolayer absorption final labels.
- Phonopy missing `FORCE_SETS` / subtask evidence is not final.
- Batch B result entries keep schema-aligned keys.

## Diff Reality Check

- Workflow implementation files changed:
  - `scripts/remote-workflow/workflow.py`
  - `scripts/remote-workflow/modules/base.py`
- Test files changed:
  - `scripts/remote-workflow/tests/test_provenance_labels.py`
- Documentation/update files changed:
  - `CODEX_FEEDBACK.md`
  - `docs/handoff/2026-06-22_task_011_batch-b-hse-optical-phonopy-provenance-labels.md`
- `config/**` changed: no.
- Effective-mass or mobility implementation changed: no.
- Directory names changed: no.
- Large files added: no.
- Raw bundles, PDFs, images, JSON caches, source trees, or binaries added: no.
- Formal installed skill directory changed: no.

## Not Implemented

- Did not run `ssh lilin`.
- Did not run `sbatch`.
- Did not run VASP.
- Did not run VASPKIT.
- Did not run phonopy.
- Did not run server-side workflow dry-runs.
- Did not delete, overwrite, move, sync, or write remote server files.
- Did not modify real calculation tasks.
- Did not implement effective-mass or mobility scope.
- Did not create Batch C scope.
- Did not rename workflow module directories.
- Did not broadly change scheduler or Slurm behavior.

## Checks Run

- `git checkout main`
- `git pull --ff-only origin main`
- `git checkout -b task_011_batch-b-hse-optical-phonopy-provenance-labels`
- `gh issue view 26 --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev --json number,title,state,body,url`
- `python -m py_compile scripts\remote-workflow\provenance_utils.py scripts\remote-workflow\workflow.py scripts\remote-workflow\modules\base.py scripts\remote-workflow\collect\outcar_parser.py scripts\remote-workflow\tests\test_provenance_labels.py`
- `python -m unittest discover scripts\remote-workflow\tests`
- `git diff --check`

## Remaining Notes

- This PR is Batch B only.
- ChatGPT should review whether Batch B correctly extends Batch A instead of creating a parallel label system.
- ChatGPT should focus on HSE parent policies, VASPKIT 251/710 provenance, VASPKIT 711 guardrails, optical raw-vs-converted separation, phonopy manifest/final-status gating, and scope boundaries.
