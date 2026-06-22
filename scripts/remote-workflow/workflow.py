#!/usr/bin/env python3
"""
DFT Workflow — main orchestrator for 2D material automated calculations.

Usage:
  python workflow.py new <project_name> --poscar <path>
  python workflow.py prepare <project_name>
  python workflow.py submit <project_name>
  python workflow.py monitor <project_name>
  python workflow.py collect <project_name>
  python workflow.py report <project_name>
  python workflow.py status <project_name>
  python workflow.py resume <project_name>
"""

import os
import sys
import yaml
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from provenance_utils import path_record


TERMINAL_OK_STATES = {"completed", "completed_check"}
TERMINAL_BAD_STATES = {"failed", "cancelled", "timeout", "blocked"}
BATCH_A_RESULT_MODULES = {
    "01_opt": {
        "name": "opt",
        "normalized_module_label": "01_opt",
        "method_label": "pbe_geometry_optimization",
        "parent_calculation": "00_input",
    },
    "02_scf": {
        "name": "scf",
        "normalized_module_label": "02_scf",
        "method_label": "pbe_scf",
        "parent_calculation": "01_opt",
    },
    "03_pbeband": {
        "name": "band",
        "normalized_module_label": "03_band",
        "method_label": "pbe_band_structure",
        "parent_calculation": "02_scf",
    },
    "04_dos": {
        "name": "dos",
        "normalized_module_label": "04_dos",
        "method_label": "pbe_dos",
        "parent_calculation": "02_scf",
    },
}


def now_iso():
    return datetime.now().isoformat()


def new_module_status(module):
    return {
        "name": module["name"],
        "state": "pending",
        "job_id": None,
        "dependencies": module.get("dependencies", []),
        "module_dir": module["module_dir"],
        "updated_at": now_iso(),
    }


def update_module_status(status, mod_dir, **updates):
    status.setdefault("modules", {})
    entry = status["modules"].setdefault(mod_dir, {"state": "pending"})
    entry.update(updates)
    entry["updated_at"] = now_iso()
    return entry


def dependency_state(status, dep_dir):
    return status.get("modules", {}).get(dep_dir, {}).get("state")


def write_input_provenance(project, source_poscar, audit_path, audit):
    """Write provenance for 00_input after project seed files exist."""
    input_dir = os.path.join(project.project_dir, "00_input")
    copied_poscar = os.path.join(input_dir, "POSCAR")
    metadata_path = os.path.join(input_dir, "metadata.yaml")
    manifest_path = os.path.join(project.project_dir, "manifest.yaml")
    status_path = os.path.join(project.project_dir, "workflow_status.yaml")
    missing = [
        name for name, path in (
            ("copied_poscar", copied_poscar),
            ("metadata", metadata_path),
            ("structure_audit", audit_path),
            ("manifest", manifest_path),
            ("workflow_status", status_path),
        )
        if not os.path.exists(path)
    ]
    payload = {
        "schema_version": "2026-06-20.batch_a.v1",
        "project": project.name,
        "module_identity": {
            "name": "input",
            "actual_module_dir": "00_input",
            "normalized_module_label": "00_input",
            "method_label": "input_structure",
            "calculation_purpose": "Seed the workflow from a reviewed POSCAR.",
            "batch_a_baseline": True,
        },
        "created_at": now_iso(),
        "source_structure": {
            "source_poscar": path_record(
                source_poscar, role="original_user_supplied_poscar",
                required=True),
            "copied_poscar": path_record(
                copied_poscar, base_dir=project.project_dir,
                role="workflow_input_poscar", required=True),
        },
        "audit_records": {
            "metadata": path_record(
                metadata_path, base_dir=project.project_dir,
                role="project_metadata", required=True),
            "structure_audit": path_record(
                audit_path, base_dir=project.project_dir,
                role="structure_audit", required=True),
            "manifest": path_record(
                manifest_path, base_dir=project.project_dir,
                role="workflow_manifest", required=True),
            "workflow_status": path_record(
                status_path, base_dir=project.project_dir,
                role="workflow_status", required=True),
        },
        "structure_audit_status": {
            "warnings": audit.get("warnings", []) if audit else [],
            "status": "blocked" if missing else "pending_review",
        },
        "review_state": {
            "state": "blocked" if missing else "pending_review",
            "missing_required_records": missing,
            "final_result_status": "not_applicable_input_stage",
        },
    }
    out_path = os.path.join(input_dir, "module_provenance.yaml")
    with open(out_path, "w") as f:
        yaml.dump(payload, f, default_flow_style=False)
    return out_path


