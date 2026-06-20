# JAMIP VASP Workflow Patterns

Primary sources:

- `vasp_references资料/JAMIP/JAMIP-V1.0.1.Manual-Chs.pdf-b1938462-d000-4f32-804a-ffd5d1b44a05/JAMIP.md`
- `vasp_references资料/JAMIP/jamip-1.0.2/README`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/tasks.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/setvasp.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/vaspflow.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/check.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/errorkey.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/vaspio.py`

Excluded raw sources:

- JAMIP original PDF, extracted figures, parser/cache JSON, HTML conversion files, and full Python source tree.

## Workflow Decomposition

JAMIP separates VASP workflow concerns into several layers:

- Task declaration: a compact task string or task object is converted into categories such as relaxation, MD, SCF, electronic properties, optical properties, phonons, mechanics, exchange-correlation extensions, and custom workflows.
- Input generation: `SetVasp` writes POSCAR, POTCAR, KPOINTS, INCAR, OPTCELL, vdW kernel, and external files.
- Execution orchestration: `VaspFlow` sequences relaxation, MD, SCF, property calculations, phonons, and custom workflows.
- Status checking: `CheckStatus` records finish/success states and supports continuation from previous completed stages.
- Queue/task-pool management: compute modules decide which tasks should run and how many to submit.

Pattern useful for this skill:

- Keep task declaration separate from file rendering and from submission.
- Preserve a status/provenance layer that can be read before resume.
- Treat property modules as children of successful parent stages rather than as independent jobs.

## Module Ordering

The JAMIP VASP flow follows this broad order:

1. Optional convergence test.
2. Relaxation.
3. Molecular dynamics, if requested.
4. SCF.
5. Property calculations grouped into electronic, magnetic, optical, phonon, and mechanic categories.
6. Custom workflow modules.

For `vasp-2d-monolayer`, this supports the current rule that optimization and SCF must be complete before dependent band/DOS/optical/transport tasks. It also reinforces that AIMD and phonons should be explicit modules rather than incidental INCAR variants.

## Input Generation Patterns

Observed patterns:

- POSCAR is written from a structured object with element order and selective dynamics preserved.
- POTCAR is assembled from a pseudopotential library based on structure element order.
- ENMAX/ENMIN are parsed from POTCAR and used to set ENCUT.
- KPOINTS can be explicit, line-mode, reciprocal, Gamma, Monkhorst-Pack, or replaced by `KSPACING`.
- OPTCELL is handled as an external file when present.
- vdW kernels and external files are copied only when configured.

Review implications:

- `vasp-2d-monolayer` should continue deriving ENCUT from the generated POTCAR, not from static element metadata.
- POTCAR reuse is safe only when element order and composition are unchanged.
- OPTCELL should be part of generated-file validation for 2D optimization.
- External files should be declared explicitly in provenance, not silently copied.

## Parent-Child Dependency and Inheritance

JAMIP loads structure from parent `CONTCAR` or `POSCAR` before child tasks. It handles `CHGCAR` and `WAVECAR` based on file existence and INCAR inheritance intent:

- If parent `CHGCAR` exists and the child reads charge density, the file may be copied or linked.
- If `CHGCAR` is required but absent, the task should fail rather than proceed silently.
- If parent `WAVECAR` exists, `ISTART` may be set to 1; otherwise it falls back to 0.
- Reusing `WAVECAR` is unsafe when k-points, NBANDS, or method are incompatible.

Review implications:

- The monolayer workflow should keep per-module parent file policies in `module_provenance.yaml`.
- HSE-band, PBE-band, optics, and effective-mass jobs should define exactly which parent files are required.
- Any automatic `ISTART`/`ICHARG` inference must be visible in logs or provenance.

## HSE and Band Patterns

JAMIP distinguishes ordinary band calculations, HSE gap, and HSE band modes. The manual describes adding band-edge or low-density k-path points to self-consistent KPOINTS for hybrid calculations.

Review implications:

- HSE-SCF and HSE-band should stay split.
- HSE-band should inherit the correct HSE-SCF charge density, not a mismatched PBE WAVECAR.
- KPOINTS generation should be recorded with both weighted mesh and zero-weight path provenance.

## Optical Patterns

JAMIP treats optical tasks as a property module depending on a parent electronic state. It computes or updates NBANDS when not explicitly set.

Review implications:

- NBANDS should be explicit or computed from a documented rule.
- Optical output must distinguish raw VASP dielectric response from post-processed spectra.
- GW/BSE-style optical patterns should remain out of the default monolayer workflow unless explicitly requested.

## Phonon Patterns

JAMIP models finite-displacement phonons as a parent phonon object plus generated displacement subtasks. It can generate `FORCE_SETS`, run parallel subtasks, and then continue to derived phonon properties such as softmode or Gruneisen workflows.

Review implications:

- Finite-displacement phonons should remain the preferred 2D phonon path.
- The workflow should track each displacement subtask and require all required force calculations before claiming phonon success.
- Softmode follow-up should be a separate reviewable step after imaginary-mode diagnosis.

## Effective Mass and Mobility-Relevant Patterns

JAMIP's effective-mass flow first locates band edges, checks for no-gap cases, generates local k-paths around CBM/VBM, and then fits curvature. The manual also mentions mobility and deformation-potential style workflows.

Review implications:

- Effective mass should depend on a verified band edge.
- Local k-line generation and fit quality should be recorded.
- Mobility should depend on reviewed effective-mass output and separate strain calculations, not a single static INCAR.

## Error Handling and Resume Policy

JAMIP status checking uses OUTCAR and log markers to distinguish finished, ionic convergence, electronic convergence, and task success. It supports continuation from `.status` and has error-key mappings for known VASP issues such as NPAR, WAVECAR mismatch, and non-collinear executable errors.

Review implications:

- `vasp-2d-monolayer` should keep diagnosis-first failure handling.
- Error signatures should be written to status/provenance before proposing edits.
- Automatic correction should remain off unless the user approves the proposed fix.
