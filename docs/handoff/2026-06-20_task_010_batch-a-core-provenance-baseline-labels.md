# task_010 handoff: Batch A core provenance and baseline result labels

Date: 2026-06-20

## GitHub context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/22
- Branch: `task_010_batch-a-core-provenance-baseline-labels`
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/23

## Scope

This is the first local-only workflow implementation PR for provenance/result labels. It implements Batch A only:

- `00_input`
- `01_opt`
- `02_scf`
- `03_pbeband`
- `04_dos`

## Changed files

- `scripts/remote-workflow/provenance_utils.py`
- `scripts/remote-workflow/modules/base.py`
- `scripts/remote-workflow/workflow.py`
- `scripts/remote-workflow/tests/test_provenance_labels.py`
- `CODEX_FEEDBACK.md`
- `docs/handoff/2026-06-20_task_010_batch-a-core-provenance-baseline-labels.md`

## Implementation summary

- Extended the existing `Module.write_module_provenance(...)`; no parallel provenance writer was added.
- Added local file-record and SHA256 helpers in `provenance_utils.py`.
- Added richer prepared-stage provenance for normal modules, including normalized labels and generated-input evidence.
- Moved normal-module provenance writing after generated files exist.
- Added `00_input/module_provenance.yaml` writing in `cmd_new`.
- Added Batch A `result_labels.yaml` writing in `cmd_collect`.
- Kept `03_pbeband` as the directory name and exposes `03_band` as `normalized_module_label`.
- Uses collection-time output evidence; final result labels are not written in `cmd_submit`.

## Safety behavior

- Prepared or unfinished modules are labeled `pending_review`.
- Missing evidence in a completed module is labeled `blocked` or `diagnostic`.
- Missing `BAND_GAP` in `03_pbeband` is diagnostic, not final.
- DOS evidence is labeled `dos_postprocessing_pending`; no DOS parser was implemented in this batch.

## Checks run

- `python -m py_compile scripts\remote-workflow\provenance_utils.py scripts\remote-workflow\workflow.py scripts\remote-workflow\modules\base.py scripts\remote-workflow\collect\outcar_parser.py scripts\remote-workflow\tests\test_provenance_labels.py`
- `python -m unittest discover scripts\remote-workflow\tests`
- `git diff --check`

## Boundaries respected

- Did not run `ssh lilin`.
- Did not run `sbatch`.
- Did not run VASP or VASPKIT.
- Did not run server dry-runs.
- Did not write, delete, overwrite, or sync remote server files.
- Did not modify real calculation tasks.
- Did not sync into the formal installed skill directory.
- Did not implement HSE/optical/phonopy/effective-mass/mobility labels.
- Did not rename directories.
- Did not add raw bundles, PDFs, images, JSON caches, source trees, or binaries.

## Review focus

- Confirm that `Module.write_module_provenance(...)` is extended rather than bypassed.
- Confirm that `00_input` provenance is written only after input/audit/status records exist.
- Confirm that result labels are collection-time only and evidence-based.
- Confirm that missing/incomplete outputs are not marked final.
- Confirm that Batch B/C modules were not implemented in this PR.