def inspect_vasp_run(work_dir, module_name):
    """Classify a finished/off-queue VASP directory without changing files."""
    if module_name == "mobility":
        summary = os.path.join(work_dir, "results", "mobility_summary.yaml")
        if os.path.exists(summary):
            try:
                with open(summary, "r", errors="ignore") as f:
                    payload = yaml.safe_load(f) or {}
                summary_status = payload.get("status", "check_required")
                success = summary_status == "complete"
            except Exception:
                summary_status = "unreadable"
                success = False
            return {
                "state": "completed" if success else "completed_check",
                "success": success,
                "finish": True,
                "details": f"mobility summary generated ({summary_status})",
            }
        manager_exit = os.path.join(work_dir, "mobility.exitcode")
        if os.path.exists(manager_exit):
            with open(manager_exit, "r", errors="ignore") as f:
                code = f.read().strip()
            if code and code != "0":
                return {
                    "state": "failed",
                    "success": False,
                    "finish": False,
                    "details": f"mobility manager exited with code {code}",
                }
    if module_name == "effective_mass":
        summary = os.path.join(work_dir, "results", "em_summary.yaml")
        if os.path.exists(summary):
            return {
                "state": "completed",
                "success": True,
                "finish": True,
                "details": "effective-mass summary generated",
            }
        manager_exit = os.path.join(work_dir, "effective_mass.exitcode")
        if os.path.exists(manager_exit):
            with open(manager_exit, "r", errors="ignore") as f:
                code = f.read().strip()
            if code and code != "0":
                return {
                    "state": "failed",
                    "success": False,
                    "finish": False,
                    "details": f"effective-mass manager exited with code {code}",
                }
    outcar = os.path.join(work_dir, "OUTCAR")
    if not os.path.exists(outcar):
        return {
            "state": "failed",
            "success": False,
            "finish": False,
            "details": "OUTCAR not found",
        }
    with open(outcar, "r", errors="ignore") as f:
        content = f.read()
    finished = "General timing and accounting" in content
    if not finished:
        return {
            "state": "failed",
            "success": False,
            "finish": False,
            "details": "OUTCAR exists but VASP did not reach normal timing footer",
        }
    if module_name in ("opt", "strain"):
        ionic_ok = "reached required accuracy" in content
        return {
            "state": "completed" if ionic_ok else "completed_check",
            "success": ionic_ok,
            "finish": True,
            "details": (
                "ionic convergence reached"
                if ionic_ok else
                "VASP finished but ionic convergence marker was not found"
            ),
        }
    return {
        "state": "completed",
        "success": True,
        "finish": True,
        "details": "VASP reached normal timing footer",
    }


def summarize_workflow_state(status):
    states = [
        item.get("state")
        for item in status.get("modules", {}).values()
    ]
    if not states:
        return status.get("state", "UNKNOWN")
    if any(s in TERMINAL_BAD_STATES for s in states):
        return "FAILED"
    if any(s == "completed_check" for s in states):
        return "CHECK_REQUIRED"
    if all(s == "completed" for s in states):
        return "COMPLETED"
    if any(s in ("submitted", "running", "pending") for s in states):
        return "RUNNING"
    return "PREPARED"


# ============================================================
# Project class — manages state for one calculation project
# ============================================================

