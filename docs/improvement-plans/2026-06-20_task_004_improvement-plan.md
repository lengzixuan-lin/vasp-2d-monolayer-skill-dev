# Task 004 Improvement Plan

This plan converts the `task_003` reference-summary follow-up targets into concrete review items. It is planning only: no server access, scheduler submission, real calculation edits, or remote writes are required for this task.

## Priority Order

1. Verify VASPKIT optical task numbering for the actual installed server version.
2. Define `module_provenance.yaml` schema expectations.
3. Define finite-displacement phonon subtask manifest expectations.
4. Define scheduler config and submit-template configurability expectations.
5. Define result-summary method/source label expectations.

## 1. VASPKIT Optical Task Numbering

Current summary basis:

- `docs/reference-summaries/vaspkit-task-map.md` records local README evidence for `711` as linear optical spectra.
- Earlier planning references mention `710`, creating a numbering conflict.

Review risk:

- Hard-coding the wrong VASPKIT task number would produce incorrect or failed optical post-processing commands.

Required verification:

- Under explicit future approval for server inspection, check the installed VASPKIT version and optical menu on the target server.
- Record whether `710`, `711`, or another task number maps to the required optical spectrum conversion.
- Capture the command prompt sequence needed for non-interactive execution.

Expected artifact after verification:

- A small versioned note or config entry documenting:
  - VASPKIT version.
  - Verified task number.
  - Required input files.
  - Exact prompt sequence.
  - Output files consumed by summaries.

Acceptance criteria:

- No optical post-processing command is hard-coded until the server-installed VASPKIT task number is confirmed.
- Result summaries can distinguish raw VASP dielectric output from VASPKIT-converted optical spectra.

## 2. `module_provenance.yaml` Schema

Current summary basis:

- `docs/reference-summaries/result-extraction-patterns.md` requires extracted values to carry method label, source directory, source file, parent calculation, convergence/status result, and parser/post-processing tool.
- `docs/reference-summaries/README.md` flags parent directory, `CONTCAR`, `CHGCAR`, `WAVECAR`, runtime KPOINTS, executable, INCAR template, and post-processing source as schema targets.

Review risk:

- Downstream modules may silently reuse parent files or generated inputs without enough provenance for review.

Proposed schema topics:

- Module identity: module name, method level, calculation purpose, task ID.
- Parent inputs: parent directory, inherited `CONTCAR`, `CHGCAR`, `WAVECAR`, copied/generated `KPOINTS`, copied/generated `POTCAR`.
- Runtime inputs: INCAR template name, rendered INCAR path, KPOINTS source, executable, environment/module setup reference.
- Dependency status: parent completion status, convergence status, restart/overwrite state.
- Post-processing: parser/tool name, command source, source files, generated result files.

Acceptance criteria:

- Every module can explain which parent files were inherited and why.
- Every generated summary value can trace back to a calculation directory, source file, method label, and parser/post-processing tool.
- Restart or overwrite state is explicit rather than inferred.

## 3. Finite-Displacement Phonon Subtask Manifest

Current summary basis:

- `docs/reference-summaries/scheduler-submission-patterns.md` highlights separate subtask queues for parallel displacement jobs.
- `docs/reference-summaries/result-extraction-patterns.md` requires supercell dimension, displacement generation tool, force convergence, and `FORCE_SETS` provenance.

Review risk:

- A parent phonon task could be marked complete even if some displacement jobs failed, were skipped, or produced force files from inconsistent settings.

Proposed manifest topics:

- Parent phonon task ID and source relaxed structure.
- Supercell dimensions and displacement generation tool/version.
- List of displacement subtasks with subtask ID, directory, input POSCAR, expected force output, status, and scheduler job ID when applicable.
- Per-subtask convergence status and failure reason.
- `FORCE_SETS` generation source, timestamp, required displacement count, and included displacement count.
- Imaginary-mode follow-up status and reviewer notes.

Acceptance criteria:

- Parent phonon completion requires all required displacement subtasks to finish successfully.
- `FORCE_SETS` generation can be traced to exact displacement directories.
- Imaginary modes are labeled as diagnostic until q-point/eigenvector context and convergence checks are reviewed.

## 4. Scheduler Config and Submit Template Configurability

Current summary basis:

- `docs/reference-summaries/scheduler-submission-patterns.md` lists scheduler type, queue/partition, node/task counts, walltime, MPI launcher, VASP executable, SOC executable, environment setup, and concurrency limit as configurable.

Review risk:

- Hard-coded personal server values can make the workflow unsafe, non-portable, or misleading during review.

Proposed configurable fields:

- Scheduler type.
- Queue or partition.
- Nodes, tasks, CPUs per task, memory, and walltime.
- MPI launcher.
- Standard VASP executable.
- SOC/non-collinear executable.
- Environment/module setup lines.
- Output/error log pattern.
- Maximum concurrently submitted jobs.
- Optional notification settings.

Acceptance criteria:

- Submit template rendering can be reviewed before any submission.
- Machine-local values live in config rather than workflow logic.
- Unresolved scheduler or executable values block real submission.
- `ssh`, `sbatch`, server sync, and remote writes remain behind explicit current-window approval.

## 5. Result-Summary Method/Source Labels

Current summary basis:

- `docs/reference-summaries/result-extraction-patterns.md` lists label requirements for band gaps, CBM/VBM, Fermi level, DOS/PDOS, optics, vacuum/work function, phonons, effective mass, and mobility.

Review risk:

- Manuscript-facing summaries may mix PBE, HSE, SOC, raw VASP, VASPKIT-converted, and manually post-processed values without visible source boundaries.

Required labels:

- Method level: PBE, HSE, SOC, HSE+SOC, raw VASP, VASPKIT-converted, or other post-processed.
- Source directory and source files.
- Parent calculation.
- Parser or post-processing tool.
- Convergence/status result.
- Unit and transformation, including Fermi shift, vacuum reference, optical conversion, or fit range.

Acceptance criteria:

- Any result-summary table can be audited without opening the whole workflow tree.
- Failed or incomplete calculations are not summarized as final values unless explicitly labeled diagnostic.
- DOS/PDOS, optical spectra, work function, phonons, effective mass, and mobility each expose the source and method used to generate the reported value.

## Suggested Follow-Up Issue Split

- `task_005`: Verify VASPKIT optical task numbering and document server-version evidence after explicit server-inspection approval.
- `task_006`: Draft `module_provenance.yaml` schema and example records.
- `task_007`: Draft finite-displacement phonon subtask manifest schema and review checks.
- `task_008`: Review scheduler config and submit-template fields for configurability.
- `task_009`: Draft result-summary label schema and examples.

## Out of Scope for Task 004

- Editing real workflow implementation files.
- Running or preparing server-side dry runs.
- Executing `ssh`, `sbatch`, or scheduler commands.
- Modifying real calculation tasks.
- Syncing into the formal installed skill directory.
