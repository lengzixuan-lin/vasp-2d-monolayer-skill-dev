# Provenance and Result Label Schema

This document defines the documentation/spec target for future `module_provenance.yaml` records and result-summary labels. It is not an implementation contract for a parser yet. Future workflow implementation PRs should use this as the review baseline and may split it into stricter machine schemas after review.

## Design Rules

- Every module must explain what it is, where its inputs came from, what it generated, which executable/environment it used, and whether it is review-ready.
- Every reported value must carry method, source, parser/tool, convergence/status, transformation, and final/diagnostic status.
- Failed, incomplete, exploratory, or convergence-questionable values must not be promoted to final summaries without an explicit diagnostic label.
- Do not silently mix PBE, HSE, SOC, raw VASP, VASPKIT-converted, fitted, or diagnostic values.

## `module_provenance.yaml` Schema

Top-level fields:

```yaml
schema_version: "0.1"
module:
  id: "03_band"
  name: "pbe_band"
  method_label: "PBE"
  calculation_purpose: "line-mode band structure"
  task_id: "project-name/03_band"
source_structure:
  source_module: "01_opt"
  source_directory: "../01_opt"
  source_file: "../01_opt/CONTCAR"
  structure_role: "optimized_geometry"
parent_files:
  CONTCAR:
    policy: "copy_from_parent"
    source: "../01_opt/CONTCAR"
    required: true
  CHGCAR:
    policy: "copy_from_parent"
    source: "../02_scf/CHGCAR"
    required: true
  WAVECAR:
    policy: "not_used"
    source: null
    required: false
  POTCAR:
    policy: "reuse_from_opt"
    source: "../01_opt/POTCAR"
    required: true
  KPOINTS:
    policy: "generated_at_runtime"
    source: "VASPKIT 302 or KPATH.in"
    required: true
generated_inputs:
  incar_template: "templates/incar/incar_band.j2"
  incar_path: "INCAR"
  kpoints_source: "runtime VASPKIT 2D path"
  potcar_source: "../01_opt/POTCAR"
  extra_files:
    - "sub.vasp"
executable_environment:
  vasp_executable: "vasp_std"
  soc_executable: null
  mpi_launcher: "mpirun"
  environment_setup_ref: "config/settings.yaml"
runtime_conditions:
  scheduler_profile: "standard"
  resource_profile: "config/settings.yaml:default"
dependency_status:
  parent_modules:
    - module: "01_opt"
      required_status: "finished"
      convergence_required: true
    - module: "02_scf"
      required_status: "finished"
      convergence_required: true
restart_overwrite:
  restart_used: false
  overwrite_existing: false
  reason: null
post_processing:
  parser_or_tool: "band parser"
  command_or_source: "collector"
  source_files:
    - "EIGENVAL"
    - "KPOINTS"
    - "OUTCAR"
  output_files:
    - "results/band_summary.yaml"
review_state:
  status: "pending_review"
  reviewer_notes: []
  blocking_warnings: []
  accepted_diagnostic_only_values: []
```

### Field Requirements

Required fields:

- `schema_version`
- `module.id`
- `module.method_label`
- `module.calculation_purpose`
- `source_structure.source_module`
- `source_structure.source_file`
- `parent_files`
- `generated_inputs.incar_template`
- `generated_inputs.incar_path`
- `executable_environment.vasp_executable`
- `executable_environment.environment_setup_ref`
- `dependency_status.parent_modules`
- `restart_overwrite.restart_used`
- `restart_overwrite.overwrite_existing`
- `post_processing.source_files`
- `post_processing.output_files`
- `review_state.status`

Optional but recommended fields:

- `module.task_id`
- `runtime_conditions.scheduler_profile`
- `runtime_conditions.resource_profile`
- `executable_environment.soc_executable`
- `post_processing.command_or_source`
- `review_state.reviewer_notes`
- `review_state.blocking_warnings`
- `review_state.accepted_diagnostic_only_values`

### Allowed Review States

- `pending_review`: generated but not accepted.
- `reviewed_ok`: reviewed and acceptable for downstream use.
- `diagnostic_only`: useful for troubleshooting but not final science.
- `blocked`: missing dependency, failed convergence, unsafe inheritance, or unresolved method problem.
- `superseded`: replaced by a later restart or corrected run.