class Project:
    """
    Represents one DFT calculation project (one material system).
    """

    def __init__(self, name, precision, material_type, config_dir, projects_dir):
        self.name = name
        self.precision = precision
        self.material_type = material_type
        self.project_dir = os.path.join(projects_dir, name)
        self.config_dir = config_dir

        # Load configs
        self.settings = self._load_yaml(
            os.path.join(config_dir, "settings.yaml"))
        self.precision_config = self._load_yaml(
            os.path.join(config_dir, f"precision_{precision}.yaml"))
        self.elements_db = self._load_yaml(
            os.path.join(config_dir, "elements.yaml"))

    def _load_yaml(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def init_project_dir(self, poscar_path):
        """Create project directory and copy POSCAR."""
        input_dir = os.path.join(self.project_dir, "00_input")
        os.makedirs(input_dir, exist_ok=True)

        # Copy POSCAR
        shutil.copy(poscar_path, os.path.join(input_dir, "POSCAR"))

        # Write project metadata
        from modules.base import (parse_poscar_elements,
                                  parse_poscar_atom_counts,
                                  parse_poscar_natoms)

        elements = parse_poscar_elements(
            os.path.join(input_dir, "POSCAR"))
        counts = parse_poscar_atom_counts(
            os.path.join(input_dir, "POSCAR"))
        natoms = parse_poscar_natoms(
            os.path.join(input_dir, "POSCAR"))

        meta = {
            "name": self.name,
            "precision": self.precision,
            "material_type": self.material_type,
            "created": datetime.now().isoformat(),
            "poscar_source": poscar_path,
            "elements": elements,
            "atom_counts": {el: c for el, c in zip(elements, counts)},
            "natoms": natoms,
        }
        with open(os.path.join(input_dir, "metadata.yaml"), 'w') as f:
            yaml.dump(meta, f)

    def load_manifest(self):
        """Load the workflow manifest (list of modules to run)."""
        path = os.path.join(self.project_dir, "manifest.yaml")
        if os.path.exists(path):
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        return None

    def save_manifest(self, manifest):
        """Save the workflow manifest."""
        path = os.path.join(self.project_dir, "manifest.yaml")
        with open(path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False)

    def load_status(self):
        """Load the workflow status."""
        path = os.path.join(self.project_dir, "workflow_status.yaml")
        if os.path.exists(path):
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def save_status(self, status):
        """Save the workflow status."""
        path = os.path.join(self.project_dir, "workflow_status.yaml")
        with open(path, 'w') as f:
            yaml.dump(status, f, default_flow_style=False)


# ============================================================
# Pipeline Builder — determines which modules to run
# ============================================================

class PipelineBuilder:
    """
    Build the calculation DAG based on precision and material type.
    Returns an ordered list of module specs with dependencies.
    """

    def __init__(self, project):
        self.project = project
        self.pc = project.precision_config

    def build(self):
        """Return ordered list of (module_name, module_dir, dependencies)."""
        mt = self.project.material_type
        modules = []

        modules.append(self._m("opt", "01_opt", []))
        modules.append(self._m("scf", "02_scf", ["01_opt"]))
        modules.append(self._m("band", "03_pbeband", ["02_scf"]))
        modules.append(self._m("dos", "04_dos", ["02_scf"]))
        modules.append(self._m("hse_scf", "05_hse_scf", ["02_scf"]))
        modules.append(self._m("hse_band", "05_hse_band", ["05_hse_scf"]))
        modules.append(self._m("vacuum", "07_vacuum", ["02_scf"]))
        modules.append(self._m("optical", "08_optical", ["02_scf"]))
        modules.append(self._m("phonopy_fd", "09_phonopy_fd", ["01_opt"]))
        modules.append(self._m("phonon_dfpt_check", "09_phonon_dfpt_check", ["01_opt"]))
        modules.append(self._m("aimd", "10_aimd", ["02_scf"]))
        modules.append(self._m("effective_mass", "11_effective_mass", ["02_scf", "03_pbeband"]))
        modules.append(self._m("mobility", "12_mobility", ["11_effective_mass"]))

        if mt == "heterojunction":
            modules.append(self._m("ccd", "13_ccd", ["02_scf"]))
            modules.append(self._m("bader", "14_bader", ["02_scf"]))
            modules.append(self._m("potential", "15_potential", ["02_scf"]))
            modules.append(self._m("strain", "16_strain", ["01_opt"]))
            modules.append(self._m("efield", "17_efield", ["02_scf"]))

        adsorption_cfg = self.pc.get("adsorption", {})
        if adsorption_cfg.get("enabled", False):
            modules.append(self._m("adsorption", "18_adsorption", ["02_scf"]))

        return modules

    def _m(self, name, mod_dir, deps):
        mcfg = self.pc.get(name, {})
        return {
            "name": name,
            "module_dir": mod_dir,
            "dependencies": deps,
            "enabled": mcfg.get("enabled", True),
        }


# ============================================================
# Module factory
# ============================================================

def create_module(module_name, project):
    """Dynamically import and instantiate a VaspModule subclass."""
    # Map module names to their INCAR templates
    template_map = {
        "opt": "incar/incar_opt.j2",
        "scf": "incar/incar_scf.j2",
        "band": "incar/incar_band.j2",
        "dos": "incar/incar_dos.j2",
        "hse": "incar/incar_hse_band.j2",  # backward-compatible alias
        "hse_scf": "incar/incar_hse_scf.j2",
        "hse_band": "incar/incar_hse_band.j2",
        "vacuum": "incar/incar_vacuum.j2",
        "optical": "incar/incar_optical.j2",
        "phonopy_fd": "incar/incar_phonopy_fd.j2",
        "phonon_dfpt_check": "incar/incar_phonopy.j2",
        "phonopy": "incar/incar_phonopy.j2",  # backward-compatible alias
        "aimd": "incar/incar_aimd.j2",
        "bader": "incar/incar_bader.j2",
        "ccd": "incar/incar_ccd.j2",
        "effective_mass": "incar/incar_em.j2",
        "mobility": "incar/incar_em.j2",
        "potential": "incar/incar_potential.j2",
        "strain": "incar/incar_opt.j2",   # strain uses opt-style then overrides
        "efield": "incar/incar_scf.j2",   # efield uses scf-style
    }

    from modules.base import VaspModule

    class DynamicModule(VaspModule):
        name = module_name
        incar_template = template_map.get(module_name)

    return DynamicModule(project, project.precision_config, project.settings)


# ============================================================
# Subcommand implementations
# ============================================================

def cmd_new(args):
    """Create a new project and print the calculation manifest."""
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
    projects_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects")

    # Material type: use --material-type override, or prompt user
    from modules.base import (write_structure_audit,
                              parse_poscar_elements,
                              parse_poscar_atom_counts,
                              parse_poscar_natoms,
                              estimate_vacuum_axis)

    if args.material_type:
        material_type = args.material_type
    else:
        # Print POSCAR audit summary
        print("=== POSCAR Audit ===")
        elements = parse_poscar_elements(args.poscar)
        counts = parse_poscar_atom_counts(args.poscar)
        natoms = parse_poscar_natoms(args.poscar)
        vacuum = estimate_vacuum_axis(args.poscar)
        print(f"  Elements:        {', '.join(elements)}")
        print(f"  Atom counts:     {dict(zip(elements, counts))}")
        print(f"  Total atoms:     {natoms}")
        print(f"  Vacuum axis:     {vacuum['axis_name']}")
        print(f"  Vacuum gaps (A): a={vacuum['vacuum_gaps'][0]:.2f}, "
              f"b={vacuum['vacuum_gaps'][1]:.2f}, c={vacuum['vacuum_gaps'][2]:.2f}")
        print()

        # Prompt for material type
        try:
            choice = input(
                "Select material type:\n"
                "  1 = monolayer\n"
                "  2 = heterojunction\n"
                "> ").strip()
        except (EOFError, OSError):
            print(
                "ERROR: stdin is not available for interactive material-type "
                "selection.\n"
                "Please re-run with --material-type monolayer|heterojunction "
                "for noninteractive use.",
                file=sys.stderr)
            sys.exit(2)

        type_map = {"1": "monolayer", "2": "heterojunction"}
        material_type = type_map.get(choice)
        if material_type is None:
            print(f"ERROR: invalid choice '{choice}'. Expected 1 or 2.",
                  file=sys.stderr)
            sys.exit(2)

    precision = args.precision

    project = Project(args.project_name, precision, material_type,
                      config_dir, projects_dir)

    print(f"\n=== Creating project '{args.project_name}' ===")
    print(f"  Material type: {material_type}")
    print(f"  Precision:     {precision}")
    print(f"  POSCAR:        {args.poscar}")

    # Init project
    project.init_project_dir(args.poscar)

    # Write structure audit
    audit_path = os.path.join(project.project_dir, "00_input",
                              "structure_audit.yaml")
    audit = write_structure_audit(args.poscar, audit_path)
    print(f"\n  Structure audit written to: {audit_path}")
    if audit["warnings"]:
        print(f"  Warnings:")
        for w in audit["warnings"]:
            print(f"    - {w}")

    # Build pipeline
    builder = PipelineBuilder(project)
    modules = builder.build()

    # Print manifest
    print(f"\n=== Calculation Manifest ({len(modules)} modules) ===\n")
    enabled_count = 0
    for i, m in enumerate(modules):
        status = "ENABLED" if m["enabled"] else "SKIPPED"
        deps = " -> ".join(m["dependencies"]) if m["dependencies"] else "none"
        if m["enabled"]:
            enabled_count += 1
        print(f"  [{status}] {m['module_dir']} ({m['name']}) depends: [{deps}]")

    # Save manifest
    project.save_manifest(modules)

    # Save initial status
    status = {
        "state": "CREATED",
        "precision": precision,
        "material_type": material_type,
        "created_at": now_iso(),
        "modules": {
            m["module_dir"]: new_module_status(m)
            for m in modules if m["enabled"]
        },
    }
    status["input_provenance_file"] = os.path.join(
        project.project_dir, "00_input", "module_provenance.yaml")
    project.save_status(status)
    write_input_provenance(project, args.poscar, audit_path, audit)

    print(f"\n  Total enabled: {enabled_count}/{len(modules)}")
    print(f"  Project saved to: {project.project_dir}")
    print(f"\n  Next steps:")
    print(f"    python workflow.py prepare {args.project_name}")
    print(f"    python workflow.py submit {args.project_name}")


def _setup_project_from_disk(project_name):
    """Create a Project instance with settings loaded from saved metadata."""
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
    projects_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects")

    # Read saved metadata
    meta_path = os.path.join(projects_dir, project_name, "00_input", "metadata.yaml")
    status_path = os.path.join(projects_dir, project_name, "workflow_status.yaml")

    precision = "standard"
    material_type = "monolayer"
    if os.path.exists(meta_path):
        with open(meta_path, 'r') as f:
            meta = yaml.safe_load(f)
        precision = meta.get("precision", "standard")
        material_type = meta.get("material_type", "monolayer")
    elif os.path.exists(status_path):
        with open(status_path, 'r') as f:
            status = yaml.safe_load(f)
        precision = status.get("precision", "standard")
        material_type = status.get("material_type", "monolayer")

    project = Project(project_name, precision, material_type, config_dir, projects_dir)
    return project


def validate_optcell_for_2d(work_dir, module_dir):
    """Validate that 2D optimization keeps the POSCAR c-axis fixed."""
    from modules.base import estimate_vacuum_axis

    optcell_path = os.path.join(work_dir, "OPTCELL")
    if not os.path.exists(optcell_path):
        raise RuntimeError(f"{module_dir} is not ready; missing OPTCELL.")
    with open(optcell_path, "r") as f:
        optcell_lines = [
            line.strip().replace(" ", "")
            for line in f
            if line.strip()
        ]
    if optcell_lines[:3] != ["110", "110", "000"]:
        raise RuntimeError(
            f"{module_dir} OPTCELL must fix the c-axis as 110/110/000; "
            f"found {'/'.join(optcell_lines[:3]) or 'empty'}."
        )
    vacuum = estimate_vacuum_axis(os.path.join(work_dir, "POSCAR"))
    if vacuum["axis_name"] != "c":
        gaps = ", ".join(
            f"{axis}={gap:.2f} A"
            for axis, gap in zip(("a", "b", "c"), vacuum["vacuum_gaps"])
        )
        raise RuntimeError(
            f"{module_dir} POSCAR vacuum appears to be along "
            f"{vacuum['axis_name']}, not c ({gaps}). Check the POSCAR or "
            "choose a matching OPTCELL before submitting."
        )


def cmd_prepare(args):
    """Prepare all module input files (INCAR, KPOINTS, POTCAR)."""
    project = _setup_project_from_disk(args.project_name)
    if getattr(args, "phonopy_stage", None):
        project.precision_config.setdefault("phonopy_fd", {})["stage"] = (
            args.phonopy_stage
        )
    manifest = project.load_manifest()
    if manifest is None:
        print(f"Error: project '{args.project_name}' not found. Run 'new' first.")
        return

    for m in manifest:
        if not m["enabled"]:
            continue
        cfg = project.precision_config.get(m["name"], {})
        if m["name"] == "optical":
            if not cfg.get("allow_2d_loptics", False):
                raise RuntimeError(
                    "The optical module is disabled for automatic 2D "
                    "production runs because LOPTICS needs explicit "
                    "low-dimensional post-processing. Set "
                    "optical.allow_2d_loptics=true only after documenting "
                    "the post-processing plan."
                )
            if cfg.get("postprocess") != "vaspkit_710":
                raise RuntimeError(
                    "The optical module requires optical.postprocess="
                    "vaspkit_710 for 2D optical data conversion."
                )
        if m["name"] in ("effective_mass", "mobility"):
            if not cfg.get("workflow_ready", False):
                if m["name"] == "effective_mass":
                    detail = (
                        "It requires band-edge confirmation, runtime local "
                        "k-line generation, and curvature-fit post-processing "
                        "before the results are scientifically reliable. "
                    )
                else:
                    detail = (
                        "It requires deformation-potential strain calculations "
                        "and reviewed effective-mass inputs before the results "
                        "are scientifically reliable. "
                    )
                print(
                    f"  [WARN] {m['name']} is enabled but workflow_ready=false. "
                    f"{detail}"
                    "Set workflow_ready=true only after those steps are implemented and reviewed."
                )

    print(f"=== Preparing input files for '{args.project_name}' ===\n")

    # Order matters: prepare in dependency order
    prepared = []
    status = project.load_status() or {}
    status.setdefault("modules", {})
    for m in manifest:
        if not m["enabled"]:
            continue
        mod = create_module(m["name"], project)
        mod.module_dir = m["module_dir"]

        # Find dependency directory for copying inputs
        dep_dir = None
        if m["dependencies"]:
            # Use the first dependency's work dir
            dep_name = m["dependencies"][0]
            for mm in manifest:
                if mm["module_dir"] == dep_name:
                    dep_dir = os.path.join(project.project_dir, dep_name)
                    break

        mod.setup_dir(copy_inputs_from=dep_dir)
        if m["name"] == "opt":
            validate_optcell_for_2d(mod.work_dir, m["module_dir"])
        provenance_path = os.path.join(mod.work_dir, "module_provenance.yaml")
        provenance = {}
        if os.path.exists(provenance_path):
            with open(provenance_path, "r") as f:
                provenance = yaml.safe_load(f) or {}
        update_module_status(
            status,
            m["module_dir"],
            name=m["name"],
            module_dir=m["module_dir"],
            dependencies=m["dependencies"],
            state="prepared",
            job_id=None,
            parent_dir=dep_dir,
            provenance_file=provenance_path,
            inheritance=provenance.get("inheritance", {}),
        )
        prepared.append(m["module_dir"])
        print(f"  [OK] {m['module_dir']} ({m['name']}) — INCAR, KPOINTS written")

    status["state"] = "PREPARED"
    status["prepared_at"] = now_iso()
    project.save_status(status)

    print(f"\n  Prepared {len(prepared)} modules.")
    print(f"  Next: python workflow.py submit {args.project_name}")


def cmd_submit(args):
    """Submit prepared modules to Slurm after an explicit review gate."""
    project = _setup_project_from_disk(args.project_name)
    manifest = project.load_manifest()
    if manifest is None:
        print(f"Error: project '{args.project_name}' not found.")
        return

    enabled = [m for m in manifest if m["enabled"]]
    print(f"=== Submission review for '{args.project_name}' ===\n")
    for m in enabled:
        deps = ", ".join(m["dependencies"]) if m["dependencies"] else "none"
        print(f"  {m['module_dir']:12s} {m['name']:16s} deps=[{deps}]")
    if args.dry_run:
        print("\n  Dry run: validate inputs and show sbatch commands only.")
    else:
        print("\n  This will submit Slurm jobs and consume compute resources.")
    if not args.yes:
        if not args.dry_run:
            answer = input("  Type SUBMIT to continue: ").strip()
            if answer != "SUBMIT":
                print("  Submission cancelled.")
                return

    action = "Validating submission" if args.dry_run else "Submitting jobs"
    print(f"\n=== {action} for '{args.project_name}' ===\n")

    import subprocess
    import re
    status = project.load_status() or {}
    status.setdefault("modules", {})
    job_map = {}  # module_dir -> slurm_job_id

    for m in enabled:
        mod_dir = m["module_dir"]
        work_dir = os.path.join(project.project_dir, mod_dir)
        mod_status = status.get("modules", {}).get(mod_dir, {})
        if mod_status.get("state") in TERMINAL_OK_STATES:
            print(f"  {mod_dir}: SKIP already {mod_status.get('state')}")
            continue

        missing = [
            fn for fn in ("INCAR", "KPOINTS", "POTCAR", "POSCAR", "sub.vasp")
            if not os.path.exists(os.path.join(work_dir, fn))
        ]
        if m["name"] == "opt":
            optcell_path = os.path.join(work_dir, "OPTCELL")
            if not os.path.exists(optcell_path):
                missing.append("OPTCELL")
        if missing:
            raise RuntimeError(
                f"{mod_dir} is not ready; missing {', '.join(missing)}. "
                "Run prepare and fix input generation before submitting."
            )
        if m["name"] == "opt":
            validate_optcell_for_2d(work_dir, mod_dir)

        deps = m["dependencies"]
        dep_str = ""
        if deps:
            dep_jobs = [job_map[d] for d in deps if d in job_map]
            unresolved_deps = []
            for d in deps:
                if d in job_map:
                    continue
                d_state = dependency_state(status, d)
                if d_state not in TERMINAL_OK_STATES:
                    unresolved_deps.append(f"{d}({d_state or 'unknown'})")
            if unresolved_deps:
                raise RuntimeError(
                    f"Cannot submit {mod_dir}; dependency jobs missing: "
                    f"{', '.join(unresolved_deps)}"
                )
            if dep_jobs:
                dep_str = "--dependency=afterok:" + ":".join(dep_jobs)

        cmd = f"sbatch {dep_str} sub.vasp"
        if args.dry_run:
            print(f"  {mod_dir}: DRY-RUN {cmd}")
            job_map[mod_dir] = f"DRYRUN_{mod_dir}"
            continue
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True, text=True, cwd=work_dir)
        output = result.stdout.strip()
        error = result.stderr.strip()
        print(f"  {mod_dir}: {output}")
        if result.returncode != 0:
            raise RuntimeError(f"sbatch failed for {mod_dir}: {error or output}")

        match = re.search(r"Submitted batch job (\d+)", output)
        if not match:
            raise RuntimeError(f"Could not parse Slurm job id for {mod_dir}: {output}")
        job_map[mod_dir] = match.group(1)
        update_module_status(
            status,
            mod_dir,
            name=m["name"],
            state="submitted",
            job_id=job_map[mod_dir],
            submitted_at=now_iso(),
        )

    if args.dry_run:
        print(f"\n  Dry run passed for {len(job_map)} jobs. No Slurm jobs submitted.")
        return

    status["state"] = "RUNNING"
    status["submitted_at"] = now_iso()
    project.save_status(status)

    print(f"\n  Submitted {len(job_map)} jobs.")
    print(f"  Next: python workflow.py monitor {args.project_name}")


