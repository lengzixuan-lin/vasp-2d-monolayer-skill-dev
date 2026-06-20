# task_009: provenance/result-label implementation readiness

Date: 2026-06-20

Scope: local documentation/planning audit only. This plan inspected the local mirror under `scripts/remote-workflow/**` and `config/**`; it did not run SSH, Slurm, VASP, VASPKIT, server dry-runs, or modify workflow implementation files.

## Purpose

This document converts the schema foundation in `references/provenance-and-result-label-schema.md` into implementation-ready mapping notes. It identifies where each workflow module is prepared, rendered, linked to parent files, submitted, collected, and parsed, then proposes where future implementation PRs should write:

- `module_provenance.yaml`
- `result_labels.yaml`, or equivalent labels embedded in module/project summaries

## Current orchestration map

Primary local source files:

- `scripts/remote-workflow/workflow.py`
  - `cmd_new`: creates `00_input`, metadata, structure audit, status/manifest files.
  - `PipelineBuilder.build`: maps configured module names to local module directories.
  - `create_module`: maps module names to INCAR templates.
  - `cmd_prepare`: creates each enabled module directory and calls `Module.setup_dir(...)`.
  - `cmd_submit`: validates prepared inputs and submits `sub.vasp` through Slurm.
  - `inspect_vasp_run`: classifies module completion/failure during monitoring.
  - `cmd_collect`: writes project-level `results.yaml` from completed modules.
- `scripts/remote-workflow/modules/base.py`
  - `render_incar`: renders INCAR templates.
  - `generate_kpoints_and_potcar`: generates normal KPOINTS/POTCAR through VASPKIT 102.
  - `inheritance_policy`: centralizes current parent-file/runtime-copy policy.
  - `write_module_provenance`: existing minimal provenance writer.
  - `setup_dir`: normal module preparation, runtime pre/post command construction, `sub.vasp` rendering.
  - `setup_effective_mass_dir`, embedded `EffectiveMassManager`: effective-mass preparation and result collection.
  - `setup_mobility_dir`, embedded `MobilityManager`: mobility preparation and result collection.
  - `setup_phonopy_fd_dir`: finite-displacement phonon preparation.
- `scripts/remote-workflow/submit/slurm.py`
  - `submit`, `status`, `diagnose`, `resubmit`: submission/status/restart mechanics.
- `scripts/remote-workflow/collect/outcar_parser.py`
  - `OUTCARParser`: reusable parser source for energies, convergence, force, Fermi level, and band gaps.
- `config/settings.yaml`
  - VASP/VASPKIT paths, Slurm defaults, submit template, runtime environment.
- `config/precision_standard.yaml` and `config/precision_quick.yaml`
  - enabled modules, module-specific parameters, optical post-processing mode, readiness flags for effective-mass and mobility workflows.

## Directory-name reality check

The requested documentation module names are partly normalized names, not exact current local directory names:

| Requested name | Current local mapping in `PipelineBuilder.build` | Notes |
|---|---|---|
| `00_input` | `00_input` | Created by `cmd_new`, not a `Module` instance. |
| `01_opt` | `01_opt` | Exact match. |
| `02_scf` | `02_scf` | Exact match. |
| `03_band` | `03_pbeband` | Current implementation directory keeps the PBE-specific name. |
| `04_dos` | `04_dos` | Exact match. |
| `05_hse_scf` | `05_hse_scf` | Exact match. |
| `05_hse_band` | `05_hse_band` | Exact match, shares numeric prefix with HSE SCF. |
| `06_potential` | `07_vacuum` for monolayer vacuum potential; `15_potential` for heterojunction potential | Naming must be settled before implementation. |
| `07_optical` | `08_optical` | Current implementation directory is one index later than the normalized docs name. |
| `08_phonopy_fd` | `09_phonopy_fd` | Current implementation directory is one index later than the normalized docs name. |
| `11_effective_mass` | `11_effective_mass` | Exact match. |
| `12_mobility` | `12_mobility` | Exact match. |

