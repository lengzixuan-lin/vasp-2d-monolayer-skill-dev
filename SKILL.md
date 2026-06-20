---
name: vasp-2d-monolayer
description: 审查、准备并执行单层二维材料的 VASP 计算流程。输入 POSCAR 后，用于生成和核查结构优化、SCF、能带、DOS/PDOS、HSE/SOC、功函数、光吸收、声子、AIMD、有效质量、迁移率等任务；适用于需要先列计算清单、确认后再在 lilin 服务器提交和监控 Slurm 任务的场景。
---

# VASP 单层二维材料计算

Use this skill when the user provides a monolayer 2D material POSCAR or asks for a complete monolayer VASP workflow on server `lilin`.

This skill is for single-layer 2D materials. For heterojunctions, adsorption, HER/OER, interface binding energy, charge-density difference, or built-in electric-field analysis, first switch to a heterojunction/catalysis workflow or explicitly ask the user to confirm the scope.

## Required Reading

Before planning, preparing, or submitting calculations, read:

- `references/monolayer-audit.md`

If auditing the implementation, also inspect the remote workflow:

```bash
ssh lilin 'find ~/calculation/1_dft/02_workflow -maxdepth 3 -type f | sort'
ssh lilin 'sed -n "1,240p" ~/calculation/1_dft/02_workflow/config/settings.yaml'
ssh lilin 'sed -n "1,260p" ~/calculation/1_dft/02_workflow/config/precision_standard.yaml'
```

## Server Context

- SSH alias: `lilin`
- Workflow root: `/home/lilin/calculation/1_dft/02_workflow`
- Projects root: `/home/lilin/calculation/1_dft/02_workflow/projects`
- Submit template currently expected by the user: `/home/lilin/input/sub.vasp`
- VASP executable in current config: `/home/soft/vasp/vasp.6.3.2_optcell/bin/vasp_std`
- SOC executable is expected to be `vasp_ncl` in the same directory unless `vasp.executable_ncl` overrides it.
- VASPkit executable in current config: `/home/lilin/software/vaspkit.1.3.1/bin/vaspkit`

Do not print SSH keys, tokens, or private credentials.

## Operating Rules

1. Treat the user-provided POSCAR as the authoritative input, but audit it before preparing jobs.
2. For every 2D geometry optimization, require `OPTCELL` and keep the vacuum direction fixed. The expected optimization control is in-plane relaxation with fixed `c` axis.
3. Before any `sbatch`, show the calculation list, input-generation assumptions, high-cost tasks, and known risks. Submit only after explicit user confirmation.
4. Use `/home/lilin/input/sub.vasp` as the current Slurm submit-template reference unless the user updates the path.
5. In the standard precision workflow, HSE-SCF, HSE-band, VASPKIT-710 optical conversion, and finite-displacement `phonopy_fd` are enabled by default. The old `IBRION=8` phonon task is retained only as optional `phonon_dfpt_check`. SOC and AIMD remain optional unless the user approves them. Strain, efield, CCD, Bader, and potential are disabled by default (heterojunction-only modules).
6. Record enough provenance for paper extraction: POSCAR source, pseudopotentials, ENCUT rule, KPOINTS rule, INCAR settings, job IDs, convergence status, and extracted values.
7. Before real submission, run `python workflow.py submit <project_name> --dry-run` on the server to validate ready files, `OPTCELL`, vacuum-axis detection, and dependency commands without calling `sbatch`.
8. Optical modules emit provenance warnings when `workflow_ready=false`. For 2D optical absorption, run VASP `LOPTICS` only as the raw response step and require VASPKIT 710 conversion before using the data in a paper. Effective mass uses `11_effective_mass`: a runtime manager reads the PBE band-edge source, generates explicit in-plane local k-lines around CBM/VBM, runs non-SCF VASP from the `02_scf` charge density, and fits curvature with quality checks. Mobility uses `12_mobility`: a deformation-potential manager reads `11_effective_mass/results/em_summary.yaml`, applies in-plane strain, relaxes internal coordinates with fixed strained lattice, runs strain SCF and local band-edge calculations, then fits `C2D`, `E1`, and the intrinsic acoustic-phonon-limited mobility.
9. For 2D phonons, prefer finite-displacement `phonopy_fd`. Use `stage: debug` for testing (`PREC=Accurate`, `EDIFF=1E-06`, nominal `dim=3 3 1`, scaled by in-plane lattice length) and `stage: production` for manuscript phonons (`PREC=Accurate`, `EDIFF=1E-07`, nominal `dim=4 4 1`). If an actionable imaginary mode appears, first review the q-point/eigenvector, then repeat with enlarged in-plane supercell, denser KPOINTS, tighter `EDIFF`, and only then run softmode displacement along the imaginary-mode eigenvector to search for a more stable structure.
10. Treat failed jobs as diagnosis-first events. Use `python workflow.py diagnose <project_name> [--module-dir <dir>]` to write error signatures and suggested actions into `workflow_status.yaml`; do not resubmit or auto-edit INCAR until the user approves the proposed fix.
11. During prepare, inspect each module's `module_provenance.yaml`. It records the parent directory, `CONTCAR/CHGCAR/WAVECAR` inheritance policy, runtime KPOINTS generation mode, VASP executable, and INCAR template.