def cmd_monitor(args):
    """Monitor submitted jobs until completion."""
    project = _setup_project_from_disk(args.project_name)
    status = project.load_status()
    if not status:
        print(f"Error: project '{args.project_name}' not found.")
        return

    import time
    from submit.slurm import SlurmManager

    modules = status.get("modules", {})
    manifest = project.load_manifest() or []
    module_names = {m["module_dir"]: m["name"] for m in manifest}
    slurm = SlurmManager(project.settings)
    print(f"=== Monitoring '{args.project_name}' ===\n")

    pending = {k: v for k, v in modules.items() if v.get("job_id")}
    while pending:
        for mod_dir, info in list(pending.items()):
            job_id = info.get("job_id")
            state_info = slurm.status(job_id)
            output_state = state_info.get("state", "UNKNOWN")
            output = f"JobState={output_state}"
            work_dir = os.path.join(project.project_dir, mod_dir)
            module_name = info.get("name") or module_names.get(mod_dir, "")

            if "JobState=COMPLETED" in output:
                print(f"  [OK] {mod_dir} ({job_id}) — COMPLETED")
                run_state = inspect_vasp_run(work_dir, module_name)
                info.update(run_state)
                info["completed_at"] = now_iso()
                del pending[mod_dir]
            elif "JobState=FAILED" in output or "JobState=TIMEOUT" in output:
                print(f"  [FAIL] {mod_dir} ({job_id}) — {output.split('JobState=')[-1].split()[0] if 'JobState=' in output else 'UNKNOWN'}")
                info["state"] = "failed"
                info["slurm_state"] = output_state
                info["diagnosis"] = slurm.diagnose(work_dir)
                info["failed_at"] = now_iso()
                del pending[mod_dir]
            elif "NOT_FOUND" in output:
                run_state = inspect_vasp_run(work_dir, module_name)
                info.update(run_state)
                if not run_state["success"]:
                    info["diagnosis"] = slurm.diagnose(work_dir)
                del pending[mod_dir]
                continue

        if pending:
            project.save_status(status)
            time.sleep(60)  # Check every minute

    status["state"] = summarize_workflow_state(status)
    project.save_status(status)
    print(f"\n  Monitoring complete.")
    print(f"  Next: python workflow.py collect {args.project_name}")