Future implementation should avoid renaming directories in the provenance/label PRs unless a separate migration task explicitly decides to standardize naming.

## Module-by-module readiness table

| Module | Prepare/render/copy parent files | Submit/status | Collect/parse | Existing provenance/labels | Recommended provenance write point | Recommended result-label write point | Existing information | Missing or weak information |
|---|---|---|---|---|---|---|---|---|
| `00_input` | `cmd_new` creates `00_input`, copies source POSCAR, writes metadata/audit/status files. | Not submitted. | Not collected as a calculation module. | No `module_provenance.yaml`; metadata and structure audit are partial provenance. | End of `cmd_new` after POSCAR, `metadata.yaml`, `structure_audit.yaml`, and manifest are written. | Usually none; optional `input_labels.yaml` or status label can mark source POSCAR and audit status. | Source POSCAR, project name, structure audit status. | Missing immutable source hash, source path label, normalized module identity, review state. |
| `01_opt` | `Module.setup_dir`; POSCAR from `00_input`; KPOINTS/POTCAR generated or reused; INCAR from `incar_opt.j2`; `OPTCELL` generated. | `cmd_submit`; Slurm via `sub.vasp`; `inspect_vasp_run` checks normal termination and ionic convergence. | `cmd_collect` reads OUTCAR energy/convergence; `OUTCARParser` can provide structured parser source. | Existing minimal `module_provenance.yaml`; no structured result labels. | Extend existing `write_module_provenance` from `setup_dir` after all generated inputs exist. | `cmd_collect` after OUTCAR parse, or module-local summary writer if added later. | Parent module, POSCAR source, template, executable, inheritance policy, convergence classification. | Missing source hashes, KPOINTS/POTCAR generator details, overwrite/restart state, parser version, explicit final/diagnostic labels. |
| `02_scf` | `Module.setup_dir`; POSCAR from `01_opt/CONTCAR`; CHGCAR policy from `inheritance_policy`; INCAR from `incar_scf.j2`. | `cmd_submit`; status through Slurm and `inspect_vasp_run`. | `cmd_collect`; OUTCAR parser can extract energy, Fermi level, convergence, band gap. | Existing minimal `module_provenance.yaml`; no structured labels. | Extend `write_module_provenance` from `setup_dir`; include parent `01_opt/CONTCAR`, POTCAR source, and runtime CHGCAR policy. | `cmd_collect` should write SCF method/source labels into project/module summary. | Dependency on opt, executable/template, Slurm status, final OUTCAR indicators. | Missing parser-source labels, CHGCAR actual-copy confirmation, electronic convergence detail, restart/overwrite state. |
| `03_band` / `03_pbeband` | `Module.setup_dir`; POSCAR from opt; runtime KPOINTS placeholder; `inheritance_policy` says KPOINTS generated at runtime with VASPKIT 302 and CHGCAR is required. | `cmd_submit`; `sub.vasp` pre/post commands handle runtime KPOINTS and VASPKIT 211 band-gap extraction. | `cmd_collect` reads `BAND_GAP` if present and OUTCAR status. | Existing minimal `module_provenance.yaml`; no source/method labels for band path or `BAND_GAP`. | Extend `write_module_provenance`; record runtime KPOINTS mode and parent CHGCAR requirement. | After VASPKIT 211 post-processing, or in `cmd_collect` when `BAND_GAP` is parsed. | Module dependency, template, runtime KPOINTS mode, post-processing command intent. | Missing exact generated KPOINTS provenance, VASPKIT path/version/task for post-processing, band-path label, parser/source file labels. |
| `04_dos` | `Module.setup_dir`; POSCAR from opt; CHGCAR required by policy; normal KPOINTS/POTCAR generation/reuse; INCAR from `incar_dos.j2`. | `cmd_submit`; status through Slurm and OUTCAR inspection. | `cmd_collect` can parse OUTCAR status/energy; DOSCAR-specific parsing is not yet represented in result labels. | Existing minimal `module_provenance.yaml`; no DOS method/source labels. | Extend `write_module_provenance`; include parent CHGCAR runtime-copy policy and KPOINTS density. | `cmd_collect` or future DOS parser summary writer. | Parent/dependency and generated inputs. | Missing DOSCAR source labels, energy grid/broadening labels, parser source, convergence-to-final status mapping. |
| `05_hse_scf` | `Module.setup_dir`; POSCAR from opt; CHGCAR required; INCAR from `incar_hse_scf.j2`. | `cmd_submit`; status through Slurm/OUTCAR. | `cmd_collect` currently treats it like a generic completed module. | Existing minimal `module_provenance.yaml`; no HSE method/result labels. | Extend `write_module_provenance`; record HSE template/settings and parent CHGCAR policy. | `cmd_collect` should write HSE SCF labels when OUTCAR is parsed. | Dependency/template/executable/status. | Missing exact hybrid-functional setting labels, parser source, restart state, convergence tolerance labels. |
| `05_hse_band` | `Module.setup_dir`; POSCAR from opt; runtime KPOINTS placeholder; `inheritance_policy` says VASPKIT 251 runtime KPOINTS and CHGCAR required; INCAR from `incar_hse_band.j2`. | `cmd_submit`; post command runs VASPKIT 252 for HSE band post-processing. | `cmd_collect` can read `BAND_GAP`; HSE-specific label source is weak. | Existing minimal `module_provenance.yaml`; no HSE band method/source labels. | Extend `write_module_provenance`; record VASPKIT 251 runtime KPOINTS mode and parent HSE/SCF dependency. | After VASPKIT 252 post-processing, or in `cmd_collect` when outputs are parsed. | Runtime KPOINTS mode, post-processing command intent, status. | Missing VASPKIT path/version/task labels, generated KPOINTS source hash, HSE band path/source labels. |
| `06_potential` / `07_vacuum` | Monolayer vacuum module uses `Module.setup_dir` for current `vacuum`; heterojunction `potential` also exists as `15_potential`. | `cmd_submit`; status via Slurm/OUTCAR. | Generic `cmd_collect`; potential/vacuum-specific parser labels are not yet established. | Existing minimal provenance for prepared module; no potential labels. | Extend `write_module_provenance`; include whether this is monolayer vacuum or heterojunction potential. | Future parser/summary writer after LOCPOT/potential extraction is defined. | Module config and dependency can be recorded. | Missing naming decision, LOCPOT/source-file labels, vacuum-level parser source, final diagnostic status. |
| `07_optical` / `08_optical` | `Module.setup_dir`; POSCAR from opt; CHGCAR required; `cmd_prepare` checks `allow_2d_loptics` and `postprocess=vaspkit_710`; INCAR from `incar_optical.j2`; post command runs VASPKIT 710. | `cmd_submit`; status via Slurm/OUTCAR and VASPKIT post-processing command in `sub.vasp`. | `cmd_collect` generic only; no structured parsing of `ABSORPTION_2D.dat`. | Existing minimal provenance; task_006/007 docs define required optical provenance but writer is not complete. | Extend `write_module_provenance`; record `LOPTICS`, `NBANDS`, VASPKIT path/version, task 710, input files, and expected `ABSORPTION_2D.dat`. | After VASPKIT 710 completes, or in `cmd_collect` when optical output files are present. | Verified server task mapping: VASPKIT 710 is 2D, 711 is bulk-only; config has VASPKIT path/version. | Missing actual output-file presence labels, REAL/IMAG fallback source choice, parser/tool labels, warning if 711 appears. |
| `08_phonopy_fd` / `09_phonopy_fd` | `setup_phonopy_fd_dir`; copies opt structure, generates/reuses inputs, writes phonopy manager script and settings. | `sub.vasp` executes phonopy finite-displacement manager; no normal single VASP submit semantics inside manager. | Manager should collect finite-displacement artifacts; project-level `cmd_collect` is generic. | Existing minimal provenance is augmented with `phonopy_fd` settings; no structured subtask manifest labels. | Extend `setup_phonopy_fd_dir` provenance and add subtask manifest before manager execution. | Manager collect phase should write finite-displacement result labels/manifest status. | Supercell/displacement settings can be recorded; executable path available in settings. | Missing subtask manifest schema, per-displacement status, force-file source labels, parser/source labels. |
| `11_effective_mass` | `setup_effective_mass_dir`; writes settings/runtime manager; manager `prepare_runs` creates band-edge source, target directories, explicit KPOINTS, `em_runs.yaml`. | `sub.vasp` runs embedded effective-mass manager; it launches per-target VASP runs locally through the job script. | Embedded manager `collect_results` writes `results/em_summary.yaml` and CSV. | Existing provenance is augmented with `effective_mass` settings; summary lacks full result-label schema. | Extend `setup_effective_mass_dir` and manager `prepare_runs` to record target-level provenance. | Embedded manager `collect_results` should write fit/source labels beside `em_summary.yaml`. | Target settings, parent CHGCAR use, run manifest, summary output. | Missing fit quality labels, source band-edge labels, parser/tool version, uncertainty and final diagnostic labels. |
| `12_mobility` | `setup_mobility_dir`; writes settings/runtime manager; manager `prepare_runs` creates strain relax/SCF/edge directories and copies parent inputs. | `sub.vasp` runs embedded mobility manager; per-strain VASP runs occur inside manager. | Embedded manager `collect_results` writes `results/mobility_summary.yaml`, CSV, and parses LOCPOT/vacuum when needed. | Existing provenance is augmented with mobility settings; summary lacks full result-label schema. | Extend `setup_mobility_dir` and manager `prepare_runs` to record strain-target provenance and overwrite policy. | Embedded manager `collect_results` should write mobility result labels beside `mobility_summary.yaml`. | Strain grid, parent OPT/SCF/EM sources, run manifest, summary output, some parser functions. | Missing deformation-potential fit labels, elastic fit quality, effective-mass source linkage, uncertainty labels, overwrite/restart status. |

