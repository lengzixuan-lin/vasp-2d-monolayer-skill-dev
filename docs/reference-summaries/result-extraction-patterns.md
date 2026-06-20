# Result Extraction Patterns

Primary sources:

- `vasp_references资料/vaspkit/vaspkit_readme.md`
- `vasp_references资料/JAMIP/JAMIP-V1.0.1.Manual-Chs.pdf-b1938462-d000-4f32-804a-ffd5d1b44a05/JAMIP.md`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/analysis/vasp/band.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/analysis/vasp/dos.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/analysis/vasp/optics.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/analysis/vasp/outcar.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/check.py`

Excluded raw sources:

- Raw VASPKIT/JAMIP PDFs, extracted figures, generated cache JSON, and source trees.

## General Extraction Rule

Every extracted value should carry:

- method label: PBE, HSE, SOC, post-processed, VASPKIT-converted, etc.
- source directory
- source file
- parent calculation
- convergence/status result
- parser or post-processing tool

This is the main lesson shared by VASPKIT and JAMIP: post-processing is powerful, but it must remain traceable.

## Band Gap, CBM, VBM, and Fermi Level

VASPKIT band post-processing reads Fermi energy, KPOINTS/KPATH labels, and band data. JAMIP band parsing extracts bands, k-points, CBM/VBM, direct/indirect gap, and effective-mass-related band-edge data from VASP outputs.

Review implications:

- Band gaps must state whether they are PBE, HSE, SOC, or another level.
- CBM/VBM should include k-point coordinates or high-symmetry labels when available.
- If Fermi energy is shifted to zero in output data, record that transformation.
- For HSE band, record whether the KPOINTS contain weighted SCF mesh plus zero-weight path points.

## DOS and PDOS

VASPKIT highlights total DOS, projected DOS by element/atom/orbital, selected sums, and Fermi-level shifting. JAMIP's DOS parser reads DOSCAR metadata such as energy range, Fermi level, NEDOS, total DOS, and projected DOS blocks.

Review implications:

- DOS outputs should identify TDOS versus PDOS.
- PDOS selections must record atom IDs, element names, and orbital channels.
- `LORBIT`, `NEDOS`, Fermi shift, spin channel, and DOS source file should be recorded.
- Reviewer-facing summaries should not silently mix DOS from different methods.

## Optical Outputs

VASPKIT's optical section derives spectra from dielectric-function data and can compute linear optical spectra from `vasprun.xml` or extracted dielectric files. JAMIP treats optical tasks as property modules and may compute NBANDS from parent SCF data.

Review implications:

- Label raw VASP dielectric response separately from converted optical spectra.
- Record `LOPTICS`, `NBANDS`, parent SCF/HSE source, and post-processing command/tool.
- For 2D optical absorption, require explicit conversion and units before using values in a paper.

## Vacuum Level and Work Function

VASPKIT's potential section uses planar average potential and Fermi level to derive work function.

Review implications:

- Work function must cite LOCPOT or potential source, Fermi-level source, and vacuum plateau selection.
- 2D slab orientation and vacuum axis must be confirmed before reporting vacuum-referenced values.
- Band-edge positions relative to vacuum should carry the same method label as the band edges.

## Phonon Stability

JAMIP finite-displacement patterns use generated displaced supercells, force extraction, `FORCE_SETS`, and derived phonon analysis. VASPKIT has finite-displacement and DFPT phonon menus, but for this skill finite displacement remains the safer default.

Review implications:

- Record supercell dimension, displacement generation tool, KPOINTS, force convergence, and whether `FORCE_SETS` was produced.
- Report whether imaginary modes are numerical noise, acoustic near-Gamma behavior, or actionable instabilities only after reviewing q-point/eigenvector context.
- Do not use softmode displacement as a first response before convergence checks.

## Effective Mass and Mobility

VASPKIT's effective-mass workflow and JAMIP's band-edge parsing both emphasize local k-points around band extrema and curvature fitting. JAMIP also treats mobility as a separate property workflow in the manual.

Review implications:

- Effective mass requires confirmed CBM/VBM and local k-line calculations.
- Fit range, fit quality, carrier type, band index, direction, and source files should be recorded.
- Mobility should be derived from effective mass plus deformation-potential calculations, not inferred from a single band run.
- Strain direction, strain magnitude, internal relaxation policy, and fitting quality are required for mobility provenance.

## Status and Failure Extraction

JAMIP checks OUTCAR for finish markers, ionic convergence, electronic convergence, and known error cases. It can load status from `.status` for continuation.

Review implications:

- Result extraction should refuse to summarize values from failed or incomplete jobs unless explicitly labeled diagnostic.
- The collector should include convergence status in summary outputs.
- Known failure signatures should be captured in status/provenance before proposing fixes.
