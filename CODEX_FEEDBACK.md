# CODEX_FEEDBACK.md

## GitHub Context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/3
- Follow-up Issue / ChatGPT review: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/5
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/4
- Branch: `task_002_review-skill-rules`
- Task ID: `task_002_review-skill-rules`

## This Round Summary

- Started from clean branch `task_002_review-skill-rules`.
- Read open Issues and PR #4 with GitHub CLI.
- Found follow-up Issue #5 requesting progressive-loading documentation structure.
- Refactored `SKILL.md` into a shorter entrypoint with trigger/scope, required reading, safety gates, high-level workflow, collaboration rules, and local mirror status.
- Moved stable module details into `references/workflow-modules.md`.
- Moved server/GitHub/sync safety boundaries into `references/server-boundary.md`.
- Reduced duplication in `references/monolayer-audit.md` by keeping it focused on audit/submission readiness and pointing to focused references.
- Added a new progressive-loading handoff file.

## Implemented Changes

- `SKILL.md` is now shorter and points to focused reference files for progressive loading.
- `references/monolayer-audit.md` keeps P0/P1 blockers, scope gate, mandatory input audit, optimization rules, submission review template, and result extraction minimum.
- `references/workflow-modules.md` documents module order, parent/child dependencies, required files, KPOINTS rules, module notes, and method labels.
- `references/server-boundary.md` documents local mirror versus server truth, confirmation gates, GitHub CLI preflight, handoff sync truth, and submission boundary.
- `docs/handoff/2026-06-20_task_002_progressive-loading-docs.md` records the follow-up review implementation.

## Diff Reality Check

- Actual changed file count relative to `main`: 9.
- Large files added: no.
- Reference bundle changed: no.
- Third-party materials or binaries changed: no.
- `references/` changed: yes, focused Markdown references only.
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
- Did not commit raw `vasp_references资料/` bundles, PDFs, images, source trees, generated cache JSON, or binaries.

## Checks Run

- `git status --short --branch`
- `C:\Program Files\GitHub CLI\gh.exe issue list --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev --state open --limit 20`
- `C:\Program Files\GitHub CLI\gh.exe pr list --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev --state open --limit 20`
- `C:\Program Files\GitHub CLI\gh.exe issue view 5 --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev --json number,title,body,comments,labels,url`
- `C:\Program Files\GitHub CLI\gh.exe issue view 3 --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev --json number,title,body,comments,labels,url`
- `C:\Program Files\GitHub CLI\gh.exe pr view 4 --repo lengzixuan-lin/vasp-2d-monolayer-skill-dev --json number,title,body,comments,reviews,url`
- `rg --files references docs`
- `rg -n "^## " references/monolayer-audit.md`
- `git diff --stat`
- `git diff --check`
- `git diff --name-only -- scripts/remote-workflow`
- `C:\Program Files\GitHub CLI\gh.exe pr edit 4 ...`

## Remaining Notes

- Ask ChatGPT to review whether `SKILL.md` is now concise enough without losing essential safety gates.
- Ask ChatGPT to check whether the new reference split improves progressive loading and whether server/calculation boundaries remain explicit.