## Priority Rules

P0 blockers before any submission:

- If the local mirror differs from `/home/lilin/calculation/1_dft/02_workflow`, do not assume the server will execute the local logic. Sync or patch the remote execution source first, after user confirmation.
- If the structure is a 2D material and the vacuum direction is not confirmed to be the POSCAR `c` axis, stop and ask the user before preparing optimization jobs.
- If an optimization job lacks `OPTCELL`, or `OPTCELL` does not keep the vacuum direction fixed, do not submit.
- If `POTCAR`, `KPOINTS`, `INCAR`, `POSCAR`, or `sub.vasp` is missing from a prepared calculation directory, do not submit.
- If the generated input choices conflict with the user's confirmed calculation scope, do not submit.

P1 input-generation requirements:

- Generate the first calculation's `KPOINTS` and `POTCAR` with VASPKIT task 102 using exactly:

```bash
(echo 102; echo 2; echo 0.04) | vaspkit
```

- Treat the `INCAR` written by VASPKIT 102 as disposable; overwrite it with the reviewed workflow template.
- Reuse the VASPKIT-generated `POTCAR` from the optimization directory for downstream calculations unless the element order or POSCAR composition changes.
- Use the MoS2 reference optimization INCAR at `/home/lilin/calculation/1_dft/01_pc/01_hterojunction/02_mos2_mose2/01_mos2/1-opt/INCAR` as a human-reviewed baseline, not as a blind copy. Keep `LREAL=.FALSE.`, `ADDGRID=.TRUE.`, `EDIFF=1E-06`, `EDIFFG=-0.01`, `IBRION=2`, and `NSW=100` unless there is a reason to change them. Question or adapt `ENCUT=340`, `ISTART=1`, `ISIF=3`, `IVDW=11`, `NCORE=8`, and smearing for each material.
- HSE is split into `05_hse_scf` and `05_hse_band`. `05_hse_scf` uses uniform KPOINTS and writes HSE `CHGCAR/WAVECAR`; `05_hse_band` depends on `05_hse_scf`, uses VASPKIT 251, reads the HSE-SCF `CHGCAR` with `ICHARG=1`, uses `ISTART=0` by default, and does not copy or require `WAVECAR` after changing KPOINTS. If `ISTART=1` is tested, the WAVECAR must be optional and k-point-compatible; never hard-require a mismatched HSE-SCF `WAVECAR`.

## Default Workflow

Phase 1: audit POSCAR and scope.