## Cross-cutting insertion points

### `module_provenance.yaml`

The implementation should extend, not replace, the current `Module.write_module_provenance(...)` path.

Recommended additions:

- Add a shared provenance builder near `write_module_provenance` that assembles the schema from module identity, config, source files, generated inputs, executable/environment, dependency state, restart/overwrite policy, post-processing, and review state.
- Keep `setup_dir`, `setup_effective_mass_dir`, `setup_mobility_dir`, and `setup_phonopy_fd_dir` as the module-specific call sites because they know which files were generated and which manager/post-processing mode applies.
- For `00_input`, add a separate input-provenance writer in `cmd_new`, because it is not a `Module` instance.
- Record source-file hashes only after files exist and before submission; do not require server execution to build provenance.
- Capture runtime-copy intent from `inheritance_policy`, and later augment with actual-copy confirmation only if a runtime monitor/collector can verify it.

### `result_labels.yaml` or equivalent labels

Recommended write points:

- Generic VASP modules: `cmd_collect`, using `OUTCARParser` as the parser-source anchor and adding module-specific source files.
- Band/HSE band/optical post-processing: a collector step should inspect post-processing outputs and record the VASPKIT task/path/version used by the prepared `sub.vasp` command.
- Effective mass: embedded `EffectiveMassManager.collect_results`, next to `results/em_summary.yaml`.
- Mobility: embedded `MobilityManager.collect_results`, next to `results/mobility_summary.yaml`.
- Phonopy finite displacement: phonopy manager collect/finalization phase, with per-displacement manifest status.