def cmd_status(args):
    """Print current workflow status."""
    project = _setup_project_from_disk(args.project_name)
    status = project.load_status()
    if not status:
        print(f"Error: project '{args.project_name}' not found.")
        return

    print(f"=== Status: {args.project_name} ===")
    print(f"  State:        {status.get('state', 'UNKNOWN')}")
    print(f"  Precision:    {status.get('precision', '?')}")
    print(f"  Material:     {status.get('material_type', '?')}")
    print(f"  Created:      {status.get('created_at', '?')}")
    print()

    modules = status.get("modules", {})
    if modules:
        for mod_dir, info in modules.items():
            state = info.get("state", "?")
            job_id = info.get("job_id", "-")
            print(f"  [{state:12s}] {mod_dir}  job={job_id}")
            diagnosis = info.get("diagnosis")
            if diagnosis:
                print(f"      diagnosis: {diagnosis.get('error_type')} - {diagnosis.get('details')}")
                actions = diagnosis.get("actions") or []
                if actions:
                    print(f"      actions: {'; '.join(actions)}")
    else:
        print("  No modules found. Run 'new' first.")


def cmd_diagnose(args):
    """Diagnose failed or incomplete modules without modifying inputs."""
    project = _setup_project_from_disk(args.project_name)
    status = project.load_status()
    if not status:
        print(f"Error: project '{args.project_name}' not found.")
        return

    from submit.slurm import SlurmManager

    slurm = SlurmManager(project.settings)
    manifest = project.load_manifest() or []
    module_names = {m["module_dir"]: m["name"] for m in manifest}
    targets = [args.module_dir] if args.module_dir else list(status.get("modules", {}))

    print(f"=== Diagnosing '{args.project_name}' ===\n")
    for mod_dir in targets:
        work_dir = os.path.join(project.project_dir, mod_dir)
        module_name = module_names.get(mod_dir, "")
        run_state = inspect_vasp_run(work_dir, module_name)
        diag = slurm.diagnose(work_dir)
        update_module_status(
            status,
            mod_dir,
            state=run_state["state"],
            success=run_state["success"],
            finish=run_state["finish"],
            details=run_state["details"],
            diagnosis=diag,
        )
        print(f"  {mod_dir}: {run_state['state']} - {run_state['details']}")
        print(f"    diagnosis: {diag.get('error_type')} - {diag.get('details')}")
        for action in diag.get("actions", []):
            print(f"    action: {action}")

    status["state"] = summarize_workflow_state(status)
    project.save_status(status)


