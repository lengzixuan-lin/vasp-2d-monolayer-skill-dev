# Task 005 Framework Audit

This audit checks whether the `vasp-2d-monolayer` skill framework is ready before module-by-module workflow review.

## Summary

The framework is mostly ready, but the entrypoint needed cleanup. `SKILL.md` now acts as a compact control plane with clearer scope, safety gates, progressive-loading links, and collaboration rules. Detailed design material remains in `references/`, `docs/reference-summaries/`, and `docs/improvement-plans/`.

## Findings and Actions

### Trigger and Scope

Finding:

- The skill should trigger for single-layer 2D monolayer POSCAR audits, monolayer VASP workflow planning, and maintenance of this skill repository.
- It should not silently handle heterojunctions, adsorption/catalysis, defects, molecules, bulk structures, or slabs.

Action:

- Rewrote the `SKILL.md` YAML description and opening scope text to make this boundary explicit.
- Updated `agents/openai.yaml` to say "single-layer 2D monolayer" and to include server dry-runs and real task edits in the confirmation boundary.

### Safety and Authority Boundaries

Finding:

- The repo already separates local edits from installed skill, server workflow, and real calculation tasks.
- The entrypoint needed a more compact list of gated actions.

Action:

- Consolidated the `SKILL.md` safety gates around explicit current-conversation confirmation for `ssh`, `sbatch`, server dry-runs, remote writes, installed-skill sync, and real calculation edits.
- Kept `references/server-boundary.md` as the detailed authority reference.

### Progressive Loading

Finding:

- `SKILL.md` should not carry all design detail.
- The task_003 summaries and task_004 improvement plan were useful but not clearly discoverable from the entrypoint.

Action:

- Added entrypoint links to:
  - `docs/reference-summaries/README.md`
  - `docs/improvement-plans/`
- Left detailed module behavior in `references/workflow-modules.md`.

### GitHub Collaboration Loop

Finding:

- Existing Issue, PR, and handoff templates already require changed-file count, explicit staging, scope boundary, safety status, and sync truth.
- No template changes were necessary for task_005.

Action:

- Recorded the framework audit in this file.
- Updated `CODEX_FEEDBACK.md` and the task handoff.

### Roadmap Readiness

Finding:

- Task_004's suggested next issue split used `task_005` for VASPKIT optical verification, but Issue #10 now uses task_005 for framework audit.

Action:

- Renumbered the suggested follow-up split in the task_004 plan so future work starts at `task_006`.

Recommended next sequence:

1. `task_006`: Verify VASPKIT optical task numbering only after explicit server-inspection approval.
2. `task_007`: Draft `module_provenance.yaml` schema and example records.
3. `task_008`: Draft finite-displacement phonon subtask manifest schema and review checks.
4. `task_009`: Review scheduler config and submit-template fields for configurability.
5. `task_010`: Draft result-summary method/source label schema and examples.
6. Begin module-by-module workflow implementation review after the schema and labeling foundations are accepted.

## Acceptance Check

- Workflow implementation files changed: no.
- Server operations performed: no.
- Real calculation tasks changed: no.
- Raw reference bundle or unsafe artifacts committed: no.
- `SKILL.md` remains compact and points to focused references: yes.
- Safety gates remain explicit: yes.
- Collaboration loop templates remain adequate: yes.
