# VASPKIT Optical Task Verification

## Verification Status

- Server inspection performed: yes.
- User confirmation: explicit current-conversation authorization for task_006 read-only server inspection.
- Authorization source: the user message immediately starting this task said, `执行 Issue #12 / task_006。授权本轮仅进行服务器只读检查，用于确认 VASPKIT 版本和 optical task 编号。禁止 sbatch、禁止 VASP 运行、禁止 server dry-run、禁止远程写入/删除/同步、禁止真实计算任务修改、禁止修改 scripts/remote-workflow/** 实现文件。完成后开 PR 给 ChatGPT 审查。`
- Server account inspected: `lilin`.
- Hostname reported by server: `node`.
- Working directory for checks: `/home/lilin`.
- Server writes performed: no.
- Write-safety check: after the VASPKIT task probes, `find /home/lilin -maxdepth 1 -mmin -5 -type f` returned no top-level recently modified regular files.
- Scheduler or VASP execution performed: no.

## Installed VASPKIT

- Path: `/home/lilin/software/vaspkit.1.3.1/bin/vaspkit`
- Version banner: `VASPKIT Standard Edition 1.3.1 (03 Dec. 2021)`

## Verified Optical Numbering

For the installed VASPKIT 1.3.1 on `lilin`:

- `710`: `Linear Optical Spectrums for Two-Dimensional Semiconductors`
- `711`: `Linear Optical Spectrums for Bulk Semiconductors`

This resolves the previous 710/711 ambiguity for monolayer workflows: use `710` for 2D optical post-processing and do not use `711` for monolayer optical absorption summaries.

## Read-Only Evidence

Read-only binary-string inspection of the installed executable exposed:

```text
======================= Optical Options =========================
710) Linear Optical Spectrums for Two-Dimensional Semiconductors
711) Linear Optical Spectrums for Bulk Semiconductors
```

Command-line probing in `/home/lilin` showed:

- `vaspkit -task 710` enters the 2D optical path and prints:
  - `See an example in vaspkit/examples/optical_2D.`
  - `The vacuum slab is supposed to be along z axis.`
  - `Error: The POSCAR File NOT Exist.`
- `vaspkit -task 711` enters the bulk optical path and prints:
  - `See an example in vaspkit/examples/Si_bse_optical.`
  - `This utility is NOT suitable for low-dimensional materials.`
  - `Error: The INCAR File NOT Exist.`

## Required Inputs

For `710` 2D optical post-processing:

- `POSCAR` is required.
- The VASPKIT example README states:
  - Step 1: optionally extract `REAL.in` and `IMAG.in` from `vasprun.xml`.
  - Step 2: run VASPKIT task `710`.
- The example extraction script reads `vasprun.xml` and writes `IMAG.in` and `REAL.in`.
- The example INCAR uses optical-response settings including `LOPTICS = .TRUE.` and `NBANDS`.

For `711` bulk optical post-processing:

- `INCAR` is required.
- VASPKIT explicitly warns that this utility is not suitable for low-dimensional materials.

## Expected Outputs for 2D Task 710

The installed VASPKIT 1.3.1 `optical_2D` examples contain these output names:

- `ABSORPTION_2D.dat`
- `REFLECTION_2D.dat`
- `TRANSMISSION_2D.dat`
- `REAL_OPTICAL_CONDUCTIVITY_2D.dat`
- `IMAG_OPTICAL_CONDUCTIVITY_2D.dat`

## Recommended Workflow Wording

Future workflow code and docs should refer to:

- `vaspkit -task 710` for VASPKIT-converted 2D optical spectra after VASP `LOPTICS` output is available.
- `vaspkit -task 711` only for bulk semiconductor optical spectra, not for monolayer results.

Future integration target:

- A later reviewed task should link this verification note from `references/workflow-modules.md` or the optical workflow docs before changing any optical workflow implementation.

Optical result summaries should label:

- raw VASP dielectric response separately from VASPKIT-converted 2D spectra;
- required inputs, including `POSCAR`, `vasprun.xml` or derived `REAL.in`/`IMAG.in`, and optical INCAR settings such as `LOPTICS` and `NBANDS`;
- generated source files, especially `ABSORPTION_2D.dat` when reporting 2D absorption.

## Commands Run

All commands were read-only inspection commands executed via `ssh lilin`.

```bash
hostname
whoami
pwd
command -v vaspkit
type -a vaspkit
timeout 8s vaspkit -version
timeout 8s vaspkit --version
timeout 8s vaspkit -h
printf "7\n0\n" | timeout 10s vaspkit
printf "710\n0\n" | timeout 10s vaspkit
printf "711\n0\n" | timeout 10s vaspkit
printf "71\n0\n0\n" | timeout 10s vaspkit
printf "71\n711\n0\n0\n" | timeout 10s vaspkit
printf "71\n710\n0\n0\n" | timeout 10s vaspkit
strings /home/lilin/software/vaspkit.1.3.1/bin/vaspkit | grep ...
ls -l vasprun.xml REAL.in IMAG.in
timeout 10s vaspkit -task 710
timeout 10s vaspkit -task 711
find /home/lilin -maxdepth 1 -mmin -5 -type f
find /home/lilin/software/vaspkit.1.3.1/examples ...
sed -n ... /home/lilin/software/vaspkit.1.3.1/examples/optical_2D/README
sed -n ... /home/lilin/software/vaspkit.1.3.1/examples/optical_2D/graphene/optical.sh
sed -n ... /home/lilin/software/vaspkit.1.3.1/examples/optical_2D/graphene/INCAR
sed -n ... /home/lilin/software/vaspkit.1.3.1/examples/Si_BSE_optical/README
sed -n ... /home/lilin/software/vaspkit.1.3.1/examples/Si_BSE_optical/optical.sh
```

No `sbatch`, VASP execution, server dry-run, remote write/delete/sync, or real calculation edit was performed.