def _result_status_from_evidence(workflow_state, evidence_exists, finished):
    if workflow_state in TERMINAL_BAD_STATES:
        return "blocked"
    if not evidence_exists:
        return "blocked" if workflow_state == "completed" else "pending_review"
    if not finished:
        return "diagnostic"
    if workflow_state != "completed":
        return "pending_review"
    return "final"


def _outcar_finished(outcar_path):
    if not os.path.exists(outcar_path):
        return False
    with open(outcar_path, "r", errors="ignore") as f:
        return "General timing and accounting" in f.read()


def _transformation_record(label, details=None):
    return {
        "label": label,
        "details": details,
    }


def _parser_or_tool_record(name, command_or_source, version="workflow-local"):
    return {
        "name": name,
        "version": version,
        "command_or_source": command_or_source,
    }


def _result_entry(name, value, unit, method_label, source_module,
                  source_dir, source_files, parent_calculation,
                  parser_or_tool, transformation, convergence_status,
                  result_status):
    if isinstance(transformation, str):
        transformation = _transformation_record(transformation)
    return {
        "value_name": name,
        "value": value,
        "unit": unit,
        "method_label": method_label,
        "source_module": source_module,
        "source_directory": source_dir,
        "source_files": source_files,
        "parent_calculation": parent_calculation,
        "parser_or_tool": parser_or_tool,
        "convergence_status": convergence_status,
        "transformation": transformation,
        "uncertainty_or_fit_quality": {
            "type": "not_applicable",
            "value": None,
            "notes": None,
        },
        "result_status": result_status,
        "review_notes": [],
    }