Avoid writing labels during `cmd_submit`; submit-time code can record job IDs and intended dependency state, but final result labels require collected output evidence.

## Existing vs missing metadata

| Category | Existing source | Current readiness | Missing for implementation |
|---|---|---|---|
| Module identity | `PipelineBuilder.build`, `create_module`, module directory names | Mostly ready | Normalize documented name vs actual directory name without renaming directories. |
| Parent files | `inheritance_policy`, `setup_dir`, manager scripts | Partly ready | Actual hashes, optional actual runtime-copy confirmation, explicit missing-parent diagnostics. |
| Generated inputs | `render_incar`, KPOINTS/POTCAR generation, settings YAMLs | Ready for prepared files | Need source hashes and generator labels for VASPKIT/runtime-generated KPOINTS. |
| Executable/environment | `settings.yaml`, `render_submit_script`, manager scripts | Mostly ready | Need captured VASPKIT/VASP executable version where feasible without running calculations. |
| Dependency status | `cmd_prepare`, `cmd_submit`, `workflow_status.yaml` | Partly ready | Need normalized dependency label fields and distinction between intended dependency and verified completed dependency. |
| Convergence/status | `inspect_vasp_run`, `OUTCARParser`, `cmd_collect` | Partly ready | Need final-vs-diagnostic status labels, parser-source labels, per-subtask status for manager modules. |
| Restart/overwrite | Slurm `resubmit`, manager cleanup behavior | Weak | Need explicit overwrite policy, restart mode, previous-output preservation status. |
| Parser/tool source | `OUTCARParser`, VASPKIT post commands, manager parsers | Partly ready | Need per-result parser/tool labels and source-file list in each summary. |

