# CHATGPT_REVIEW.md

## GitHub Context

- Issue: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/issues/1
- PR: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/2
- Branch: `task_001_review-github-bridge`
- Task ID: `task_001_review-github-bridge`

## ChatGPT Review Source

- Review URL: https://github.com/lengzixuan-lin/vasp-2d-monolayer-skill-dev/pull/2#pullrequestreview-4536381171
- Review result: changes recommended before merge.

## Review Goal

- Check whether the GitHub bridge can support ChatGPT planning/review and Codex implementation for future `vasp-2d-monolayer` skill work.
- Focus on scope clarity, traceability, safety boundaries, and reviewability.

## Main Findings

1. PR description and actual diff are inconsistent.
2. The full `vasp_references资料/` bundle makes the PR large and difficult to review.
3. `.gitignore` was too broad after allowing the full reference bundle.
4. Issue, PR, and handoff templates need stronger fields for changed-file count, allowed files, out-of-scope items, large-file exceptions, and remote-action boundaries.
5. `SKILL.md` should not make server SSH inspection default required reading.
6. PR links need to be backfilled in this file, `CODEX_FEEDBACK.md`, and the handoff file.
7. Local workflow mirror state must be clearly separated from the server execution source.

## Risk Level

- Overall: high until PR scope and reference-bundle handling are made explicit.
- Repository/review risk: high because the current PR changes 404 files and includes 399 reference-bundle files.
- Copyright/publication risk: medium-high for third-party PDFs, images, sources, configs, and binaries.
- Remote-compute safety risk: medium; no remote compute was performed, but docs need stronger wording.
- Maintainability risk: medium-high unless templates capture diff reality and sync truth.

## Recommended Codex Changes

- Strengthen `.gitignore` to block future full bundles, generated caches, PDFs, images, and binaries unless explicitly approved.
- Add diff reality, scope boundary, large-file exception, and sync truth fields to PR, Issue, and handoff templates.
- Update collaboration docs to require actual diff/file-count reporting and local-mirror vs server-source clarity.
- Move `SKILL.md` server SSH checks out of default required reading and into a user-confirmed server verification section.
- Backfill PR #2 URL in review, feedback, and handoff records.
- Do not delete or split `vasp_references资料/` without explicit user confirmation.

## User Confirmation Still Needed

1. Should the full `vasp_references资料/` bundle remain in PR #2, be moved to a separate PR, or be replaced by curated summaries?
2. Are third-party PDFs, images, source trees, config files, and binaries allowed to remain in long-term git history?
3. Will the repository remain private permanently?
4. Should server verification always require explicit user confirmation before SSH?
5. May Codex remove or restructure the reference bundle in this PR?

## Forbidden Direct Actions

- Do not run `ssh lilin`.
- Do not run `sbatch`.
- Do not delete, overwrite, or modify remote server files.
- Do not modify real calculation tasks.