## Result-Summary Label Schema

Every extracted value should be represented with enough context to audit it without opening the full workflow tree.

```yaml
results:
  - value_name: "band_gap"
    value: 1.82
    unit: "eV"
    method_label: "HSE"
    source_module: "05_hse_band"
    source_directory: "05_hse_band"
    source_files:
      - "EIGENVAL"
      - "KPOINTS"
      - "OUTCAR"
    parent_calculation: "05_hse_scf"
    parser_or_tool:
      name: "band parser"
      version: "workflow-local"
      command_or_source: "collector"
    convergence_status:
      electronic: "converged"
      ionic: "not_applicable"
      task_status: "finished"
    transformation:
      label: "none"
      details: null
    uncertainty_or_fit_quality:
      type: "not_applicable"
      value: null
      notes: null
    result_status: "final"
    review_notes: []
```

Required result fields:

- `value_name`
- `unit`
- `method_label`
- `source_module`
- `source_directory`
- `source_files`
- `parent_calculation`
- `parser_or_tool.name`
- `convergence_status.task_status`
- `transformation.label`
- `result_status`

Optional but recommended fields:

- `value`
- `parser_or_tool.version`
- `parser_or_tool.command_or_source`
- `convergence_status.electronic`
- `convergence_status.ionic`
- `uncertainty_or_fit_quality`
- `review_notes`

Allowed `method_label` examples:

- `PBE`
- `HSE`
- `SOC`
- `HSE+SOC`
- `raw VASP`
- `VASPKIT-converted`
- `fitted`
- `post-processed`
- `diagnostic`

Allowed `result_status` values:

- `final`
- `diagnostic`
- `blocked`
- `superseded`
- `pending_review`

## Representative Module Examples

These examples show expected coverage, not final serialized files.

### `01_opt`

```yaml
module:
  id: "01_opt"
  method_label: "PBE"
  calculation_purpose: "2D geometry optimization with fixed vacuum"
source_structure:
  source_module: "00_input"
  source_file: "../00_input/POSCAR"
parent_files:
  CONTCAR: {policy: "not_applicable", source: null, required: false}
  CHGCAR: {policy: "not_used", source: null, required: false}
  WAVECAR: {policy: "not_used", source: null, required: false}
  POTCAR: {policy: "generated_or_reused_from_input", source: "POTCAR", required: true}
  KPOINTS: {policy: "generated_by_vaspkit_102", source: "KPOINTS", required: true}
generated_inputs:
  incar_template: "templates/incar/incar_opt.j2"
  extra_files: ["OPTCELL", "sub.vasp"]
review_state:
  status: "pending_review"
  blocking_warnings:
    - "OPTCELL must match the actual vacuum direction before submission."
```

### `02_scf`

```yaml
module:
  id: "02_scf"
  method_label: "PBE"
  calculation_purpose: "self-consistent charge density"
source_structure:
  source_module: "01_opt"
  source_file: "../01_opt/CONTCAR"
parent_files:
  CONTCAR: {policy: "copy_from_parent", source: "../01_opt/CONTCAR", required: true}
  CHGCAR: {policy: "not_used", source: null, required: false}
  WAVECAR: {policy: "not_required", source: null, required: false}
  POTCAR: {policy: "reuse_from_opt", source: "../01_opt/POTCAR", required: true}
  KPOINTS: {policy: "generated_regular_2d_mesh", source: "KPOINTS", required: true}
post_processing:
  source_files: ["OUTCAR", "vasprun.xml", "CHGCAR"]
  output_files: ["results/scf_summary.yaml"]
```

### `03_band`

```yaml
module:
  id: "03_band"
  method_label: "PBE"
  calculation_purpose: "line-mode band structure"
parent_files:
  CONTCAR: {policy: "copy_from_opt", source: "../01_opt/CONTCAR", required: true}
  CHGCAR: {policy: "copy_from_scf", source: "../02_scf/CHGCAR", required: true}
  WAVECAR: {policy: "not_used_if_kpoints_differ", source: null, required: false}
generated_inputs:
  kpoints_source: "runtime VASPKIT 302 2D path"
result_labels:
  expected:
    - "band_gap"
    - "CBM"
    - "VBM"
    - "Fermi_level"
```

