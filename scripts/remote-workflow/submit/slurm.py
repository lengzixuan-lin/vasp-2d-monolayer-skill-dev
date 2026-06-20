#!/usr/bin/env python3
"""
SlurmManager — handles job submission, status tracking, and failure diagnosis.
"""

import os
import re
import time
import subprocess
import yaml
from datetime import datetime


class SlurmManager:
    """Manage Slurm job submission and monitoring."""

    def __init__(self, settings):
        slurm = settings.get("slurm", {})
        self.partition = slurm.get("partition", "cpus")
        self.ntasks = slurm.get("ntasks", 16)
        self.max_retries = settings.get("max_retries", 0)
        self.monitor_interval = settings.get("monitor_interval_sec", 60)
        # SSH command prefix for remote execution
        # If running on-server, ssh_cmd is empty
        self.ssh_cmd = []  # Empty = run locally

    def _run(self, cmd, work_dir=None):
        """Execute a command locally or on remote server."""
        if work_dir:
            cmd = f"cd {work_dir} && {cmd}"
        if self.ssh_cmd:
            full_cmd = self.ssh_cmd + [cmd]
        else:
            full_cmd = ["bash", "-c", cmd]

        result = subprocess.run(full_cmd, capture_output=True, text=True,
                                timeout=300)
        return result.stdout.strip(), result.stderr.strip()

    def submit(self, work_dir, job_name, dependency=None):
        """
        Submit a VASP job to Slurm.

        Args:
            work_dir: Path to working directory with sub.vasp
            job_name: Slurm job name
            dependency: Optional job ID for --dependency=afterok

        Returns:
            Slurm job ID (str), or None on failure
        """
        dep_flag = ""
        if dependency:
            dep_flag = f"--dependency=afterok:{dependency}"

        sub_script = os.path.join(work_dir, "sub.vasp")
        if not os.path.exists(sub_script):
            raise FileNotFoundError(f"Submit script not found: {sub_script}")

        cmd = f"sbatch {dep_flag} --job-name={job_name} sub.vasp"
        stdout, stderr = self._run(cmd, work_dir)

        if stderr and "Submitted batch job" not in stdout:
            print(f"  [ERROR] sbatch failed: {stderr}")
            return None

        match = re.search(r"Submitted batch job (\d+)", stdout)
        if match:
            return match.group(1)
        return None

    def status(self, job_id):
        """
        Query a job's status via scontrol.

        Returns dict with keys: state, exit_code, work_dir, elapsed
        """
        stdout, _ = self._run(
            f"scontrol show job {job_id} --oneline 2>/dev/null")

        if not stdout:
            return {"state": "NOT_FOUND"}

        info = {"state": "UNKNOWN", "exit_code": None}
        if "JobState=" in stdout:
            info["state"] = stdout.split("JobState=")[1].split()[0]
        if "ExitCode=" in stdout:
            info["exit_code"] = stdout.split("ExitCode=")[1].split()[0]
        if "WorkDir=" in stdout:
            info["work_dir"] = stdout.split("WorkDir=")[1].split()[0]
        if "RunTime=" in stdout:
            info["elapsed"] = stdout.split("RunTime=")[1].split()[0]

        return info

    def status_all(self, job_ids):
        """Check status of multiple jobs using squeue+scontrol."""
        stdout, _ = self._run(
            f"squeue -j {','.join(job_ids)} -h -o '%i %T' 2>/dev/null")
        results = {}
        for jid in job_ids:
            results[jid] = {"state": "COMPLETED"}  # default if not in queue

        for line in stdout.split("\n"):
            if not line.strip():
                continue
            parts = line.strip().split()
            if len(parts) >= 2:
                results[parts[0]] = {"state": parts[1]}

        return results

    def _latest_log_text(self, work_dir, limit=3):
        """Read recent Slurm/output logs for diagnosis, if present."""
        if not os.path.isdir(work_dir):
            return ""
        names = [
            f for f in os.listdir(work_dir)
            if f.startswith("output_") or f.endswith(".out") or f.endswith(".err")
        ]
        names = sorted(
            names,
            key=lambda x: os.path.getmtime(os.path.join(work_dir, x)),
            reverse=True,
        )[:limit]
        chunks = []
        for name in names:
            path = os.path.join(work_dir, name)
            try:
                with open(path, "r", errors="ignore") as f:
                    chunks.append(f.read()[-20000:])
            except OSError:
                pass
        return "\n".join(chunks)

    def _match_error_signature(self, text):
        """Return a diagnosis from known VASP/log signatures."""
        low = text.lower()
        signatures = [
            {
                "error_type": "WAVECAR_INCOMPATIBLE",
                "patterns": ["while reading wavecar", "plane wave coefficients changed"],
                "details": "WAVECAR is incompatible with the current KPOINTS/NBANDS/method",
                "actions": [
                    "Remove WAVECAR and rerun with ISTART=0",
                    "Do not reuse WAVECAR after KPOINTS, NBANDS, SOC, or HSE changes",
                ],
                "retriable": True,
            },
            {
                "error_type": "CHGCAR_MISSING",
                "patterns": ["chgcar", "icharg=11"],
                "mode": "all",
                "details": "A charge-density restart was requested but CHGCAR is missing or unreadable",
                "actions": [
                    "Verify the parent SCF/HSE-SCF finished and wrote CHGCAR",
                    "Rerun the parent task before submitting this dependent module",
                ],
                "retriable": False,
            },
            {
                "error_type": "SCF_DIVERGENCE",
                "patterns": ["zbrent", "brmix", "edddav"],
                "details": "Electronic SCF appears unstable or divergent",
                "actions": [
                    "Try ALGO=Normal, reduce AMIX, and increase NELM",
                    "For difficult semiconductors, consider a staged SCF from a safer smearing",
                ],
                "retriable": True,
            },
            {
                "error_type": "INSUFFICIENT_BANDS",
                "patterns": ["nbands", "too few bands"],
                "details": "The calculation likely needs more bands",
                "actions": [
                    "Increase NBANDS, especially for LOPTICS/HSE optical calculations",
                ],
                "retriable": True,
            },
            {
                "error_type": "KPOINTS_OR_SYMMETRY",
                "patterns": ["internal error in subroutine ibzkpt", "tetrahedron method fails"],
                "details": "KPOINTS or symmetry settings are inconsistent",
                "actions": [
                    "Regenerate KPOINTS and consider ISYM=0 for SOC/HSE/problematic cells",
                    "Check that the 2D vacuum axis and line-mode KPOINTS are correct",
                ],
                "retriable": True,
            },
            {
                "error_type": "MEMORY_LIMIT",
                "patterns": ["oom-kill", "out of memory", "cannot allocate memory"],
                "details": "Job exceeded available memory",
                "actions": [
                    "Increase memory/resources or reduce parallel pressure",
                    "For HSE/optical/phonon, reduce task size or split the job",
                ],
                "retriable": True,
            },
            {
                "error_type": "WALLTIME_EXCEEDED",
                "patterns": ["time limit", "due to time limit"],
                "details": "Job exceeded walltime",
                "actions": [
                    "Resubmit only after confirming restart files are compatible",
                    "Use ISTART=1 only when WAVECAR compatibility is guaranteed",
                ],
                "retriable": True,
            },
        ]
        for item in signatures:
            patterns = item["patterns"]
            if item.get("mode") == "all":
                matched = all(pattern in low for pattern in patterns)
            else:
                matched = any(pattern in low for pattern in patterns)
            if matched:
                return {
                    "error_type": item["error_type"],
                    "details": item["details"],
                    "actions": item["actions"],
                    "retriable": item["retriable"],
                }
        return None

    def diagnose(self, work_dir):
        """
        Diagnose a failed VASP job by inspecting output files.

        Returns:
            dict with: error_type, details, suggested_actions, retriable (bool)
        """
        issues = []
        outcar = os.path.join(work_dir, "OUTCAR")

        # Check if OUTCAR exists
        if not os.path.exists(outcar):
            # Check slurm output
            log_text = self._latest_log_text(work_dir)
            signature = self._match_error_signature(log_text)
            if signature:
                return signature
            log_files = sorted(
                [f for f in os.listdir(work_dir) if f.startswith("output_")],
                key=lambda x: os.path.getmtime(os.path.join(work_dir, x)),
                reverse=True)
            if log_files:
                with open(os.path.join(work_dir, log_files[0]),
                          'r', errors='ignore') as f:
                    log = f.read()
                if "oom-kill" in log.lower() or "out of memory" in log.lower():
                    return {
                        "error_type": "OOM",
                        "details": "Out of memory",
                        "actions": ["Reduce NCORE or increase memory request"],
                        "retriable": True,
                    }
            return {
                "error_type": "NO_OUTCAR",
                "details": "OUTCAR not found, job likely crashed early",
                "actions": ["Check output_*.log for error messages"],
                "retriable": False,
            }

        with open(outcar, 'r', errors='ignore') as f:
            content = f.read()
        signature = self._match_error_signature(
            content + "\n" + self._latest_log_text(work_dir)
        )
        if signature:
            return signature

        # SCF divergence
        if "ZBRENT" in content and "NELM" in content:
            issues.append({
                "type": "SCF_NOT_CONVERGED",
                "detail": "Electronic SCF did not converge",
            })

        # Ions not converged
        if ("reached required accuracy" not in content and
                "General timing and accounting" in content):
            # Completed but without ionic convergence
            force_lines = []
            for line in content.split("\n"):
                if "TOTAL-FORCE" in line:
                    force_lines.append(line)

        # Walltime exceeded
        if "time limit" in content.lower():
            issues.append({
                "type": "WALLTIME_EXCEEDED",
                "detail": "Job ran out of walltime",
            })

        # Build diagnosis
        if not issues:
            if "General timing and accounting" in content:
                return {
                    "error_type": "COMPLETED_NO_CONVERGENCE",
                    "details": "Job completed but ionic convergence not reached",
                    "actions": ["Check forces at final step",
                                "Increase NSW or switch IBRION"],
                    "retriable": True,
                }
            return {
                "error_type": "UNKNOWN",
                "details": "Job did not finish normally",
                "actions": ["Check OUTCAR tail for clues"],
                "retriable": False,
            }

        # Map issue types to strategies
        strategies = {
            "SCF_NOT_CONVERGED": {
                "actions": [
                    "Reduce AMIX to 0.1",
                    "Switch ALGO to Normal (ALGO=Normal)",
                    "Increase NELM to 200",
                ],
                "retriable": True,
            },
            "WALLTIME_EXCEEDED": {
                "actions": [
                    "Resubmit with ISTART=1 to continue from WAVECAR",
                ],
                "retriable": True,
            },
        }

        primary = issues[0]
        strategy = strategies.get(
            primary["type"],
            {"actions": ["Manual inspection needed"], "retriable": False})

        return {
            "error_type": primary["type"],
            "details": primary["detail"],
            "actions": strategy["actions"],
            "retriable": strategy["retriable"],
        }

    def resubmit(self, work_dir, job_name, dependency=None,
                 modify_incar=None):
        """
        Resubmit a failed job with optional INCAR modifications.

        Args:
            work_dir: Working directory
            job_name: Slurm job name
            dependency: Optional job ID dependency
            modify_incar: dict of {tag: value} to append/modify in INCAR
        """
        if modify_incar:
            incar_path = os.path.join(work_dir, "INCAR")
            if os.path.exists(incar_path):
                with open(incar_path, 'r') as f:
                    content = f.read()
                for tag, value in modify_incar.items():
                    # Update existing or append
                    pattern = rf'^(\s*{tag}\s*=\s*).*$'
                    if re.search(pattern, content, re.MULTILINE):
                        content = re.sub(pattern,
                                         rf'\1{value}', content,
                                         flags=re.MULTILINE)
                    else:
                        content += f"\n{tag} = {value}\n"
                with open(incar_path, 'w') as f:
                    f.write(content)

                # Also set ISTART=1 to continue from WAVECAR
                if "ISTART" not in modify_incar:
                    content += "\nISTART = 1\n"
                    with open(incar_path, 'w') as f:
                        f.write(content)

        return self.submit(work_dir, f"{job_name}_retry", dependency)