def build_baseline_result_labels(project, mod_dir, info, parser=None):
    """Build Batch A result labels from existing local output evidence."""
    module_meta = BATCH_A_RESULT_MODULES[mod_dir]
    work_dir = os.path.join(project.project_dir, mod_dir)
    outcar = os.path.join(work_dir, "OUTCAR")
    band_gap_file = os.path.join(work_dir, "BAND_GAP")
    doscar = os.path.join(work_dir, "DOSCAR")
    workflow_state = info.get("state", "unknown")
    outcar_exists = os.path.exists(outcar)
    outcar_finished = _outcar_finished(outcar)
    parser_meta = _parser_or_tool_record(
        "OutcarParser" if parser else "not_available",
        "scripts/remote-workflow/collect/outcar_parser.py")
    convergence_status = {
        "electronic": "unknown",
        "ionic": (
            "converged"
            if parser and parser.has_converged()
            else "not_confirmed"
        ),
        "task_status": (
            "finished"
            if outcar_finished
            else ("missing_evidence" if not outcar_exists else "not_finished")
        ),
    }
    source_files = {
        "OUTCAR": path_record(
            outcar, base_dir=project.project_dir,
            role="vasp_output", required=True),
        "BAND_GAP": path_record(
            band_gap_file, base_dir=project.project_dir,
            role="vaspkit_band_gap_output",
            required=module_meta["name"] == "band"),
        "DOSCAR": path_record(
            doscar, base_dir=project.project_dir,
            role="dos_output", required=module_meta["name"] == "dos"),
    }
    result_status = _result_status_from_evidence(
        workflow_state, outcar_exists, outcar_finished)
    labels = {
        "schema_version": "2026-06-20.batch_a.v1",
        "generated_at": now_iso(),
        "module_identity": {
            "name": module_meta["name"],
            "actual_module_dir": mod_dir,
            "normalized_module_label": module_meta["normalized_module_label"],
            "method_label": module_meta["method_label"],
            "batch_a_baseline": True,
        },
        "collection_context": {
            "workflow_state": workflow_state,
            "job_id": info.get("job_id"),
            "source_directory": work_dir,
        },
        "source_files": source_files,
        "parser": parser_meta,
        "convergence_status": {
            "outcar_exists": outcar_exists,
            "outcar_normal_finish": outcar_finished,
            "ionic_converged": parser.has_converged() if parser else None,
            "n_ionic_steps": parser.get_n_ionic_steps() if parser else None,
        },
        "results": [],
        "review_state": {
            "state": "pending_review" if result_status == "final" else result_status,
            "reason": "collector_evidence_based_labels",
        },
    }
    method = module_meta["method_label"]
    source_module = module_meta["normalized_module_label"]
    parent_calculation = module_meta["parent_calculation"]

    if parser:
        total_energy = parser.get_total_energy()
        if total_energy is not None:
            energy_status = result_status
            if module_meta["name"] == "opt" and not parser.has_converged():
                energy_status = "diagnostic"
            labels["results"].append(_result_entry(
                "total_energy", total_energy, "eV", method, source_module,
                work_dir, ["OUTCAR"], parent_calculation, parser_meta,
                "none", convergence_status, energy_status))
        fermi = parser.get_fermi_level()
        if fermi is not None:
            fermi_status = (
                result_status if module_meta["name"] in ("scf", "dos")
                else "diagnostic"
            )
            labels["results"].append(_result_entry(
                "fermi_level", fermi, "eV", method, source_module,
                work_dir, ["OUTCAR"], parent_calculation, parser_meta,
                "none", convergence_status, fermi_status))
        max_force = parser.get_max_force()
        if module_meta["name"] == "opt" and max_force is not None:
            force_status = result_status if parser.has_converged() else "diagnostic"
            labels["results"].append(_result_entry(
                "max_force", max_force, "eV/A", method, source_module,
                work_dir, ["OUTCAR"], parent_calculation, parser_meta,
                "none", convergence_status, force_status))

    if module_meta["name"] == "band":
        band_parser = _parser_or_tool_record("VASPKIT 211 output", "BAND_GAP")
        if os.path.exists(band_gap_file):
            with open(band_gap_file, "r", errors="ignore") as f:
                band_gap_text = f.read().strip()
            labels["results"].append(_result_entry(
                "band_gap", band_gap_text, "eV", method, source_module,
                work_dir, ["BAND_GAP"], parent_calculation, band_parser,
                "band_gap_extraction", convergence_status, result_status))
        else:
            labels["results"].append(_result_entry(
                "band_gap", None, "eV", method, source_module,
                work_dir, ["BAND_GAP"], parent_calculation, band_parser,
                "band_gap_extraction", convergence_status, "diagnostic"))

    if module_meta["name"] == "dos":
        dos_status = "pending_review" if os.path.exists(doscar) else "diagnostic"
        labels["results"].append(_result_entry(
            "dos_output", "present" if os.path.exists(doscar) else None,
            None, method, source_module, work_dir, ["DOSCAR"],
            parent_calculation,
            _parser_or_tool_record(
                "not_implemented",
                "DOSCAR parser not implemented in Batch A"),
            "dos_postprocessing_pending", convergence_status, dos_status))

    if not labels["results"]:
        labels["results"].append(_result_entry(
            "module_collection_status", workflow_state, None, method,
            source_module, work_dir, [], parent_calculation, parser_meta,
            "none", convergence_status, result_status))

    return labels


