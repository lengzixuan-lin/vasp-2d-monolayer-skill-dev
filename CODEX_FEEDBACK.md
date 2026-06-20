# CODEX_FEEDBACK.md

## GitHub Context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/6
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/7
- Branch: `task_003_curate-vasp-references`
- Task ID: `task_003_curate-vasp-references`

## This Round Summary

- Read online Issue #6 and confirmed it has no additional comments.
- Merged PR #4 into `main` with squash merge before starting task_003.
- Synced local `main` and created branch `task_003_curate-vasp-references`.
- Read local safety boundary docs before touching the reference bundle.
- Reviewed local `vasp_references资料/` text and source materials in read-only mode.
- Created curated Markdown summaries under `docs/reference-summaries/`.
- Did not commit raw PDFs, images, generated JSON/cache files, source trees, binaries, or the raw `vasp_references资料/` bundle.

## Implemented Changes

- Added `docs/reference-summaries/README.md`.
- Added `docs/reference-summaries/source-index.md`.
- Added `docs/reference-summaries/vaspkit-task-map.md`.
- Added `docs/reference-summaries/jamip-vasp-workflow-patterns.md`.
- Added `docs/reference-summaries/scheduler-submission-patterns.md`.
- Added `docs/reference-summaries/result-extraction-patterns.md`.
- Added task handoff at `docs/handoff/2026-06-20_task_003_curate-vasp-references.md`.

## Sources Summarized

- `vasp_references资料/vaspkit/vaspkit_readme.md`
- `vasp_references资料/JAMIP/JAMIP-V1.0.1.Manual-Chs.pdf-b1938462-d000-4f32-804a-ffd5d1b44a05/JAMIP.md`
- `vasp_references资料/JAMIP/jamip-1.0.2/README`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/abtools/vasp/*.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/compute/*.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/analysis/vasp/*.py`

## Intentionally Excluded

- Raw `vasp_references资料/` directory.
- Original PDFs.
- Extracted image folders.
- Generated parser/cache JSON files.
- HTML conversion outputs.
- JAMIP third-party source tree.
- Binaries and executables.

## Diff Reality Check

- Actual changed file count: 8.
- Large files added: no.
- Reference bundle changed: no raw bundle files committed.
- Third-party materials or binaries changed: no.
- `docs/reference-summaries/` changed: yes, curated Markdown only.
- `scripts/remote-workflow/` changed: no.
- Local workflow mirror changed: no.
- Server execution source changed: no.
- Formal installed skill directory changed: no.

## Not Implemented

- Did not edit `scripts/remote-workflow/**`.
- Did not run `ssh lilin`.
- Did not run `sbatch`.
- Did not run server-side dry runs.
- Did not delete, overwrite, or modify remote server files.
- Did not modify real calculation tasks.
- Did not sync changes into the formal installed skill directory.

## Checks Run

- `git status --short --branch`
- `C:\Program Files\GitHub CLI\gh.exe pr view 4 ...`
- `C:\Program Files\GitHub CLI\gh.exe pr merge 4 --squash --delete-branch`
- `git checkout main`
- `git pull --ff-only origin main`
- `git checkout -b task_003_curate-vasp-references`
- `C:\Program Files\GitHub CLI\gh.exe issue view 6 --comments`
- `C:\Program Files\GitHub CLI\gh.exe issue view 6 --json number,title,body,comments,labels,url,state`
- `Get-ChildItem -LiteralPath vasp_references资料 ...`
- `rg` and `Select-String` searches over VASPKIT/JAMIP local materials.
- `git diff --check`
- `git commit -m "task_003: curate vasp references"`
- `git push -u origin task_003_curate-vasp-references`
- `C:\Program Files\GitHub CLI\gh.exe pr create ...`

## Remaining Notes

- ChatGPT should review whether the summaries are specific enough to guide future workflow improvements without copying raw third-party material.
- Future tasks can use these summaries to propose targeted updates to `SKILL.md`, `references/workflow-modules.md`, or `scripts/remote-workflow/`, but this task intentionally does not change workflow code.
