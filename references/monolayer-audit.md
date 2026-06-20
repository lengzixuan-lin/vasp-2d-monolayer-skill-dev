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

## Default Versus Optional Tasks

Default standard chain (enabled by default in precision_standard.yaml):

- structure optimization
- SCF
- PBE band structure
- DOS/PDOS
- HSE06 self-consistent calculation
- HSE06 band structure
- electrostatic potential and vacuum level
- work function and band-edge alignment from consistent references
- optical absorption with VASP `LOPTICS` plus VASPKIT 710 conversion
- phonon stability using finite-displacement `phonopy_fd`
- effective mass (`11_effective_mass`; local in-plane k-line curvature fitting around CBM/VBM)
- carrier mobility (`12_mobility`; 2D deformation-potential manager using `11_effective_mass` results)

Optional/high-cost chain, requiring confirmation:

- AIMD
- SOC (spin-orbit coupling)

Disabled by default (heterojunction-only modules):

- strain regulation
- external electric field
- charge-density difference (CCD)
- Bader charge transfer
- electrostatic potential (LVTOT/LVHAR)

Not default for a monolayer-only workflow:

- interface binding energy
- charge-density difference across an interface
- Bader charge transfer across an interface
- HER/OER adsorption free energies

These require a separate adsorption, catalysis, or heterojunction scope.

## Server Workflow Checks

Before trusting generated jobs, inspect or verify these known risk points in `/home/lilin/calculation/1_dft/02_workflow`:

- `config/precision_standard.yaml`: `IVDW=11` is DFT-D3 zero damping in VASP, not D3(BJ). Use `IVDW=12` for D3(BJ), or document why `11` is intended.
- `modules/base.py`: VASPKIT task 102 should be run as `102 -> 2 -> 0.04`; the INCAR it generates must be overwritten by the reviewed template.
- `modules/base.py`: downstream jobs should reuse the optimization POTCAR unless the POSCAR composition or element order changes.
- `modules/base.py`: the old heuristic-only `detect_material_type()` has been replaced by a user prompt (1=monolayer, 2=heterojunction) in `workflow.py new`. The `--material-type` CLI flag provides a noninteractive override. The heuristic remains available as a fallback for programmatic use.
- `modules/base.py`: POSCAR parsing assumes VASP 5 element-symbol and count lines; check behavior for selective dynamics and unusual POSCAR formats.
- `templates/sub.j2`: avoid hardcoded VASP executable paths when config already provides `vasp.executable`.
- SOC calculations require `vasp_ncl`; verify `sub.vasp` switches from `vasp_std` to `vasp_ncl` for SOC modules.
- HSE workflows must distinguish `05_hse_scf` from `05_hse_band` and preserve method labels during result extraction.
- HSE band workflows using VASPKIT 251 regenerate KPOINTS; do not reuse a PBE `WAVECAR` with the changed hybrid-band KPOINTS.
- For `band`, `dos`, `hse_scf`, `hse_band`, `optical`, `bader`, `ccd`, and `potential`, the generated submit script should hard-fail before VASP if the required parent `CHGCAR` is missing.
- PBE band and HSE band directories should not show an ordinary SCF KPOINTS as if it were final; prepared `KPOINTS` should clearly state that final KPOINTS are generated at runtime by VASPKIT 302 or 251.
- Each prepared module now writes `kpoints_summary.yaml` with 2D validation results (Nkz=1 check for regular meshes, kz=0 check for line-mode KPOINTS).
- `sub.vasp` now includes a 2D k-point runtime guard that exits before VASP if kz != 0 or Nkz != 1.
- Optical calculations need an explicit and justified `NBANDS`, not just an unexplained default. For 2D materials, `LOPTICS` is only the raw VASP response step; require VASPKIT 710 conversion before treating the output as 2D optical absorption data.
- Effective-mass and mobility calculations are not complete just because a VASP INCAR exists. Effective mass requires the `11_effective_mass` manager output: band-edge confirmation, explicit in-plane local KPOINTS around CBM/VBM, curvature-fit quality checks, and `results/em_summary.yaml`. Mobility requires the `12_mobility` manager output: reviewed effective-mass inputs, in-plane strain relax/SCF subruns, LOCPOT vacuum alignment, `C2D`/`E1` fitting quality checks, and `results/mobility_summary.yaml`.
- For 2D phonons, `phonopy_fd` is preferred over the old single-job `IBRION=8` check. Debug runs use `PREC=Accurate`, `EDIFF=1E-06`, and nominal `dim=3 3 1` adjusted by in-plane lattice length; production runs use `PREC=Accurate`, `EDIFF=1E-07`, and nominal `dim=4 4 1`. Keep `dim_z=1`, generate `FORCE_SETS`, and review any actionable imaginary mode before softmode displacement. If imaginary modes persist, repeat with enlarged in-plane supercell, denser KPOINTS, and tighter `EDIFF` before searching along the imaginary eigenvector.
- AIMD needs user-approved temperature, timestep, and simulation length.
- Email notification should not hard-code a personal email address unless the user asks for it.
- Any `cmd_submit` or dependency scheduler code should be tested in dry-run mode before bulk submission.
- Automatic retry should remain disabled by default. Failure handling should record an error signature and suggested actions in `workflow_status.yaml`.

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
- output from `python workflow.py submit <project_name> --dry-run`

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