def write_baseline_result_labels(project, mod_dir, info, parser=None):
    labels = build_baseline_result_labels(project, mod_dir, info, parser)
    path = os.path.join(project.project_dir, mod_dir, "result_labels.yaml")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(labels, f, default_flow_style=False)
    return path


def cmd_collect(args):
    """Collect results from all completed modules."""
    project = _setup_project_from_disk(args.project_name)
    status = project.load_status()
    if not status:
        print(f"Error: project '{args.project_name}' not found.")
        return

    from collect.outcar_parser import OutcarParser

    print(f"=== Collecting results for '{args.project_name}' ===\n")
    results = {}
    modules = status.get("modules", {})

    for mod_dir, info in modules.items():
        work_dir = os.path.join(project.project_dir, mod_dir)
        outcar = os.path.join(work_dir, "OUTCAR")
        parser = None
        if os.path.exists(outcar):
            try:
                parser = OutcarParser(outcar)
            except Exception as exc:
                print(f"  [{mod_dir}] OUTCAR parser unavailable: {exc}")

        if mod_dir in BATCH_A_RESULT_MODULES:
            label_path = write_baseline_result_labels(
                project, mod_dir, info, parser=parser)
            update_module_status(
                status, mod_dir, result_labels_file=label_path)

        if info.get("state") != "completed":
            continue

        print(f"  [{mod_dir}]")
        if parser:
            energy = parser.get_total_energy()
            if energy is not None:
                results.setdefault(mod_dir, {})["energy_eV"] = energy
                print(f"    Energy: {energy} eV")
            if parser.has_converged():
                print(f"    Convergence: OK")

        band_gap_file = os.path.join(work_dir, "BAND_GAP")
        if os.path.exists(band_gap_file):
            with open(band_gap_file, "r", errors="ignore") as f:
                gap_text = f.read().strip()
            print(f"    Band gap: {gap_text}")
            results.setdefault(mod_dir, {})["band_gap"] = gap_text

    # Save results
    results_path = os.path.join(project.project_dir, "results.yaml")
    with open(results_path, 'w') as f:
        yaml.dump(results, f, default_flow_style=False)
    project.save_status(status)

    print(f"\n  Results saved to: {results_path}")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="DFT Workflow for 2D Materials",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python workflow.py new mos2 --poscar POSCAR
  python workflow.py prepare mos2
  python workflow.py submit mos2 --dry-run
  python workflow.py submit mos2
  python workflow.py monitor mos2
  python workflow.py collect mos2
  python workflow.py status mos2
        """)

    subparsers = parser.add_subparsers(dest="command")

    # new
    p_new = subparsers.add_parser("new", help="Create new project")
    p_new.add_argument("project_name")
    p_new.add_argument("--poscar", required=True)
    p_new.add_argument("--material-type", choices=["monolayer", "heterojunction"],
                       help="Material type (noninteractive override)")
    p_new.add_argument("--precision", choices=["standard", "quick"],
                       default="standard",
                       help="Precision level (default: standard)")

    # prepare
    p_prep = subparsers.add_parser("prepare", help="Prepare input files")
    p_prep.add_argument("project_name")
    p_prep.add_argument("--phonopy-stage", choices=["debug", "production"],
                        help="Override phonopy_fd stage for this prepare run")

    # submit
    p_sub = subparsers.add_parser("submit", help="Submit jobs to Slurm")
    p_sub.add_argument("project_name")
    p_sub.add_argument("--yes", action="store_true",
                       help="Submit without interactive confirmation")
    p_sub.add_argument("--dry-run", action="store_true",
                       help="Validate inputs and print sbatch commands without submitting")

    # monitor
    p_mon = subparsers.add_parser("monitor", help="Monitor job status")
    p_mon.add_argument("project_name")

    # collect
    p_col = subparsers.add_parser("collect", help="Collect results")
    p_col.add_argument("project_name")

    # status
    p_stat = subparsers.add_parser("status", help="Show project status")
    p_stat.add_argument("project_name")

    # diagnose
    p_diag = subparsers.add_parser("diagnose", help="Diagnose failed modules")
    p_diag.add_argument("project_name")
    p_diag.add_argument("--module-dir", help="Diagnose one module directory")

    # resume
    p_res = subparsers.add_parser("resume", help="Resume unfinished modules")
    p_res.add_argument("project_name")
    p_res.add_argument("--yes", action="store_true",
                       help="Submit without interactive confirmation")
    p_res.add_argument("--dry-run", action="store_true",
                       help="Validate inputs and print sbatch commands without submitting")

    # report
    p_rep = subparsers.add_parser("report", help="Generate report")
    p_rep.add_argument("project_name")

    args = parser.parse_args()

    if args.command == "new":
        cmd_new(args)
    elif args.command == "prepare":
        cmd_prepare(args)
    elif args.command == "submit":
        cmd_submit(args)
    elif args.command == "monitor":
        cmd_monitor(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "collect":
        cmd_collect(args)
    elif args.command == "diagnose":
        cmd_diagnose(args)
    elif args.command == "resume":
        cmd_submit(args)
    elif args.command == "report":
        print("Report generation not yet implemented.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