### `04_dos`

```yaml
module:
  id: "04_dos"
  method_label: "PBE"
  calculation_purpose: "DOS and PDOS from SCF charge density"
parent_files:
  CHGCAR: {policy: "copy_from_scf", source: "../02_scf/CHGCAR", required: true}
post_processing:
  parser_or_tool: "DOS parser or VASPKIT DOS post-processing"
  source_files: ["DOSCAR", "vasprun.xml", "OUTCAR"]
review_state:
  blocking_warnings:
    - "PDOS selections must record atom IDs, element names, orbital channels, spin channel, and Fermi shift."
```

### `05_hse_scf`

```yaml
module:
  id: "05_hse_scf"
  method_label: "HSE"
  calculation_purpose: "HSE self-consistent charge density"
parent_files:
  CONTCAR: {policy: "copy_from_opt", source: "../01_opt/CONTCAR", required: true}
  CHGCAR: {policy: "optional_seed_from_pbe_scf", source: "../02_scf/CHGCAR", required: false}
  WAVECAR: {policy: "not_required", source: null, required: false}
generated_inputs:
  incar_template: "templates/incar/incar_hse_scf.j2"
post_processing:
  output_files: ["CHGCAR", "WAVECAR", "results/hse_scf_summary.yaml"]
```

### `05_hse_band`

```yaml
module:
  id: "05_hse_band"
  method_label: "HSE"
  calculation_purpose: "HSE band structure"
parent_files:
  CHGCAR: {policy: "copy_from_hse_scf", source: "../05_hse_scf/CHGCAR", required: true}
  WAVECAR: {policy: "avoid_if_kpoints_or_nbands_mismatch", source: null, required: false}
generated_inputs:
  kpoints_source: "VASPKIT 251 weighted mesh plus zero-weight path"
dependency_status:
  parent_modules:
    - {module: "05_hse_scf", required_status: "finished", convergence_required: true}
result_label_requirements:
  - "record whether KPOINTS contain weighted SCF mesh plus zero-weight path points"
```

### `07_optical`

```yaml
module:
  id: "07_optical"
  method_label: "raw VASP + VASPKIT-converted"
  calculation_purpose: "2D optical response"
parent_files:
  CHGCAR: {policy: "copy_from_scf_or_hse_parent", source: "../02_scf/CHGCAR", required: true}
generated_inputs:
  incar_template: "templates/incar/incar_optical.j2"
  required_tags: ["LOPTICS", "NBANDS"]
post_processing:
  parser_or_tool: "VASPKIT"
  command_or_source: "vaspkit -task 710"
  source_files: ["POSCAR", "vasprun.xml", "REAL.in", "IMAG.in"]
  output_files:
    - "ABSORPTION_2D.dat"
    - "REFLECTION_2D.dat"
    - "TRANSMISSION_2D.dat"
    - "REAL_OPTICAL_CONDUCTIVITY_2D.dat"
    - "IMAG_OPTICAL_CONDUCTIVITY_2D.dat"
review_state:
  blocking_warnings:
    - "VASPKIT 711 is bulk-only and must not be used for monolayer optical absorption summaries."
```

Optical result label example:

```yaml
value_name: "absorption_spectrum"
unit: "documented_by_VASPKIT_output"
method_label: "VASPKIT-converted"
source_module: "07_optical"
source_files: ["ABSORPTION_2D.dat", "vasprun.xml", "POSCAR"]
parent_calculation: "07_optical raw VASP LOPTICS"
parser_or_tool:
  name: "VASPKIT"
  version: "Standard Edition 1.3.1"
  command_or_source: "vaspkit -task 710"
convergence_status:
  task_status: "finished"
transformation:
  label: "2D optical conversion"
  details: "raw dielectric response converted by verified VASPKIT 710"
result_status: "final"
```

### `08_phonopy_fd`

```yaml
module:
  id: "08_phonopy_fd"
  method_label: "PBE"
  calculation_purpose: "finite-displacement phonons"
source_structure:
  source_module: "01_opt"
  source_file: "../01_opt/CONTCAR"
generated_inputs:
  extra_files: ["phonopy_disp.yaml", "displacement_manifest.yaml"]
post_processing:
  parser_or_tool: "phonopy"
  source_files: ["FORCE_SETS", "phonopy_disp.yaml", "displacement_manifest.yaml"]
  output_files: ["results/phonon_summary.yaml"]
review_state:
  blocking_warnings:
    - "Parent phonon task is not complete until all displacement subtasks finish and FORCE_SETS is traceable."
```

