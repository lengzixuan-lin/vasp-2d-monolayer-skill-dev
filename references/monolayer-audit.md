# 单层二维材料 VASP 工作流审查清单

This checklist defines what must be true before using server time for a monolayer 2D material workflow.

## P0/P1 Execution Priorities

P0 blockers:

- Do not treat the local mirror as executable truth if it differs from `/home/lilin/calculation/1_dft/02_workflow`; sync or patch the remote execution source first after user confirmation.
- Do not submit a 2D optimization unless `OPTCELL` exists and fixes the vacuum direction.
- Do not submit if the POSCAR vacuum axis is not confirmed to be the POSCAR `c` axis.
- Do not submit if any prepared directory is missing `POSCAR`, `POTCAR`, `KPOINTS`, `INCAR`, or `sub.vasp`.
- Do not submit if the workflow scope is ambiguous between monolayer, heterojunction, adsorption/catalysis, defect, or charged-cell calculations.
- Do not resubmit or auto-edit failed jobs before reviewing `python workflow.py diagnose <project_name>` output and getting user approval for the fix.

P1 requirements:

- Generate the initial `KPOINTS` and `POTCAR` with VASPKIT task 102:

```bash
(echo 102; echo 2; echo 0.04) | vaspkit
```

- Overwrite the VASPKIT-generated `INCAR` with the reviewed workflow INCAR.
- Reuse the optimization-step `POTCAR` for downstream jobs unless the POSCAR element order or composition changes.
- Compute `ENCUT` from the real generated `POTCAR` `ENMAX` values, not from static element metadata.
- Treat `/home/lilin/calculation/1_dft/01_pc/01_hterojunction/02_mos2_mose2/01_mos2/1-opt/INCAR` as a useful optimization reference, but not as a universal standard.
- During `prepare`, require each module directory to contain `module_provenance.yaml` recording parent directory, `CONTCAR/CHGCAR/WAVECAR` inheritance, runtime KPOINTS mode, VASP executable, and INCAR template.

## Scope Gate

Use this workflow only when the input is a single-layer 2D material.

Do not silently treat these as monolayers:

- van der Waals heterojunctions
- bilayers or multilayers
- adsorption/catalysis models
- doped/alloy systems where material identity cannot be inferred from element count alone
- slabs with adsorbates or charged defects

If the structure is ambiguous, inspect the POSCAR geometry and ask the user before preparing jobs.

## Mandatory Input Audit

Check and report:

- POSCAR element symbols and atom counts
- coordinate mode and whether selective dynamics is present
- lattice vectors and which direction is vacuum
- vacuum thickness
- minimum interatomic distances
- whether the cell is already relaxed or generated from a database
- whether magnetism, SOC, or charged calculations may be needed

`workflow.py new` now writes these to `00_input/structure_audit.yaml` automatically.
The audit warns when the vacuum axis is not `c` and when interatomic distances are unusually small.

Do not modify the POSCAR without explicit user approval.

## 2D Optimization Rule

Every structure optimization for a 2D material must include `OPTCELL`.

Expected intent:

- allow in-plane lattice relaxation
- keep the vacuum direction fixed
- keep the `c` axis length unchanged when `c` is the vacuum direction

Current remote workflow intent is `OPTCELL` equivalent to:

```text
110
110
000
```

During prepare and again before submission, verify the generated `01_opt/OPTCELL` exists and matches the actual vacuum direction. If the vacuum is not along `c`, stop and ask the user.

## Optimization INCAR Baseline

The MoS2 reference optimization INCAR is broadly reasonable for a 2D semiconductor in this server environment because it uses:

- `LREAL = .FALSE.`
- `ADDGRID = .TRUE.`
- `ISMEAR = 0`
- `NELM = 90`, `NELMIN = 6`
- `EDIFF = 1E-06`
- `NSW = 100`, `IBRION = 2`
- `EDIFFG = -0.01`
- `LWAVE = .FALSE.`, `LCHARG = .FALSE.`

Do not copy it blindly. Re-check these items for each material:

- `ISIF = 3` is acceptable only with the OPTCELL-enabled VASP build and a correct `OPTCELL` file that fixes the vacuum direction. Without `OPTCELL`, it may change the vacuum/c-axis.
- `ENCUT = 340` may be too low for some PAW potentials. Prefer the workflow rule based on POTCAR `ENMAX` unless the user approves a convergence-tested fixed ENCUT.
- `ISTART = 1` is harmless only if VASP falls back cleanly without `WAVECAR`; for a fresh optimization, `ISTART = 0` is cleaner.
- `IVDW = 11` is DFT-D3 zero damping in VASP, not D3(BJ). Use `IVDW = 12` for D3(BJ), or document why `11` is intended.
- `NCORE = 8` is server/performance-specific, not a materials parameter.
- `SIGMA = 0.1` is usable for relaxation, but `0.05` is often cleaner for final SCF/DOS of semiconductors.

## Module and Server Detail References

Keep this file focused on audit and submission readiness. Load these focused references when details are needed:

- `references/workflow-modules.md`: module order, optional/high-cost modules, dependency files, KPOINTS rules, HSE/optical/phonon/effective-mass/mobility notes, and method labels.
- `references/server-boundary.md`: local mirror versus server execution truth, confirmation gates, GitHub CLI preflight, sync truth, and handoff wording.

## Submission Review Template

Before asking the user for approval to submit, present:

- project path and POSCAR source
- generated task directories
- exact tasks to submit now
- optional tasks deferred
- whether `OPTCELL` was generated and checked
- VASP executable and submit template path
- estimated resource class or expected high-cost steps
- nonstandard assumptions and unresolved risks
- output from `python workflow.py submit <project_name> --dry-run`, if the user has confirmed server dry-run access

Only submit after the user explicitly agrees.

## Result Extraction Minimum

For manuscript use, collect at minimum:

- relaxed lattice constants and layer thickness/vacuum thickness
- final total energy and convergence status
- band gap, CBM, VBM, and Fermi level with method labels
- vacuum level and work function
- DOS/PDOS files and orbital contribution notes
- optical absorption onset and peak positions, if optical was run
- phonon imaginary-mode check, if phonon was run
- AIMD energy/temperature stability, if AIMD was run
- effective masses and mobility assumptions, if transport was run

Never report a value without its calculation level and source file.