class WorkflowMonitor:
    """
    Monitor a batch of Slurm jobs with callbacks.
    Supports automatic retry on failure.
    """

    def __init__(self, slurm_manager, project_dir, status_file):
        self.slurm = slurm_manager
        self.project_dir = project_dir
        self.status_file = status_file
        self.retry_counts = {}

    def load_status(self):
        if os.path.exists(self.status_file):
            with open(self.status_file, 'r') as f:
                return yaml.safe_load(f)
        return {"modules": {}}

    def save_status(self, status):
        with open(self.status_file, 'w') as f:
            yaml.dump(status, f, default_flow_style=False)

    def monitor(self, module_jobs, callback=None):
        """
        Monitor jobs until all complete or fail.

        Args:
            module_jobs: {module_dir: {"job_id": str, "name": str}}
            callback: function(module_dir, event, data) called on events

        Returns:
            dict of final results per module
        """
        status = self.load_status()
        pending = dict(module_jobs)
        results = {}

        print(f"Monitoring {len(pending)} jobs...")
        print(f"{'Module':20s} {'Job ID':10s} {'State':15s}")
        print("-" * 50)

        while pending:
            for mod_dir, info in list(pending.items()):
                job_id = info["job_id"]
                state = self.slurm.status(job_id)

                if state["state"] in ("COMPLETED",):
                    # Verify OUTCAR exists
                    work_dir = info.get("work_dir",
                                        os.path.join(self.project_dir, mod_dir))
                    outcar = os.path.join(work_dir, "OUTCAR")
                    if os.path.exists(outcar):
                        conv = self._check_convergence(outcar)
                        status_msg = "CONVERGED" if conv else "COMPLETED"
                        results[mod_dir] = {"state": status_msg, "job_id": job_id}
                        print(f"{mod_dir:20s} {job_id:10s} {status_msg:15s}")
                    else:
                        results[mod_dir] = {"state": "NO_OUTCAR", "job_id": job_id}
                        print(f"{mod_dir:20s} {job_id:10s} {'NO_OUTCAR':15s}")

                    if callback:
                        callback(mod_dir, "completed", results[mod_dir])
                    del pending[mod_dir]

                elif state["state"] in ("FAILED", "TIMEOUT", "CANCELLED",
                                        "DEADLINE", "OUT_OF_MEMORY"):
                    work_dir = info.get("work_dir",
                                        os.path.join(self.project_dir, mod_dir))
                    diag = self.slurm.diagnose(work_dir)
                    print(f"{mod_dir:20s} {job_id:10s} {state['state']:15s} "
                          f"— {diag['error_type']}")

                    # Auto-retry if applicable
                    retry_key = mod_dir
                    self.retry_counts[retry_key] = (
                        self.retry_counts.get(retry_key, 0) + 1)
                    max_retries = self.slurm.max_retries

                    if (diag["retriable"] and
                            self.retry_counts[retry_key] <= max_retries):
                        print(f"  [AUTO-RETRY] attempt "
                              f"{self.retry_counts[retry_key]}/{max_retries}")
                        new_job_id = self.slurm.resubmit(
                            work_dir, info["name"])
                        if new_job_id:
                            info["job_id"] = new_job_id
                        else:
                            del pending[mod_dir]
                            results[mod_dir] = {
                                "state": "RETRY_FAILED", "job_id": job_id}
                    else:
                        results[mod_dir] = {
                            "state": "FAILED", "job_id": job_id}
                        if callback:
                            callback(mod_dir, "failed", results[mod_dir])
                        del pending[mod_dir]

                elif state["state"] == "NOT_FOUND":
                    # Job might have finished and been cleaned from queue
                    work_dir = info.get("work_dir",
                                        os.path.join(self.project_dir, mod_dir))
                    outcar = os.path.join(work_dir, "OUTCAR")
                    if os.path.exists(outcar):
                        conv = self._check_convergence(outcar)
                        status_msg = "CONVERGED" if conv else "COMPLETED"
                        results[mod_dir] = {"state": status_msg,
                                            "job_id": job_id}
                        print(f"{mod_dir:20s} {job_id:10s} "
                              f"{status_msg:15s} (off-queue)")
                    else:
                        results[mod_dir] = {"state": "NOT_FOUND",
                                            "job_id": job_id}
                        print(f"{mod_dir:20s} {job_id:10s} "
                              f"{'NOT_FOUND':15s}")
                    del pending[mod_dir]

                else:
                    # Still running/queued
                    pass

            if pending:
                time.sleep(self.slurm.monitor_interval)

        # Save final status
        status["modules"] = results
        status["completed_at"] = datetime.now().isoformat()
        self.save_status(status)

        return results

    def _check_convergence(self, outcar_path):
        """Check if OUTCAR shows convergence."""
        with open(outcar_path, 'r', errors='ignore') as f:
            return "reached required accuracy" in f.read()