Phonon result label example:

```yaml
value_name: "minimum_phonon_frequency"
unit: "THz"
method_label: "post-processed"
source_module: "08_phonopy_fd"
source_files: ["FORCE_SETS", "phonopy.yaml"]
parser_or_tool: {name: "phonopy", command_or_source: "phonon collector"}
convergence_status:
  task_status: "finished"
  displacement_subtasks: "all_finished"
transformation:
  label: "finite-displacement force-constant fit"
uncertainty_or_fit_quality:
  type: "review_required"
  notes: "Imaginary modes require q-point/eigenvector and convergence review."
result_status: "diagnostic"
```

### `11_effective_mass`

```yaml
module:
  id: "11_effective_mass"
  method_label: "fitted"
  calculation_purpose: "local in-plane band-edge curvature fitting"
parent_files:
  CHGCAR: {policy: "copy_from_scf", source: "../02_scf/CHGCAR", required: true}
generated_inputs:
  kpoints_source: "local k-lines around confirmed CBM/VBM"
post_processing:
  source_files: ["EIGENVAL", "KPOINTS", "results/band_edge_source.yaml"]
  output_files: ["results/em_summary.yaml"]
```

Effective-mass result label example:

```yaml
value_name: "electron_effective_mass_x"
unit: "m0"
method_label: "fitted"
source_module: "11_effective_mass"
source_files: ["EIGENVAL", "KPOINTS", "results/em_fit.json"]
parent_calculation: "02_scf"
parser_or_tool: {name: "effective-mass fitter", command_or_source: "collector"}
transformation:
  label: "parabolic curvature fit"
  details: "CBM band, x direction, local k-window recorded in em_summary.yaml"
uncertainty_or_fit_quality:
  type: "fit_quality"
  value: "R2 or residual required"
result_status: "pending_review"
```

### `12_mobility`

```yaml
module:
  id: "12_mobility"
  method_label: "fitted"
  calculation_purpose: "deformation-potential mobility"
parent_files:
  effective_mass_summary:
    policy: "read_from_11_effective_mass"
    source: "../11_effective_mass/results/em_summary.yaml"
    required: true
generated_inputs:
  strain_series: "in-plane strain structures with fixed strained lattice and internal relaxation policy"
post_processing:
  source_files:
    - "../11_effective_mass/results/em_summary.yaml"
    - "strain_series/*/results/band_edge.yaml"
    - "strain_series/*/OUTCAR"
  output_files: ["results/mobility_summary.yaml"]
review_state:
  blocking_warnings:
    - "Mobility requires C2D, E1, effective mass source, strain direction, strain magnitude, and fit quality."
```

Mobility result label example:

```yaml
value_name: "electron_mobility_x"
unit: "cm^2 V^-1 s^-1"
method_label: "fitted"
source_module: "12_mobility"
source_files:
  - "results/mobility_summary.yaml"
  - "../11_effective_mass/results/em_summary.yaml"
parent_calculation: "11_effective_mass and strain SCF series"
parser_or_tool: {name: "deformation-potential fitter", command_or_source: "collector"}
transformation:
  label: "deformation-potential mobility"
  details: "uses C2D, E1, effective mass, temperature, and strain fit"
uncertainty_or_fit_quality:
  type: "fit_quality"
  notes: "Record C2D fit residual, E1 fit residual, strain range, and carrier type."
result_status: "pending_review"
```

## Review Checklist for Future Implementation PRs

- Does every prepared module write provenance before submission?
- Does each inherited file state copy/generate/not-used policy and source path?
- Are incompatible `WAVECAR` reuses blocked or labeled?
- Are executable, SOC executable, MPI launcher, and environment setup traceable?
- Are restart and overwrite choices explicit?
- Are parser/tool names and source files recorded for every summary value?
- Are failed or incomplete values marked `diagnostic`, `blocked`, or `pending_review` rather than `final`?
- Are optical, phonon, effective-mass, and mobility results labeled with their transformations and fit quality?