- `workflow.py new` writes `00_input/structure_audit.yaml` with element symbols, atom counts, selective dynamics, coordinate mode, lattice vectors, vacuum axis/gaps, and interatomic distance warnings.
- After the audit summary, the user is prompted to select material type: `1` = monolayer, `2` = heterojunction. Noninteractive use requires `--material-type monolayer|heterojunction`.
- Confirm it is truly a single-layer 2D material, not a heterojunction, bilayer, slab adsorption model, or molecular system.
- Check element order, atom counts, selective dynamics, coordinate mode, vacuum thickness, c-axis direction, and whether magnetic/SOC treatment is chemically plausible.
- Identify required paper outputs: lattice constants, band gap, CBM/VBM, Fermi level, vacuum level, work function, band-edge positions, DOS/PDOS, optical absorption, stability metrics, and transport descriptors.

Phase 2: prepare inputs.

- Generate KPOINTS and the initial POTCAR with VASPkit task 102: `(echo 102; echo 2; echo 0.04) | vaspkit`.
- Render INCAR after POTCAR exists; `ENCUT` must be computed from the real generated POTCAR `ENMAX` values as `max(ENMAX) * encut_factor`.
- For downstream calculations, reuse the optimization POTCAR unless the POSCAR composition/order changes.
- Generate INCAR from reviewed templates.
- For optimization, write `OPTCELL` during prepare and verify immediately that it locks the vacuum direction.
- For PBE band/HSE band, make prepared `KPOINTS` a runtime-generation placeholder; `sub.vasp` must generate the final KPATH/KPOINTS with VASPKIT before VASP starts.
- Each prepared module writes `kpoints_summary.yaml` recording whether 2D KPOINTS validation passed (Nkz=1 for regular meshes, kz=0 for line-mode).
- `sub.vasp` includes a 2D k-point runtime guard that checks kz=0 and Nkz=1 before VASP starts, exiting early on violations.
- For dependent tasks, use the optimized `CONTCAR` and copy required `CHGCAR`/`WAVECAR` from the correct parent job.
- For `band`, `dos`, `hse_scf`, `hse_band`, `optical`, `bader`, `ccd`, and `potential`, require the parent `CHGCAR` at runtime when the INCAR reads charge density. Remove `WAVECAR` for tasks whose KPOINTS, NBANDS, or method differ from the parent.

Phase 3: present a review checklist.

- Separate required tasks from optional high-cost tasks.
- Call out any nonstandard choices, especially `IVDW`, HSE-SCF/HSE-band split, HSE path generation, SOC executable, NBANDS for optics, `phonopy_fd` stage/supercell/KPOINTS, imaginary-mode follow-up policy, AIMD length/temperature, and mobility assumptions.
- Run `submit --dry-run` and include its result in the review.
- Ask for confirmation before submission.

Phase 4: submit and monitor after confirmation.

- Submit with Slurm from each prepared calculation directory.
- Track job IDs, queue status, runtime failures, electronic/ionic convergence, and missing outputs.
- Do not resubmit failed jobs without explaining the cause and proposed change.
- Use `resume` only after status review; it skips modules already marked `completed` or `completed_check` and submits unfinished modules whose dependencies are satisfied.

Phase 5: collect results.

- Extract structural parameters, total energies, band gap, CBM/VBM, vacuum level, work function, DOS/PDOS summaries, optical absorption, phonon stability, AIMD stability, effective masses, and mobility inputs/outputs.
- Mark values as PBE, HSE, SOC, or post-processed. Do not mix methods silently.

## Local Script Status

`scripts/remote-workflow/` is a synchronized local mirror of the remote workflow code, config, modules, templates, submit helpers, and collectors. `scripts/remote-workflow/SYNC_MANIFEST.md` records the remote source path, sync time, included files, excluded files, and SHA256 hashes.

Use the local mirror for review, diff, and proposed edits. Treat the server workflow as the execution source of truth until changes are explicitly synced back to `lilin`. Do not write changes back to the server or submit jobs without user confirmation.

When reviewing the remote workflow, specifically check for the known issues listed in `references/monolayer-audit.md`.
