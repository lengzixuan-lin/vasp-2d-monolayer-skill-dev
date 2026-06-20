---
name: vasp-2d-monolayer
description: 审查、规划、准备并在用户确认后执行单层二维材料 VASP 工作流。用于单层 2D POSCAR 审查，结构优化、SCF、能带、DOS/PDOS、HSE/SOC、功函数、光吸收、声子、AIMD、有效质量、迁移率等 monolayer 任务规划，也用于维护本 skill 的规则、reference 文档、本地 workflow mirror 和 ChatGPT/Codex 协作边界。遇到异质结、吸附、HER/OER、界面、电荷差分、ssh、sbatch、远程写入或真实计算任务修改时，必须先确认范围和权限。
---

# VASP 单层二维材料计算

Use this skill when the user provides a monolayer 2D material POSCAR, asks for a monolayer VASP workflow on `lilin`, or asks to review/improve this skill's rules, references, local workflow mirror, or handoff notes.

This skill is only for single-layer 2D materials unless the user explicitly confirms a different scope. For heterojunctions, adsorption, HER/OER, interface binding energy, charge-density difference, built-in electric fields, defects, molecules, bulk, or surface slabs, stop and ask for scope confirmation or switch to a more appropriate workflow.

## Required Reading

Read only the files needed for the task:

- Always read `references/monolayer-audit.md` before planning, preparing, submitting, or collecting monolayer calculations.
- Read `references/workflow-modules.md` when selecting modules, checking dependencies, reviewing generated inputs, or extracting results.
- Read `references/server-boundary.md` before any GitHub handoff, installed-skill sync, server verification, remote sync, `ssh`, `sbatch`, or real calculation action.
- For implementation review, inspect the local mirror files first:
  - `scripts/remote-workflow/SYNC_MANIFEST.md`
  - `scripts/remote-workflow/config/settings.yaml`
  - `scripts/remote-workflow/config/precision_standard.yaml`

## Safety Gates

- Never run `ssh lilin`, `sbatch`, remote deletion, remote overwrite, remote file synchronization, or real calculation-task modification unless the user explicitly confirms that exact action in the current conversation.
- Treat local repository edits as proposed changes only. They do not change the installed skill, the `lilin` workflow, or any real calculation unless the user separately requests synchronization.
- Do not print GitHub tokens, SSH keys, license files, private credentials, or machine-local secrets.
- Before any real submission, show the calculation list, input-generation assumptions, high-cost modules, dependency chain, dry-run result, and known risks. Submit only after explicit user confirmation.
- Before Codex reads PR/Issue comments or pushes with GitHub CLI, confirm `gh` is authenticated. In PowerShell:

```powershell
gh auth status --hostname github.com
gh auth login --hostname github.com --web --git-protocol https
```

If `gh` is installed but not on PATH on Windows, try `C:\Program Files\GitHub CLI\gh.exe`.

## Monolayer Workflow

Phase 1: audit POSCAR and scope.

- Confirm the structure is a single-layer 2D material, not a heterojunction, bilayer, adsorption model, molecular system, bulk, defect, or charged-cell workflow.
- Check element order, atom counts, coordinate mode, selective dynamics, lattice vectors, vacuum axis, vacuum thickness, interatomic distances, and whether magnetic/SOC treatment may be needed.
- `workflow.py new` writes `00_input/structure_audit.yaml`; review it before preparing jobs.

Phase 2: prepare inputs.

- Generate the initial `KPOINTS` and `POTCAR` with VASPKIT task 102:

```bash
(echo 102; echo 2; echo 0.04) | vaspkit
```

- Treat the VASPKIT-generated `INCAR` as disposable; overwrite it with the reviewed workflow template.
- Compute `ENCUT` from the generated `POTCAR` `ENMAX` values.
- For optimization, require `OPTCELL` and keep the vacuum direction fixed.
- Use `references/workflow-modules.md` for module dependencies, parent files, runtime KPOINTS generation, and method labels.

Phase 3: present a review checklist.

- Separate required tasks from optional high-cost tasks.
- Call out nonstandard choices such as `IVDW`, HSE split, SOC executable, NBANDS for optics, phonon stage, AIMD settings, and mobility assumptions.
- After the user confirms server dry-run access, run `python workflow.py submit <project_name> --dry-run` before real submission and include its result in the review.
- Ask for confirmation before any `sbatch`.

Phase 4: submit and monitor only after confirmation.

- Submit with Slurm only from prepared calculation directories after user approval.
- Track job IDs, queue status, runtime failures, convergence status, and missing outputs.
- Diagnose failed jobs before proposing fixes; do not resubmit or auto-edit INCAR without approval.

Phase 5: collect results.

- Extract structural parameters, total energies, band gap, CBM/VBM, Fermi level, vacuum level, work function, DOS/PDOS, optical absorption, phonon stability, AIMD stability, effective masses, and mobility outputs as applicable.
- Mark every value as PBE, HSE, SOC, or post-processed. Do not mix methods silently.

## Collaboration Rules

- ChatGPT plans and reviews Issues, PR diffs, `CHATGPT_REVIEW.md`, `CODEX_FEEDBACK.md`, and handoff files.
- Codex implements local edits, runs local checks, updates `CODEX_FEEDBACK.md`, writes `docs/handoff/YYYY-MM-DD_task_xxx.md`, commits, pushes, and opens PRs when requested.
- Stage explicit files only; do not use `git add .`.
- Every task PR should state changed-file count, reference-bundle status, script changes, formal skill sync status, and server execution-source status.

## Local Mirror Status

`scripts/remote-workflow/` is a synchronized local mirror for review, diff, and proposed edits. Treat `/home/lilin/calculation/1_dft/02_workflow` as the execution source of truth until the user explicitly approves synchronization back to `lilin`.
