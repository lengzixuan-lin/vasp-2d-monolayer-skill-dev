# Scheduler and Submission Patterns

Primary sources:

- `vasp_references资料/JAMIP/JAMIP-V1.0.1.Manual-Chs.pdf-b1938462-d000-4f32-804a-ffd5d1b44a05/JAMIP.md`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/compute/cluster.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/compute/launch.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/compute/manager.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/compute/pool.py`
- `vasp_references资料/JAMIP/jamip-1.0.2/jamip/compute/queues.py`

Excluded raw sources:

- JAMIP source tree and generated/manual artifacts.

## Scheduler Abstraction

JAMIP abstracts PBS, LSF, and SLURM behind a cluster configuration object. The scheduler type controls script headers, queue command, node/core directives, output/error files, environment setup, and submission command.

Useful pattern:

- Scheduler-specific syntax should live in configuration/templates.
- Workflow logic should not hard-code a single scheduler's command or resource directives.
- Environment setup should be data-driven, visible, and reviewable.

For `vasp-2d-monolayer`, this supports keeping `sub.vasp` and scheduler parameters in templates/config rather than scattered logic.

## Job Script Structure

JAMIP-generated scripts contain:

- shell header
- scheduler job name
- queue/partition
- node/core/task settings
- walltime/time when configured
- error and output log paths
- working-directory setup
- optional environment lines
- final Python manager command

Review implications:

- Every generated `sub.vasp` should expose job name, partition/queue, resources, logs, working directory, environment, and VASP executable.
- Personal or machine-local values should be configurable.
- The final command should be visible before submission.

## Task Pool and Status Model

JAMIP stores a pool of tasks with fields such as status, priority, job id, and functional/task object. Submission loops choose waiting jobs by priority and update them to running after scheduler submission. Queue managers can count user jobs and throttle new submissions.

Useful pattern:

- Maintain explicit task states: wait/running/finish/error-like states.
- Record job IDs as soon as submission succeeds.
- Throttle submissions with a maximum count.
- Avoid resubmitting tasks whose status already indicates success unless restart/overwrite is explicitly requested.

For `vasp-2d-monolayer`, this maps well to `workflow_status.yaml` and supports resume behavior.

## Dependency and Continuation Checks

JAMIP uses status files and completed parent directories to continue from the most advanced valid stage. It also removes or resets status when restart/overwrite is requested.

Review implications:

- Resume should read status first and explain what will be skipped or submitted.
- Restart/overwrite should be explicit and visible in review output.
- Any deletion of status or parent files is a high-risk action requiring user confirmation.

## Subtask Patterns

For parallel subtasks such as phonon displacements, JAMIP writes a separate subtask queue and submits multiple worker scripts. Each worker updates shared status with file locking.

Review implications:

- Phonon finite-displacement workflows need a subtask manifest.
- Shared status writes should be robust against concurrent updates.
- A parent phonon task should only be marked complete after all required displacement jobs finish successfully.

## Safety Checks Before Real Submission

Task_003 is documentation only, but these design patterns suggest future submission checks:

- Validate required files exist before scheduler submission.
- Render and display the final submit script before `sbatch`.
- Run dry-run validation only after the user confirms server dry-run access.
- Do not submit if dependencies are missing, parent status is failed, or resource settings are unresolved.
- Keep `ssh`, `sbatch`, server sync, and remote writes behind explicit current-conversation confirmation.

## Configurable Rather Than Hard-Coded

The following should stay configurable:

- scheduler type
- queue/partition
- node and task counts
- walltime/time limit
- MPI launcher
- VASP executable
- SOC/non-collinear executable
- environment/module setup
- maximum concurrently submitted jobs
- notification settings

Hard-coded personal email addresses, paths, executables, and queue names should be avoided unless the user explicitly chooses them for the current server.
