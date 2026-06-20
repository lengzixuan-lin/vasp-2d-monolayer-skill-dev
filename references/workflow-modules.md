# Monolayer Workflow Modules

This file holds stable module and dependency details for the monolayer 2D VASP workflow. Load it when selecting modules, reviewing prepared inputs, checking dependencies, or collecting results.

## Default Module Order

Default standard chain:

1. `01_opt`: geometry optimization with `OPTCELL`.
2. `02_scf`: PBE SCF from optimized structure.
3. `03_band`: PBE band structure with runtime VASPKIT KPATH generation.
4. `04_dos`: DOS/PDOS from SCF charge density.
5. `05_hse_scf`: HSE06 self-consistent calculation.
6. `05_hse_band`: HSE06 band structure from HSE-SCF charge density.
7. `06_potential`: electrostatic potential and vacuum-level analysis when enabled for monolayer band-edge alignment.
8. `07_optical`: raw VASP `LOPTICS` response plus VASPKIT 710 conversion before using 2D optical absorption data.
9. `08_phonopy_fd`: finite-displacement phonons.
10. `11_effective_mass`: local in-plane band-edge curvature fitting.
11. `12_mobility`: deformation-potential mobility workflow using effective-mass results.

Optional or high-cost modules requiring explicit user confirmation:

- AIMD.
- SOC.
- Production phonons if only debug phonons were requested initially.

Disabled by default or heterojunction/catalysis scope:

- strain regulation
- external electric field
- charge-density difference
- Bader charge transfer
- interface binding energy
- HER/OER adsorption free energies

## Parent Files and Dependencies

- Downstream modules normally use the optimized `CONTCAR` from `01_opt`.
- Reuse the optimization `POTCAR` unless POSCAR composition or element order changes.
- Modules that read charge density must require parent `CHGCAR` at runtime before VASP starts.
- Remove or avoid `WAVECAR` when KPOINTS, NBANDS, functional, or method differ from the parent.
- Each prepared module should write `module_provenance.yaml` with parent directory, `CONTCAR/CHGCAR/WAVECAR` inheritance policy, runtime KPOINTS mode, VASP executable, and INCAR template.

Modules that normally require parent `CHGCAR`:

- `03_band`
- `04_dos`
- `05_hse_scf`
- `05_hse_band`
- `07_optical`
- `bader`
- `ccd`
- `potential`

## KPOINTS Rules

- Initial `KPOINTS` and `POTCAR` come from VASPKIT task 102:

```bash
(echo 102; echo 2; echo 0.04) | vaspkit
```

- For 2D regular meshes, require `Nkz=1`.
- For line-mode KPOINTS, require `kz=0`.
- PBE band and HSE band prepared `KPOINTS` may be placeholders; final KPOINTS are generated at runtime by VASPKIT.
- Each prepared module should write `kpoints_summary.yaml` with 2D validation results.
- `sub.vasp` should exit before VASP if the 2D KPOINTS guard fails.

## Module Notes

### Optimization

- Every 2D optimization requires `OPTCELL`.
- The expected intent is in-plane lattice relaxation with fixed vacuum direction.
- For a POSCAR with vacuum along `c`, the current OPTCELL intent is:

```text
110
110
000
```

### HSE

- Split HSE into `05_hse_scf` and `05_hse_band`.
- `05_hse_scf` uses uniform KPOINTS and writes HSE `CHGCAR/WAVECAR`.
- `05_hse_band` depends on `05_hse_scf`, uses VASPKIT 251, reads HSE-SCF `CHGCAR` with `ICHARG=1`, and should not hard-require a mismatched HSE-SCF `WAVECAR`.
- Preserve method labels during extraction.

### Optical

- `LOPTICS` is the raw VASP response step for 2D optical analysis.
- Require VASPKIT 710 conversion before treating outputs as 2D optical absorption data.
- Require explicit and justified `NBANDS`.

### Effective Mass

- Effective mass is complete only after `11_effective_mass` produces reviewed outputs.
- The manager should identify CBM/VBM, generate in-plane local k-lines, run non-SCF VASP from `02_scf` charge density, fit curvature, and write `results/em_summary.yaml`.

### Mobility

- Mobility is complete only after `12_mobility` produces reviewed outputs.
- It should read `11_effective_mass/results/em_summary.yaml`, apply in-plane strain, relax internal coordinates with fixed strained lattice, run strain SCF and local band-edge calculations, fit `C2D` and `E1`, and write `results/mobility_summary.yaml`.

### Phonons

- Prefer finite-displacement `phonopy_fd` over the old single-job `IBRION=8` check.
- Debug runs use `PREC=Accurate`, `EDIFF=1E-06`, nominal `dim=3 3 1`, scaled by in-plane lattice length.
- Production runs use `PREC=Accurate`, `EDIFF=1E-07`, nominal `dim=4 4 1`.
- Keep `dim_z=1` for 2D systems.
- If an actionable imaginary mode appears, review q-point and eigenvector first. Then repeat with enlarged in-plane supercell, denser KPOINTS, and tighter `EDIFF` before searching along the imaginary-mode eigenvector.

## Result Labels

Never report a value without method and source.

Use clear labels:

- PBE
- HSE
- SOC
- post-processed
- VASPKIT-converted

Do not mix PBE, HSE, SOC, and post-processed values silently in summaries or manuscripts.
