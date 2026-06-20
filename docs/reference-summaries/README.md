# Reference Summaries for Task 003

This directory contains curated Markdown summaries derived from the local `vasp_references资料/` bundle. It is intended as reviewable learning material for ChatGPT and Codex, without committing the raw reference bundle or unsafe large artifacts.

## Source Bundle

Local source bundle:

- `vasp_references资料/vaspkit/`
- `vasp_references资料/JAMIP/`

Reviewed source categories:

- VASPKIT README/tutorial Markdown converted from the local VASPKIT PDF bundle.
- JAMIP Chinese manual Markdown converted from the local JAMIP PDF bundle.
- JAMIP VASP workflow source files under `jamip-1.0.2/jamip/abtools/vasp/`.
- JAMIP scheduler and task-pool source files under `jamip-1.0.2/jamip/compute/`.
- JAMIP VASP result extraction source files under `jamip-1.0.2/jamip/analysis/vasp/`.

## What Is Intentionally Excluded

The following local materials are intentionally not committed:

- Original PDFs.
- Extracted image folders.
- Generated layout/model/cache JSON files.
- Third-party source trees.
- Tool executables or binaries.
- Raw `vasp_references资料/` directory contents.

The summaries cite local source paths so reviewers can trace claims without placing the raw bundle in Git history.

## How ChatGPT Should Use These Files

Use these summaries as a learning layer before reviewing future changes to:

- `SKILL.md`
- `references/workflow-modules.md`
- `references/server-boundary.md`
- `scripts/remote-workflow/`

The summaries are not a request to copy JAMIP or VASPKIT behavior directly. They are meant to identify reusable workflow design patterns, safety checks, provenance requirements, and result-extraction expectations that can guide future `vasp-2d-monolayer` reviews.

## Future Review Targets

These summaries point to several concrete follow-up review targets:

- Verify the installed VASPKIT optical task numbering before hard-coding 710/711-style post-processing commands.
- Review the module provenance schema for parent directory, `CONTCAR`, `CHGCAR`, `WAVECAR`, runtime KPOINTS, executable, INCAR template, and post-processing source.
- Review finite-displacement phonon subtask manifests so every displacement job, `FORCE_SETS`, and imaginary-mode follow-up remains traceable.
- Review scheduler configuration boundaries: queue/partition, resources, environment setup, MPI launcher, VASP executable, SOC executable, and maximum concurrent jobs should stay configurable.
- Review result-summary method/source labels for band gap, CBM/VBM, Fermi level, vacuum level, work function, DOS/PDOS, optical spectra, phonons, effective mass, and mobility.

## Summary Files

- `source-index.md`: source paths, categories, summary status, and exclusion rationale.
- `vaspkit-task-map.md`: VASPKIT tasks relevant to KPOINTS, POTCAR, band paths, optics, 2D tools, DOS, potential, and effective mass.
- `jamip-vasp-workflow-patterns.md`: JAMIP VASP workflow ordering, dependency, inheritance, phonon, optics, and error-handling patterns.
- `scheduler-submission-patterns.md`: scheduler abstraction, script generation, task-pool status, queue throttling, and safety implications.
- `result-extraction-patterns.md`: band gap, CBM/VBM, DOS/PDOS, optical, potential/work function, phonon, effective mass, and method/source labeling patterns.
