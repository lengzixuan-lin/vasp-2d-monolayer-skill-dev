# Server and Collaboration Boundary

This file defines what is local review, what changes GitHub state, and what requires explicit user confirmation before touching `lilin` or real calculations.

## Local Versus Server Truth

- `scripts/remote-workflow/` is a local mirror for review, diff, tests, and proposed edits.
- `/home/lilin/calculation/1_dft/02_workflow` is the server execution source until the user explicitly approves synchronization.
- Editing this repository does not update the installed skill at `C:\Users\11658\.codex\skills\vasp-2d-monolayer`.
- Editing this repository does not update `lilin`, prepared calculation directories, Slurm jobs, or real project outputs.

## Actions Allowed Without Extra Confirmation

Allowed when requested by the user for a GitHub/Codex task:

- Read local repository files.
- Read GitHub Issues, PRs, comments, and reviews with `gh`.
- Edit local documentation, skill metadata, references, handoff files, and other explicitly scoped repository files.
- Run local checks such as `git status`, `git diff`, `git diff --check`, and local tests.
- Commit and push to the current task branch when the user asks Codex to do so.
- Open or update the task PR when the user asks for a PR workflow.

## Actions Requiring Explicit User Confirmation

Require explicit confirmation in the current conversation before:

- Running `ssh lilin`.
- Running `sbatch`.
- Running server-side dry runs.
- Syncing local mirror changes back to `lilin`.
- Writing, deleting, overwriting, or moving files on `lilin`.
- Modifying prepared or completed real calculation tasks.
- Resubmitting failed jobs.
- Syncing the development repository into the formal installed skill directory.
- Committing raw reference bundles, PDFs, images, source trees, generated cache JSON, binaries, secrets, or machine-local config.

## GitHub CLI Preflight

Before reading PR/Issue comments, pushing branches, or opening PRs with GitHub CLI, confirm authentication.

PowerShell:

```powershell
gh auth status --hostname github.com
gh auth login --hostname github.com --web --git-protocol https
```

If `gh` is installed but not on PATH on Windows:

```powershell
& 'C:\Program Files\GitHub CLI\gh.exe' auth status --hostname github.com
```

Do not print tokens or credentials. If `gh auth status` prints a masked token, do not copy the token value into user-facing summaries.

## Handoff Sync Truth

Every handoff should state:

- Formal skill directory changed: yes/no.
- Local workflow mirror changed: yes/no.
- Server execution source changed: yes/no.
- `ssh lilin`: yes/no.
- `sbatch`: yes/no.
- Remote writes/deletes: yes/no.
- Real calculation tasks changed: yes/no.

If only local documentation changed, the server execution source is `no`.

## Submission Review Boundary

Before asking the user to submit real jobs, present:

- project path and POSCAR source
- generated task directories
- exact tasks to submit now
- optional tasks deferred
- whether `OPTCELL` was generated and checked
- VASP executable and submit template path
- estimated resource class or expected high-cost steps
- nonstandard assumptions and unresolved risks
- output from `python workflow.py submit <project_name> --dry-run`, if the user has confirmed server dry-run access

Only submit after the user explicitly agrees.
