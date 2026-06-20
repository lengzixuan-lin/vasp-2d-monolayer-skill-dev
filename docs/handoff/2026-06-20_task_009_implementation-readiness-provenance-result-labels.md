# task_009 handoff: implementation readiness for provenance/result labels

Date: 2026-06-20

## GitHub context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/20
- Branch: `task_009_implementation-readiness-provenance-result-labels`
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/21

## Scope

This round is documentation/planning-only. It inspected the local mirror under `scripts/remote-workflow/**` and `config/**` to identify implementation insertion points for provenance and result labels.

No workflow implementation files were modified.

## Files changed

- Added `docs/implementation-plans/2026-06-20_task_009_provenance-result-label-implementation-readiness.md`.
- Updated `CODEX_FEEDBACK.md`.
- Added this handoff file.

## Main findings

- The current implementation already has a minimal `module_provenance.yaml` writer at `Module.write_module_provenance(...)`; future PRs should extend it rather than add a parallel writer.
- `cmd_new` needs a separate input provenance path for `00_input`, because it is not a `Module` instance.
- Generic result labels should be written during collection, not submission, because labels need output evidence and parser/source-file context.
- Effective-mass and mobility labels should be written by their embedded manager `collect_results` phases, next to `em_summary.yaml` and `mobility_summary.yaml`.
- The requested normalized module names do not fully match current local directory names:
  - `03_band` maps to `03_pbeband`.
  - `06_potential` likely maps to monolayer `07_vacuum`, while `15_potential` is heterojunction-specific.
  - `07_optical` maps to `08_optical`.
  - `08_phonopy_fd` maps to `09_phonopy_fd`.

## Suggested implementation batches

1. Batch A: core provenance writer plus `00_input`, `01_opt`, `02_scf`, `03_pbeband`, `04_dos`.
2. Batch B: HSE, optical, and phonopy finite-displacement provenance/result labels.
3. Batch C: effective-mass and mobility fitted-result labels.

## Boundaries respected

- Did not run `ssh lilin`.
- Did not run `sbatch`.
- Did not run VASP or VASPKIT.
- Did not run server dry-runs.
- Did not write, delete, overwrite, or sync remote server files.
- Did not modify real calculation tasks.
- Did not edit `scripts/remote-workflow/**` implementation files.
- Did not implement schema writers or parsers.
- Did not add raw bundles, PDFs, images, JSON caches, source trees, or binaries.
- Did not sync into the formal installed skill directory.

## Recommended reviewer focus

- Whether the insertion points are accurate for future implementation PRs.
- Whether the normalized-name vs actual-directory mismatch should be resolved by labels only or by a later naming migration.
- Whether `result_labels.yaml` should always be a separate file, or can be embedded in fitted-result summaries where that is more practical.