## Implementation PR batches

### Batch A: core provenance writer and baseline VASP labels

Modules: `00_input`, `01_opt`, `02_scf`, `03_pbeband`, `04_dos`.

Scope:

- Extend `write_module_provenance` schema fields.
- Add an input provenance writer for `00_input`.
- Add generic result-label output in `cmd_collect` using `OUTCARParser`.
- Record source hashes, dependency intent/status, generated input labels, executable/environment references, and parser-source labels.

Reasoning: these modules share the most common lifecycle and should establish the stable schema before specialized modules are added.

### Batch B: HSE, optical, phonopy provenance and labels

Modules: `05_hse_scf`, `05_hse_band`, `08_optical`, `09_phonopy_fd`.

Scope:

- Add HSE-specific method labels and runtime KPOINTS provenance.
- Add optical provenance/labels for `LOPTICS`, `NBANDS`, VASPKIT task 710, and `ABSORPTION_2D.dat` outputs.
- Add guardrail labels that mark VASPKIT 711 as bulk-only and invalid for monolayer absorption.
- Add phonopy finite-displacement subtask manifest and result labels.

Reasoning: these modules require post-processing and/or subtask state beyond the baseline OUTCAR parser path.

### Batch C: fitted-result labels for effective mass and mobility

Modules: `11_effective_mass`, `12_mobility`.

Scope:

- Extend manager run manifests with target-level provenance.
- Write fit quality, uncertainty, transformation, parser/tool, and final diagnostic labels next to `em_summary.yaml` and `mobility_summary.yaml`.
- Record overwrite/restart policy for manager-created target directories.

Reasoning: these are multi-run fitted-result modules; labels should be generated where fits are assembled, not only in project-level `cmd_collect`.

## Non-goals for these implementation batches

- Do not rename current module directories as part of provenance/label implementation.
- Do not change Slurm submission semantics.
- Do not run server dry-runs, VASP, VASPKIT, or `sbatch` as part of documentation-only planning.
- Do not sync into the formal installed skill directory.
- Do not introduce raw reference bundles, PDFs, images, JSON caches, source trees, or binaries.

## Review questions for ChatGPT

- Should future implementation preserve the current exact directory names while exposing normalized `module_id` labels?
- Should `result_labels.yaml` be a separate file per module, or should equivalent labels be embedded into existing module summaries for fitted-result modules?
- Should actual parent-file copy verification be deferred until monitor/collect time, given that several parent files are copied at runtime through `sub.vasp` pre-commands?
