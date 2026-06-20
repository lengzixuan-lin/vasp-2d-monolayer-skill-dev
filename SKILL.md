---
name: vasp-2d-monolayer
description: Review, plan, prepare, and, only after explicit confirmation, run VASP workflows for single-layer 2D monolayer materials. Use for monolayer POSCAR audits, monolayer VASP workflow planning, and maintenance of this skill's rules, references, local workflow mirror, and ChatGPT/Codex handoff process. For heterojunctions, adsorption/catalysis, defects, molecules, bulk, slabs, SSH, Slurm submission, remote writes, real calculation edits, or installed-skill sync, require explicit scope and permission confirmation first.
---

# VASP 2D Monolayer Workflow

Use this skill when the user provides a single-layer 2D material POSCAR, asks for a monolayer VASP workflow on `lilin`, or asks to review/improve this skill's rules, references, local workflow mirror, or handoff notes.

This skill is not the default workflow for heterojunctions, adsorption, HER/OER, interface binding energy, charge-density difference, built-in electric fields, defects, molecules, bulk structures, or surface slabs. If scope is ambiguous, stop and ask for confirmation before planning or preparing jobs.

## Required Reading

Read only the files needed for the task.

- Read `references/monolayer-audit.md` before planning, preparing, submitting, or collecting monolayer calculations.
- Read `references/workflow-modules.md` when selecting modules, checking dependencies, reviewing generated inputs, or extracting results.
- Read `references/server-boundary.md` before any GitHub handoff, installed-skill sync, server verification, remote sync, `ssh`, `sbatch`, or real calculation action.
- Read `docs/reference-summaries/README.md` when reviewing VASPKIT/JAMIP-derived design lessons.
- Read `docs/improvement-plans/` when continuing planned framework, schema, scheduler, provenance, or result-label review tasks.

For implementation review, inspect local mirror files first:

- `scripts/remote-workflow/SYNC_MANIFEST.md`
- `scripts/remote-workflow/config/settings.yaml`
- `scripts/remote-workflow/config/precision_standard.yaml`

## Safety Gates

- Never run `ssh lilin`, `sbatch`, server dry-runs, remote deletion, remote overwrite, remote file synchronization, installed-skill sync, or real calculation-task modification unless the user explicitly confirms that exact action in the current conversation.
- Treat repository edits as proposed local changes only. They do not change the installed skill, the `lilin` workflow, or any real calculation unless the user separately requests synchronization.
- Do not print GitHub tokens, SSH keys, license files, private credentials, or machine-local secrets.
- Before any real submission, show the calculation list, input-generation assumptions, high-cost modules, dependency chain, dry-run result, and known risks. Submit only after explicit user confirmation.
- Before Codex reads PR/Issue comments or pushes with GitHub CLI, confirm `gh` is authenticated. If `gh` is not on PATH on Windows, use `C:\Program Files\GitHub CLI\gh.exe`.

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
- After the user confirms server dry-run access, Codex or another authorized operator may run `python workflow.py submit <project_name> --dry-run` before real submission. ChatGPT reviews the returned dry-run result; it does not perform server-side actions.
- Ask for confirmation before any `sbatch`.

Phase 4: submit and monitor only after confirmation.

- Submit with Slurm only from prepared calculation directories after user approval.
- Track job IDs, queue status, runtime failures, convergence status, and missing outputs.
- Diagnose failed jobs before proposing fixes; do not resubmit or auto-edit INCAR without approval.

Phase 5: collect results.

- Extract structural parameters, total energies, band gap, CBM/VBM, Fermi level, vacuum level, work function, DOS/PDOS, optical absorption, phonon stability, AIMD stability, effective masses, and mobility outputs as applicable.
- Mark every value as PBE, HSE, SOC, raw VASP, VASPKIT-converted, or other post-processed output. Do not mix methods silently.

## Collaboration Rules

- ChatGPT plans and reviews Issues, PR diffs, `CHATGPT_REVIEW.md`, `CODEX_FEEDBACK.md`, and handoff files.
- Codex implements local edits, runs local checks, updates `CODEX_FEEDBACK.md`, writes `docs/handoff/YYYY-MM-DD_task_xxx.md`, commits, pushes, and opens PRs when requested.
- Stage explicit files only; do not use `git add .`.
- Every task PR should state changed-file count, reference-bundle status, script changes, formal skill sync status, and server execution-source status.

## Local Mirror Status

`scripts/remote-workflow/` is a synchronized local mirror for review, diff, and proposed edits. Treat `/home/lilin/calculation/1_dft/02_workflow` as the execution source of truth until the user explicitly approves synchronization back to `lilin`.
