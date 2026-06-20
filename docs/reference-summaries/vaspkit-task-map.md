# VASPKIT Task Map for Monolayer Workflow Review

Primary source:

- `vasp_references资料/vaspkit/vaspkit_readme.md`

Excluded raw sources:

- VASPKIT original PDF, extracted images, and generated JSON/cache files under `vasp_references资料/vaspkit/`.

## High-Level Lessons

VASPKIT is best treated as an input/post-processing helper, not as an unchecked source of final workflow truth. Its task prompts are useful for deterministic command sequences, but the `vasp-2d-monolayer` skill should still review generated files, preserve provenance, and enforce 2D-specific guards.

## Input Generation

Relevant tasks:

- `101`: customize INCAR.
- `102`: generate KPOINTS for SCF.
- `103`: generate POTCAR with default setting.
- `104`: generate POTCAR with user-specified potential.
- `108`: successive procedure to generate VASP files and check.
- `109`: check VASP files.

Task `102` is the most directly relevant command for this skill. VASPKIT documents both command-line and piped interactive forms. The workflow should continue to use the explicit prompt sequence:

```bash
(echo 102; echo 2; echo 0.04) | vaspkit
```

Review implications:

- The KPOINTS/POTCAR generation step must be run in a directory containing a reviewed POSCAR.
- VASPKIT-generated INCAR content should remain disposable unless explicitly reviewed.
- POTCAR generation depends on `~/.vaspkit` pseudopotential paths and policy tags such as POTCAR family and recommended potential selection.
- The skill should keep element order/POSCAR composition checks before reusing POTCAR downstream.

## 2D Band-Path Generation

Relevant tasks:

- `302`: generate 2D KPATH/KPOINTS-style band path files.
- `303`: 3D counterpart, not the default for monolayer materials.

VASPKIT's 2D band path generation assumes the vacuum slab is along the `c` axis and recommends standardizing the 2D cell before generating paths. In the MoS2 example, task `302` writes `PRIMCELL.vasp`, `KPATH.in`, and `HIGH_SYMMETRY_POINTS`.

Review implications:

- The monolayer workflow should confirm the vacuum direction before any 2D KPATH generation.
- Generated `KPATH.in` should be treated as a runtime artifact and preserved for provenance.
- For line-mode KPOINTS, `kz` should remain zero.
- For automated workflows, the task should report the suggested k-path and let reviewers check whether the path is scientifically appropriate.

## Hybrid-Functional Band KPOINTS

Relevant task:

- `251`: generate hybrid-functional band-structure KPOINTS with weighted SCF mesh plus zero-weight k-path points.

VASPKIT describes task `251` as reading `KPATH.in` and generating a KPOINTS file suitable for hybrid band calculations. It has separate resolution prompts for the normal weighted mesh and the k-path spacing.

Review implications:

- HSE band should be separate from HSE-SCF.
- HSE-band KPOINTS are not compatible with a blindly reused parent WAVECAR.
- The skill should require parent HSE-SCF `CHGCAR` where charge-density inheritance is intended.
- The prompt history and generated KPOINTS metadata should be recorded.

## DOS and PDOS

Relevant tasks:

- `11`: DOS post-processing menu.
- `111`: total DOS.
- `112` / `113`: projected DOS by selected atoms or elements.
- `114` / `115`: summed projected DOS by selected atoms and orbitals.

VASPKIT emphasizes direct server-side extraction from `DOSCAR` and `vasprun.xml`, Fermi-level shifting, and flexible atom/orbital selection.

Review implications:

- DOS/PDOS summaries should record whether Fermi energy was shifted to zero.
- Selection rules for atom/orbital sums must be documented in result provenance.
- A reviewer should know whether DOS/PDOS came from VASPKIT, local parser output, or manual post-processing.

## Optical Processing

Relevant tasks:

- `711`: linear optical spectra.
- `713`: transition dipole moment for band-structure calculations.

The local README describes linear optical spectra derived from the frequency-dependent dielectric function and notes that VASPKIT can read `vasprun.xml` or pre-extracted dielectric files.

Review implications:

- VASP `LOPTICS` is only the raw response step.
- The skill should keep VASPKIT optical conversion as an explicit post-processing step before using optical absorption in manuscript summaries.
- Optical output must be labeled as raw VASP dielectric response, VASPKIT-converted spectrum, or other post-processed data.

Issue #6 mentions VASPKIT 710, while the local README exposes the current optical menu around `711`. Future review should verify the exact task number in the server's installed VASPKIT version before hard-coding it.

## Effective Mass

Relevant task family:

- `912`: VASPKIT effective-mass pre/post-processing in the local README example.

The example generates local zero-weight k-points around band extrema and then fits band curvature. It warns that the method is constrained to non-charged, non-magnetic semiconductors in that documented implementation.

Review implications:

- Effective mass should not be treated as complete just because an INCAR exists.
- The workflow must confirm CBM/VBM locations, generate explicit local in-plane k-lines, run a compatible non-SCF calculation, and store fit quality.
- Degenerate band edges need special caution.

## Potential and Work Function

Relevant section:

- Planar and macroscopic averaged potential.

The README links work-function analysis to plane-averaged electrostatic potential and Fermi level extraction.

Review implications:

- Vacuum level and work function must cite the LOCPOT/potential source and Fermi-level source.
- For 2D slabs, the vacuum plateau and cell orientation must be reviewed before reporting values.

## 2D Toolkit Caveats

Relevant 2D tools:

- `921`: center atomic layer along z.
- `922`: resize vacuum thickness.
- `923`: standardize 2D crystal cell.
- `926`: 2D elastic constants.
- `927`: band edges referenced to vacuum level.
- `929`: summary for relaxed 2D structure.

Review implications:

- Automatic 2D standardization can change POSCAR geometry, so it requires user approval if applied to the authoritative input structure.
- The skill can use these task names as review prompts, but should not silently rewrite user POSCARs.
- 2D elastic or vacuum-referenced band-edge summaries should be method-labeled and source-labeled.
