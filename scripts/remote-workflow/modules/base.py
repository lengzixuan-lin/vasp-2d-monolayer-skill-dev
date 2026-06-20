#!/usr/bin/env python3
"""
VaspModule — base class for all DFT calculation modules.
Handles POSCAR parsing, INCAR rendering, KPOINTS/POTCAR generation,
submission script creation, and basic output parsing.
"""

import os
import re
import yaml
import math
import shutil
import subprocess
import numpy as np
from datetime import datetime
from pathlib import Path
from provenance_utils import path_record
try:
    from jinja2 import Environment, FileSystemLoader
    _HAS_JINJA2 = True
except ImportError:
    _HAS_JINJA2 = False


# ============================================================
# Utility functions
# ============================================================

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def parse_poscar_elements(poscar_path):
    """Parse POSCAR to extract element symbols."""
    with open(poscar_path, 'r') as f:
        lines = f.readlines()
    element_line = lines[5].strip()
    return element_line.split()


def parse_poscar_atom_counts(poscar_path):
    """Parse POSCAR to extract number of atoms per element."""
    with open(poscar_path, 'r') as f:
        lines = f.readlines()
    counts_line = lines[6].strip()
    return [int(x) for x in counts_line.split()]


def parse_poscar_natoms(poscar_path):
    """Get total number of atoms from POSCAR."""
    return sum(parse_poscar_atom_counts(poscar_path))


def parse_poscar_lattice_vectors(poscar_path):
    """Parse POSCAR lattice vectors in Angstrom."""
    with open(poscar_path, 'r') as f:
        lines = f.readlines()
    scale = float(lines[1].split()[0])
    vectors = np.array([
        [float(x) for x in lines[i].split()[:3]]
        for i in range(2, 5)
    ])
    if scale > 0:
        vectors *= scale
    return vectors


def parse_poscar_fractional_coordinates(poscar_path):
    """Parse POSCAR coordinates and return fractional coordinates."""
    with open(poscar_path, 'r') as f:
        lines = f.readlines()
    natoms = parse_poscar_natoms(poscar_path)
    coord_start = 8
    if lines[7].strip().lower().startswith("s"):
        coord_start = 9
    coord_mode = lines[coord_start - 1].strip().lower()
    coords = np.array([
        [float(x) for x in lines[coord_start + i].split()[:3]]
        for i in range(natoms)
    ])
    if coord_mode.startswith("d"):
        return coords % 1.0
    lattice = parse_poscar_lattice_vectors(poscar_path)
    frac = np.linalg.solve(lattice.T, coords.T).T
    return frac % 1.0


def estimate_vacuum_axis(poscar_path):
    """
    Estimate vacuum direction from the largest empty fractional gap.
    Returns a dict with axis index/name, lattice lengths, and vacuum gaps.
    """
    lattice = parse_poscar_lattice_vectors(poscar_path)
    frac = parse_poscar_fractional_coordinates(poscar_path)
    lengths = np.linalg.norm(lattice, axis=1)
    gaps = []
    for axis in range(3):
        values = np.sort(frac[:, axis] % 1.0)
        if len(values) == 1:
            max_gap = 1.0
        else:
            diffs = np.diff(values)
            wrap_gap = values[0] + 1.0 - values[-1]
            max_gap = max(float(np.max(diffs)), float(wrap_gap))
        gaps.append(max_gap * lengths[axis])
    vacuum_axis = int(np.argmax(gaps))
    return {
        "axis": vacuum_axis,
        "axis_name": ("a", "b", "c")[vacuum_axis],
        "lengths": [float(x) for x in lengths],
        "vacuum_gaps": [float(x) for x in gaps],
    }


def detect_material_type(poscar_path):
    """
    Detect if POSCAR represents a monolayer or heterojunction.
    Heuristic: >=4 unique elements -> heterojunction.
    """
    elements = parse_poscar_elements(poscar_path)
    if len(elements) >= 4:
        return "heterojunction"
    return "monolayer"


def parse_poscar_selective_dynamics(poscar_path):
    """Check if POSCAR uses selective dynamics."""
    with open(poscar_path, 'r') as f:
        lines = f.readlines()
    if len(lines) >= 8:
        return lines[7].strip().lower().startswith("s")
    return False


def parse_poscar_coord_mode(poscar_path):
    """Return coordinate mode: 'Direct' or 'Cartesian'."""
    with open(poscar_path, 'r') as f:
        lines = f.readlines()
    selective = parse_poscar_selective_dynamics(poscar_path)
    coord_line_index = 8 if selective else 7
    if coord_line_index < len(lines):
        line = lines[coord_line_index].strip().lower()
        if line.startswith("d"):
            return "Direct"
        elif line.startswith("c") or line.startswith("k"):
            return "Cartesian"
    return "Unknown"


def estimate_min_interatomic_distance(poscar_path):
    """Estimate the minimum interatomic distance (Angstrom) from POSCAR."""
    lattice = parse_poscar_lattice_vectors(poscar_path)
    frac = parse_poscar_fractional_coordinates(poscar_path)
    cart = frac @ lattice
    natoms = len(cart)
    min_dist = float('inf')
    for i in range(natoms):
        for j in range(i + 1, natoms):
            delta = cart[i] - cart[j]
            dist = float(np.linalg.norm(delta))
            if dist < min_dist:
                min_dist = dist
    if min_dist == float('inf'):
        return 0.0
    return round(min_dist, 4)


def write_structure_audit(poscar_path, output_path):
    """Write a structure_audit.yaml for the given POSCAR."""
    elements = parse_poscar_elements(poscar_path)
    counts = parse_poscar_atom_counts(poscar_path)
    natoms = parse_poscar_natoms(poscar_path)
    selective = parse_poscar_selective_dynamics(poscar_path)
    coord_mode = parse_poscar_coord_mode(poscar_path)
    vacuum = estimate_vacuum_axis(poscar_path)
    min_dist = estimate_min_interatomic_distance(poscar_path)

    warnings = []
    if vacuum["axis_name"] != "c":
        warnings.append(
            f"Vacuum axis is '{vacuum['axis_name']}', not 'c'. "
            "OPTCELL must be adjusted or POSCAR reoriented before optimization."
        )
    if min_dist < 0.5:
        warnings.append(
            f"Minimum interatomic distance {min_dist:.2f} A is very small; "
            "check POSCAR for overlapping atoms."
        )

    audit = {
        "poscar_source": poscar_path,
        "elements": {el: c for el, c in zip(elements, counts)},
        "total_atoms": natoms,
        "selective_dynamics": selective,
        "coordinate_mode": coord_mode,
        "lattice_vector_lengths": [round(v, 4) for v in vacuum["lengths"]],
        "vacuum_axis": vacuum["axis_name"],
        "vacuum_gaps": {
            ax: round(g, 4)
            for ax, g in zip(("a", "b", "c"), vacuum["vacuum_gaps"])
        },
        "min_interatomic_distance": min_dist,
        "warnings": warnings,
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(audit, f, default_flow_style=False)
    return audit


# ---- KPOINTS validation ----

def validate_kpoints_2d_regular(kpoints_path, tol=1e-4):
    """Validate a regular-mesh KPOINTS file has Nkz=1 for 2D."""
    if not os.path.exists(kpoints_path):
        return {"passed": False, "errors": ["KPOINTS file not found"]}
    with open(kpoints_path, 'r') as f:
        lines = f.readlines()
    # Attempt to parse mesh line: usually the 4th line in a regular-mesh KPOINTS
    errors = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('!'):
            continue
        parts = stripped.split()
        if len(parts) == 3:
            try:
                vals = [int(float(p)) for p in parts]
            except ValueError:
                continue
            if all(v > 0 for v in vals):
                if vals[2] != 1:
                    errors.append(
                        f"Regular mesh Nkz={vals[2]}, expected 1 for 2D "
                        f"(mesh: {vals[0]}x{vals[1]}x{vals[2]})")
                return {
                    "passed": len(errors) == 0,
                    "mesh": vals,
                    "errors": errors,
                }
    return {"passed": False, "errors": ["Could not parse regular KPOINTS mesh"]}


def validate_kpoints_2d_line_mode(kpoints_path, tol=1e-4):
    """Validate line-mode k-points all have kz=0 within tolerance."""
    if not os.path.exists(kpoints_path):
        return {"passed": False, "errors": ["KPOINTS file not found"]}
    with open(kpoints_path, 'r') as f:
        content = f.read()
    lines = content.strip().split('\n')
    errors = []
    kz_violations = 0
    in_coords = False
    # Line-mode KPOINTS: header lines, then k-point coordinates
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('!'):
            continue
        parts = stripped.split()
        # Look for coordinate lines (3 or 4 values per line)
        if len(parts) >= 3:
            try:
                kz = float(parts[2])
            except ValueError:
                continue
            if abs(kz) > tol:
                kz_violations += 1
                if kz_violations <= 3:
                    errors.append(
                        f"k-point with kz={kz:.6f} exceeds tolerance {tol}")
    if kz_violations > 3:
        errors.append(f"... and {kz_violations - 3} more kz violations")
    return {
        "passed": len(errors) == 0,
        "kz_violations": kz_violations,
        "errors": errors,
    }


def write_kpoints_summary(module_name, kpoints_path, output_path,
                          kpoints_mode=None):
    """Write a kpoints_summary.yaml for a prepared module.
    Runtime placeholders (band/hse_band) are recorded as requiring runtime
    validation, not as passed.
    """
    summary = {
        "module": module_name,
        "file_checked": kpoints_path,
        "mode": kpoints_mode or "unknown",
        "checked_at": datetime.now().isoformat(),
    }
    if not os.path.exists(kpoints_path):
        summary["passed"] = False
        summary["errors"] = ["KPOINTS file not found"]
    else:
        with open(kpoints_path, 'r') as f:
            header = f.read(500)
        # Detect runtime placeholder first
        is_placeholder = (
            "placeholder" in header.lower()
            or "sub.vasp will run" in header
            or "generated at job runtime" in header
        )
        if is_placeholder:
            summary["mode"] = "runtime_placeholder"
            summary["passed"] = None  # unknown until runtime
            summary["errors"] = []
            summary["warning"] = (
                "KPOINTS is a review placeholder; the real KPOINTS/KPATH "
                "is generated at job runtime by VASPKIT. Final 2D validation "
                "happens via the kpoints_2d_runtime_guard in sub.vasp."
            )
        else:
            if "line-mode" in header.lower():
                result = validate_kpoints_2d_line_mode(kpoints_path)
                summary["mode"] = "line_mode"
            else:
                result = validate_kpoints_2d_regular(kpoints_path)
                summary["mode"] = "regular"
            summary["passed"] = result["passed"]
            summary["errors"] = result.get("errors", [])
            if "mesh" in result:
                summary["mesh"] = result["mesh"]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(summary, f, default_flow_style=False)
    return summary


def kpoints_2d_runtime_guard():
    """Return a bash snippet that checks kz=0 for 2D before VASP starts.
    Uses command exit status instead of shell variables set inside awk.
    """
    return (
        "# 2D k-point guard: verify kz=0 for all k-points before VASP\n"
        "# Line-mode check: all kz must be 0\n"
        "if grep -qi 'line-mode' KPOINTS 2>/dev/null; then\n"
        "  if ! awk 'NF>=3 && $1+0==$1 && $3+0!=0"
        " {print \"ERROR: kz=\"$3\" != 0\"; e=1; exit 1}"
        " END {if(e) exit 1; else exit 0}' KPOINTS\n"
        "  then echo 'FATAL: 2D line-mode KPOINTS has non-zero kz'; exit 8; fi\n"
        "fi\n"
        "# Regular mesh check: Nkz must be 1\n"
        "if ! awk 'NF==3 && $1+0>0 && $2+0>0"
        " {if($3+0!=1) {print \"ERROR: Nkz=\"$3\" != 1\"; e=1}}"
        " END {if(e) exit 1; else exit 0}' KPOINTS\n"
        "then echo 'FATAL: 2D regular KPOINTS Nkz != 1'; exit 9; fi\n"
    )


# ============================================================
# Jinja2 environment
# ============================================================

_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "templates")
if _HAS_JINJA2:
    _JINJA_ENV = Environment(loader=FileSystemLoader(_TEMPLATE_DIR))
else:
    _JINJA_ENV = None


def render_template(template_name, **kwargs):
    """Render a Jinja2 template with given variables."""
    if not _HAS_JINJA2:
        raise RuntimeError(
            "render_template() requires Jinja2, which is not installed. "
            "Install it with: pip install jinja2"
        )
    template = _JINJA_ENV.get_template(template_name)
    return template.render(**kwargs)


# ============================================================
# VaspModule base class
# ============================================================

class VaspModule:
    """
    Base class for all VASP calculation modules.

    Subclasses define:
      - name: str (e.g. 'opt', 'scf', 'hse')
      - module_dir: str (e.g. '01_opt')
      - incar_template: str, Jinja2 template filename
      - required_inputs: list[str], files needed from previous modules
    """

    name = "base"
    module_dir = "00_base"
    incar_template = None
    required_inputs = []

    def __init__(self, project, precision_config, settings):
        self.project = project
        self.precision_config = precision_config
        self.settings = settings
        self.global_params = precision_config.get("global", {})
        self.module_params = precision_config.get(self.name, {})
        self._enabled = self.module_params.get("enabled", True)

    @property
    def enabled(self):
        return self._enabled

    @property
    def work_dir(self):
        return os.path.join(self.project.project_dir, self.module_dir)

    # ---- Element helpers ----

    @property
    def elements(self):
        if not hasattr(self, '_elements'):
            poscar = os.path.join(self.project.project_dir, "00_input", "POSCAR")
            self._elements = parse_poscar_elements(poscar)
        return self._elements

    @property
    def natoms(self):
        if not hasattr(self, '_natoms'):
            poscar = os.path.join(self.project.project_dir, "00_input", "POSCAR")
            self._natoms = parse_poscar_natoms(poscar)
        return self._natoms

    def calc_encut(self, factor=None):
        """Calculate ENCUT from the actual generated POTCAR when available."""
        if factor is None:
            factor = self.module_params.get(
                "encut_factor",
                self.global_params.get("encut_factor", 1.5))
        enmaxs = self.get_potcar_enmaxs()
        if enmaxs:
            max_enmax = max(enmaxs)
        else:
            elements_db = self.project.elements_db
            max_enmax = max(
                elements_db.get(el, {}).get("enmax", 400)
                for el in self.elements
            )
        encut = int(max_enmax * factor)
        min_encut = self.global_params.get("encut_min", 0)
        return max(encut, min_encut)

    def get_potcar_enmaxs(self):
        """Read real ENMAX values from the POTCAR selected by VASPKIT."""
        candidates = [
            os.path.join(self.work_dir, "POTCAR"),
        ]
        if self.name != "opt":
            candidates.append(self.optimization_potcar_path())
        for potcar_path in candidates:
            if not os.path.exists(potcar_path):
                continue
            with open(potcar_path, 'r', errors='ignore') as f:
                content = f.read()
            enmaxs = [
                float(x)
                for x in re.findall(r'ENMAX\s*=\s*([\d.]+)', content)
            ]
            if enmaxs:
                return enmaxs
        return []

    def calc_valence_electrons(self):
        """Calculate total valence electrons from POSCAR."""
        elements_db = self.project.elements_db
        poscar = os.path.join(self.project.project_dir, "00_input", "POSCAR")
        counts = parse_poscar_atom_counts(poscar)
        total = 0
        for el, count in zip(self.elements, counts):
            zval = elements_db.get(el, {}).get("zval", 0)
            total += zval * count
        return total

    def calc_nbands_optical(self):
        """Calculate NBANDS for optical: 2 * total valence electrons."""
        nelect = self.calc_valence_electrons()
        return int(2 * nelect)

    # ---- KPOINTS ----

    def get_kspacing(self):
        """Get KSPACING value for INCAR (VASP auto-generates k-mesh)."""
        material_type = self.project.material_type
        kpt_cfg = self.precision_config.get("kpoints", {})
        if material_type == "heterojunction":
            return kpt_cfg.get("heterojunction_density", 0.03)
        else:
            return kpt_cfg.get("monolayer_density", 0.03)

    # ---- INCAR ----

    def get_incar_vars(self):
        """Build variable dict for INCAR Jinja2 template rendering.
        Module-level params override global params (m[key] > g[key]).
        """
        g = self.global_params
        m = self.module_params
        if self.name == "phonopy_fd":
            stage = m.get("stage", "production")
            m = {**m, **m.get(stage, {})}
        return {
            "system_name": f"{self.project.name}_{self.name}",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "precision": self.project.precision,
            "kspacing": self.get_kspacing(),
            "encut": self.calc_encut(),
            "ncore": g.get("ncore", 8),
            "ivdw": g.get("ivdw", 11),
            "lreal": g.get("lreal", ".FALSE."),
            "addgrid": g.get("addgrid", ".TRUE."),
            "ispin": g.get("ispin", 1),
            "ismear": m.get("ismear", g.get("ismear", 0)),
            "sigma": m.get("sigma", g.get("sigma", 0.1)),
            "nelm": m.get("nelm", g.get("nelm", 90)),
            "nelmin": m.get("nelmin", g.get("nelmin", 6)),
            "ediff": m.get("ediff", g.get("ediff", 1E-06)),
            "nsw": m.get("nsw", 100),
            "ibrion": m.get("ibrion", 2),
            "isif": m.get("isif", 3),
            "ediffg": m.get("ediffg", g.get("ediffg", -0.01)),
            "lwave": m.get("lwave", g.get("lwave", ".FALSE.")),
            "lcharg": m.get("lcharg", g.get("lcharg", ".FALSE.")),
            "lorbit": m.get("lorbit", 11),
            "nedos": m.get("nedos", 3000),
            # HSE
            "aexx": m.get("aexx", 0.25),
            "hfscreen": m.get("hfscreen", 0.2),
            "algo": m.get("algo", "Damped"),
            "time": m.get("time", 0.4),
            "precfock": m.get("precfock", "Normal"),
            # SOC
            "lsorbit": m.get("lsorbit", ".TRUE."),
            "lmaxmix": m.get("lmaxmix", 4),
            # Optical
            "nbands_optical": self.calc_nbands_optical(),
            "cshift": m.get("cshift", 0.1),
            # Phonopy
            "prec": m.get("prec", "Accurate"),
            "ialgo": m.get("ialgo", 38),
            "nelmdl": m.get("nelmdl", -5),
            # AIMD
            "tebeg": m.get("tebeg", 300),
            "teend": m.get("teend", 300),
            "potim": m.get("potim", 1),
            "smass": m.get("smass", 1.0),
        }

    def render_incar(self):
        """Render INCAR from Jinja2 template."""
        if self.incar_template is None:
            raise NotImplementedError(
                f"Module '{self.name}' has no incar_template")
        return render_template(self.incar_template, **self.get_incar_vars())

    def render_kpoints(self):
        """KPOINTS is generated by vaspkit, not from template."""
        raise RuntimeError("Use generate_kpoints() instead of render_kpoints()")

    def generate_kpoints_and_potcar(self):
        """
        Generate KPOINTS and POTCAR using VASPKIT task 102.
        VASPKIT 102 also writes INCAR; setup_dir overwrites INCAR later.
        """
        vaspkit_exe = self.settings.get("vaspkit", {}).get(
            "executable",
            "/home/lilin/software/vaspkit.1.3.1/bin/vaspkit")
        kspacing = self.module_params.get(
            "vaspkit_102_spacing",
            self.precision_config.get("kpoints", {}).get(
                "vaspkit_102_spacing", 0.04))

        cwd = os.getcwd()
        os.chdir(self.work_dir)
        try:
            # User-approved VASPKIT flow:
            # (echo 102; echo 2; echo 0.04) | vaspkit
            input_str = f"102\n2\n{kspacing}\n"
            result = subprocess.run(
                [vaspkit_exe],
                input=input_str,
                capture_output=True, text=True, timeout=120,
                check=False)
            # Save VASPKIT 102 logs
            log_path = os.path.join(self.work_dir, "vaspkit_102.log")
            with open(log_path, 'w') as lf:
                lf.write("=== stdout ===\n")
                lf.write(result.stdout)
                lf.write("\n=== stderr ===\n")
                lf.write(result.stderr)
            if result.returncode != 0:
                raise RuntimeError(
                    f"VASPKIT 102 failed in {self.work_dir}: "
                    f"{result.stderr[-500:]}")
        finally:
            os.chdir(cwd)

        kpoints_path = os.path.join(self.work_dir, "KPOINTS")
        potcar_path = os.path.join(self.work_dir, "POTCAR")
        if not os.path.exists(kpoints_path):
            raise RuntimeError(f"KPOINTS generation failed in {self.work_dir}")
        if not os.path.exists(potcar_path):
            raise RuntimeError(f"POTCAR generation failed in {self.work_dir}")
        self._record_potcar_info(potcar_path)

    def optimization_potcar_path(self):
        """Return the canonical POTCAR generated in the optimization step."""
        return os.path.join(self.project.project_dir, "01_opt", "POTCAR")

    def reuse_optimization_potcar(self):
        """
        Reuse the VASPKIT-generated optimization POTCAR for downstream tasks.
        Returns True when a POTCAR was copied.
        """
        if self.name == "opt":
            return False
        opt_potcar = self.optimization_potcar_path()
        if not os.path.exists(opt_potcar):
            return False
        shutil.copy2(opt_potcar, os.path.join(self.work_dir, "POTCAR"))
        self._record_potcar_info(os.path.join(self.work_dir, "POTCAR"))
        return True

    def generate_kpoints(self):
        """Compatibility wrapper for older callers."""
        self.generate_kpoints_and_potcar()

    def write_runtime_kpoints_placeholder(self):
        """Make KPOINTS review-safe when sub.vasp regenerates it later."""
        if self.name == "band":
            text = (
                "KPOINTS generated at job runtime by VASPKIT 302\n"
                "0\n"
                "Line-mode placeholder\n"
                "# sub.vasp will run `(echo 302) | vaspkit` and copy "
                "KPATH.in to KPOINTS before VASP starts.\n"
            )
        elif self.name in ("hse", "hse_band"):
            text = (
                "KPOINTS generated at job runtime by VASPKIT 251\n"
                "0\n"
                "Hybrid-band placeholder\n"
                "# sub.vasp will run `(echo 251; echo 2; echo 0.04; "
                "echo 0.05) | vaspkit` before VASP starts.\n"
            )
        else:
            return
        with open(os.path.join(self.work_dir, "KPOINTS"), 'w') as f:
            f.write(text)

    def _is_our_incar(self, path):
        """Check if INCAR was written by us (not vaspkit)."""
        with open(path, 'r') as f:
            content = f.read(200)
        return "DFT Workflow" in content or "ISIF" in content

    def render_optcell(self, fix_c_axis=True):
        """
        Render OPTCELL for 2D materials.
        fix_c_axis=True: in-plane a/b relax, c-axis fixed (110/110/000).
        fix_c_axis=False: all directions relax (111/111/111).
        """
        if fix_c_axis:
            return render_template("optcell.j2",
                                   oc_a1=1, oc_a2=1, oc_a3=0,
                                   oc_b1=1, oc_b2=1, oc_b3=0,
                                   oc_c1=0, oc_c2=0, oc_c3=0)
        else:
            return render_template("optcell.j2",
                                   oc_a1=1, oc_a2=1, oc_a3=1,
                                   oc_b1=1, oc_b2=1, oc_b3=1,
                                   oc_c1=1, oc_c2=1, oc_c3=1)

    def render_submit_script(self, job_name=None, pre_cmds="", post_cmds=""):
        """Render Slurm submission script."""
        slurm = self.settings.get("slurm", {})
        env = self.settings.get("env", {})
        return render_template(
            "sub.j2",
            job_name=job_name or f"{self.project.name}_{self.name}",
            ntasks=slurm.get("ntasks", 16),
            partition=slurm.get("partition", "cpus"),
            mpi_path=env.get("PATH_MPI", "/home/soft/openmpi/bin"),
            mpi_lib=env.get("LD_MPI", "/home/soft/openmpi/lib"),
            aocl_lib=env.get("LD_AOCL",
                             "/home/soft/AOCL/5.2.0/gcc/lib_LP64"),
            omp_threads=env.get("OMP_NUM_THREADS", 1),
            vasp_executable=self.get_vasp_executable(),
            pre_cmds=pre_cmds,
            post_cmds=post_cmds)

    def get_phonopy_fd_settings(self):
        """Resolve finite-displacement phonopy settings for 2D materials."""
        cfg = dict(self.module_params)
        stage = cfg.get("stage", "production")
        stage_cfg = dict(cfg.get(stage, {}))
        dim = list(stage_cfg.get("dim", cfg.get("dim", [4, 4, 1])))
        if len(dim) != 3:
            raise RuntimeError("phonopy_fd dim must contain exactly 3 integers")
        dim = [int(x) for x in dim]

        if stage_cfg.get("scale_by_lattice", True):
            poscar = os.path.join(self.project.project_dir, "00_input", "POSCAR")
            lengths = estimate_vacuum_axis(poscar)["lengths"]
            min_len = stage_cfg.get("min_inplane_length")
            max_dim = int(stage_cfg.get("max_dim", cfg.get("max_dim", 6)))
            if min_len:
                for i in (0, 1):
                    required = int(math.ceil(float(min_len) / lengths[i]))
                    dim[i] = min(max(dim[i], required), max_dim)
        dim[2] = 1

        return {
            "stage": stage,
            "dim": dim,
            "symprec": stage_cfg.get("symprec", cfg.get("symprec", 1e-3)),
            "displacement_distance": stage_cfg.get(
                "displacement_distance",
                cfg.get("displacement_distance", 0.01)),
            "dos_mesh": stage_cfg.get("dos_mesh", cfg.get("dos_mesh", [40, 40, 1])),
            "band_points": stage_cfg.get("band_points", cfg.get("band_points", 101)),
            "band_path": stage_cfg.get(
                "band_path",
                cfg.get("band_path", "gamma_m_k_gamma")),
            "imaginary_followup": cfg.get("imaginary_followup", {}),
        }

    def write_supercell_kpoints(self, dim):
        """Scale the primitive VASPKIT mesh down for a phonopy supercell."""
        kpoints_path = os.path.join(self.work_dir, "KPOINTS")
        primitive_mesh = self.module_params.get("primitive_reference_kmesh")
        if not primitive_mesh:
            result = validate_kpoints_2d_regular(kpoints_path)
            primitive_mesh = result.get("mesh")
        if not primitive_mesh:
            primitive_mesh = self.module_params.get(
                "primitive_reference_kmesh", [12, 12, 1])
        mesh = [
            max(1, int(round(int(primitive_mesh[0]) / dim[0]))),
            max(1, int(round(int(primitive_mesh[1]) / dim[1]))),
            1,
        ]
        with open(kpoints_path, "w") as f:
            f.write(
                "Finite-displacement supercell mesh\n"
                "0\n"
                "Gamma\n"
                f"{mesh[0]} {mesh[1]} {mesh[2]}\n"
                "0 0 0\n"
            )
        return {"primitive_mesh": primitive_mesh, "supercell_mesh": mesh}

    def render_phonopy_fd_submit_script(self, fd_settings):
        """Render the manager Slurm script for finite-displacement phonopy."""
        slurm = self.settings.get("slurm", {})
        env = self.settings.get("env", {})
        phonopy_exe = self.settings.get("phonopy", {}).get(
            "executable", "phonopy")
        vasp_exe = self.get_vasp_executable()
        dim = " ".join(str(x) for x in fd_settings["dim"])
        dos_mesh = " ".join(str(x) for x in fd_settings["dos_mesh"])
        band_points = int(fd_settings["band_points"])
        followup = fd_settings.get("imaginary_followup", {})
        imag_threshold = followup.get("threshold_thz", -0.2)
        next_dim = " ".join(str(x) for x in followup.get("next_dim", [5, 5, 1]))
        next_ediff = followup.get("next_ediff", "1E-08")
        kmesh_multiplier = followup.get("kmesh_multiplier", 1.25)
        symprec = fd_settings["symprec"]
        amplitude = fd_settings["displacement_distance"]
        opt_contcar = os.path.join(self.project.project_dir, "01_opt", "CONTCAR")
        kguard = kpoints_2d_runtime_guard()
        job_name = f"{self.project.name}_{self.name}"
        return f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --ntasks={slurm.get("ntasks", 16)}
#SBATCH --partition={slurm.get("partition", "cpus")}
#SBATCH --output=slurm_%j.log
set -eo pipefail

echo "Date              = $(date)"
echo "Hostname          = $(hostname -s)"
echo "Working Directory = $(pwd)"
echo "Number of Nodes Allocated = $SLURM_JOB_NUM_NODES"
echo "Number of Tasks           = $SLURM_JOB_CPUS_PER_NODE"

export PATH={env.get("PATH_MPI", "/home/soft/openmpi/bin")}:$PATH
export LD_LIBRARY_PATH={env.get("LD_MPI", "/home/soft/openmpi/lib")}:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH={env.get("LD_AOCL", "/home/soft/AOCL/5.2.0/gcc/lib_LP64")}:$LD_LIBRARY_PATH
export OMP_NUM_THREADS={env.get("OMP_NUM_THREADS", 1)}

if [ ! -s {opt_contcar} ]; then
    echo "ERROR: missing optimized CONTCAR: {opt_contcar}" >&2
    exit 2
fi
cp {opt_contcar} POSCAR

{kguard}

rm -rf disp-* POSCAR-[0-9]* FORCE_SETS FORCE_CONSTANTS band.conf mesh.conf band.yaml total_dos.dat projected_dos.dat
{phonopy_exe} -d --dim="{dim}" --tolerance={symprec} --amplitude={amplitude} > phonopy_displacements.log 2>&1

count=$(find . -maxdepth 1 -name 'POSCAR-[0-9]*' | wc -l)
if [ "$count" -eq 0 ]; then
    echo "ERROR: phonopy generated no displaced POSCAR files" >&2
    exit 6
fi

for poscar in POSCAR-[0-9]*; do
    idx=${{poscar#POSCAR-}}
    disp_dir=disp-$idx
    mkdir -p "$disp_dir"
    cp "$poscar" "$disp_dir/POSCAR"
    cp INCAR KPOINTS POTCAR "$disp_dir/"
done

for disp_dir in disp-*; do
    echo "Starting VASP force run in $disp_dir at $(date)"
    (
        cd "$disp_dir"
        set +e
        mpirun -np $SLURM_JOB_CPUS_PER_NODE {vasp_exe} > vasp.stdout 2> vasp.stderr
        code=$?
        set -e
        echo "$code" > vasp.exitcode
        if [ "$code" -ne 0 ]; then
            echo "FATAL: VASP failed in $disp_dir with exit code $code" >&2
            tail -50 vasp.stderr >&2
            exit "$code"
        fi
        if [ ! -s vasprun.xml ]; then
            echo "FATAL: missing vasprun.xml in $disp_dir" >&2
            exit 7
        fi
    )
done

{phonopy_exe} -f disp-*/vasprun.xml > phonopy_force_sets.log 2>&1
if [ ! -s FORCE_SETS ]; then
    echo "FATAL: FORCE_SETS was not generated" >&2
    exit 8
fi

cat > band.conf <<'EOF'
DIM = {dim}
BAND = 0 0 0  0.5 0 0  0.3333333333 0.3333333333 0  0 0 0
BAND_LABELS = Gamma M K Gamma
BAND_POINTS = {band_points}
FORCE_CONSTANTS = WRITE
EOF

cat > mesh.conf <<'EOF'
DIM = {dim}
MP = {dos_mesh}
DOS = .TRUE.
EOF

{phonopy_exe} -p band.conf > phonopy_band.log 2>&1
{phonopy_exe} -p mesh.conf > phonopy_dos.log 2>&1

python3 - <<'PY'
import yaml
from pathlib import Path

threshold = float("{imag_threshold}")
next_dim = "{next_dim}"
next_ediff = "{next_ediff}"
kmesh_multiplier = float("{kmesh_multiplier}")
band_yaml = Path("band.yaml")
report = Path("imaginary_mode_followup.yaml")

if band_yaml.exists():
    data = yaml.safe_load(band_yaml.read_text()) or {{}}
    min_freq = None
    min_item = {{}}
    for q_index, qpt in enumerate(data.get("phonon", [])):
        q_pos = qpt.get("q-position")
        for band_index, band in enumerate(qpt.get("band", [])):
            freq = band.get("frequency")
            if freq is None:
                continue
            if min_freq is None or freq < min_freq:
                min_freq = float(freq)
                min_item = {{
                    "q_index": q_index,
                    "q_position": q_pos,
                    "band_index": band_index,
                    "frequency_thz": min_freq,
                }}
    payload = {{
        "threshold_thz": threshold,
        "minimum_frequency": min_item,
        "has_actionable_imaginary_mode": (
            min_freq is not None and min_freq < threshold
        ),
        "recommended_next_steps": [],
    }}
    if payload["has_actionable_imaginary_mode"]:
        payload["recommended_next_steps"] = [
            "Review the imaginary-mode q-point and eigenvector before changing the structure.",
            f"Repeat finite-displacement phonopy with enlarged in-plane supercell dim={{next_dim}}.",
            f"Increase force-calculation k-point density by about {{kmesh_multiplier}}x.",
            f"Tighten force-calculation EDIFF to {{next_ediff}}.",
            "If the imaginary mode persists, run softmode displacement along the eigenvector and relax candidate structures.",
        ]
    report.write_text(yaml.safe_dump(payload, sort_keys=False))
PY

echo "Finite-displacement phonopy workflow completed at $(date)"
"""

    def get_vasp_executable(self):
        """Choose the VASP executable required by this module."""
        vasp_cfg = self.settings.get("vasp", {})
        default_std = "/home/soft/vasp/vasp.6.3.2/bin/vasp_std"
        std_exe = vasp_cfg.get("executable_std",
                               vasp_cfg.get("executable", default_std))
        if self.name == "soc":
            return vasp_cfg.get(
                "executable_ncl",
                os.path.join(os.path.dirname(std_exe), "vasp_ncl"))
        if self.name == "gamma":
            return vasp_cfg.get(
                "executable_gam",
                os.path.join(os.path.dirname(std_exe), "vasp_gam"))
        return std_exe

    def normalized_module_label(self):
        """Return the public module label without renaming local dirs."""
        label_map = {
            "01_opt": "01_opt",
            "02_scf": "02_scf",
            "03_pbeband": "03_band",
            "04_dos": "04_dos",
        }
        return label_map.get(self.module_dir, self.module_dir)

    def method_label(self):
        labels = {
            "opt": "pbe_geometry_optimization",
            "scf": "pbe_scf",
            "band": "pbe_band_structure",
            "dos": "pbe_dos",
        }
        return labels.get(self.name, self.name)

    def calculation_purpose(self):
        purposes = {
            "opt": "Relax 2D structure while keeping the vacuum axis fixed.",
            "scf": "Generate a converged PBE charge density for child modules.",
            "band": "Compute the PBE band structure from the SCF charge density.",
            "dos": "Compute PBE density of states from the SCF charge density.",
        }
        return purposes.get(self.name, f"Run {self.name} calculation module.")

    def dependency_intent(self, copy_inputs_from=None):
        dependencies = []
        if copy_inputs_from:
            dependencies.append({
                "source_dir": copy_inputs_from,
                "status_at_prepare": (
                    "available" if os.path.isdir(copy_inputs_from)
                    else "missing_at_prepare"
                ),
            })
        return {
            "dependencies": dependencies,
            "prepare_time_note": (
                "Prepared-stage provenance records intended parent files. "
                "Runtime pre-commands still verify required parent artifacts "
                "before VASP starts."
            ),
        }

    def generated_input_records(self):
        base = self.project.project_dir
        records = {}
        for name, required in (
                ("POSCAR", True),
                ("INCAR", True),
                ("KPOINTS", True),
                ("POTCAR", True),
                ("sub.vasp", self.name in ("opt", "scf", "band", "dos")),
                ("kpoints_summary.yaml", False),
                ("potcar_info.yaml", False),
                ("OPTCELL", self.name == "opt")):
            path = os.path.join(self.work_dir, name)
            if required or os.path.exists(path):
                records[name] = path_record(
                    path, base_dir=base, role="generated_or_copied_input",
                    required=required)
        if records.get("INCAR"):
            records["INCAR"]["template"] = self.incar_template
        if records.get("KPOINTS"):
            records["KPOINTS"]["source"] = self.inheritance_policy().get(
                "KPOINTS", {}).get("mode", "prepared")
        if records.get("POTCAR"):
            records["POTCAR"]["source"] = (
                "reused_from_01_opt" if self.name != "opt"
                else "vaspkit_102_or_existing"
            )
        return records

    def parent_file_records(self, copy_inputs_from=None):
        policy = self.inheritance_policy(copy_inputs_from)
        base = self.project.project_dir
        parent = {
            "policy": policy,
            "files": {},
        }
        poscar_source = policy.get("poscar", {}).get("source")
        if poscar_source:
            parent["files"]["source_structure"] = path_record(
                os.path.join(self.project.project_dir, poscar_source),
                base_dir=base, role="source_structure",
                required=policy["poscar"].get("required_at_runtime", False))
        for fname in ("CHGCAR", "WAVECAR"):
            source = policy.get(fname, {}).get("source")
            if source:
                parent["files"][fname] = path_record(
                    source, base_dir=base, role="runtime_parent_file",
                    required=policy[fname].get("mode") == "required")
        if self.name != "opt":
            parent["files"]["POTCAR_parent"] = path_record(
                self.optimization_potcar_path(), base_dir=base,
                role="potcar_reuse_source", required=True)
        return parent

    def prepared_review_state(self, copy_inputs_from=None):
        """Classify prepared provenance without claiming final results."""
        missing_required = []
        warnings = []
        for name, rec in self.generated_input_records().items():
            if rec.get("required") and not rec.get("exists"):
                missing_required.append(name)
        parent = self.parent_file_records(copy_inputs_from)
        for name, rec in parent.get("files", {}).items():
            if rec.get("required") and not rec.get("exists"):
                warnings.append(f"{name} missing at prepare time")
        state = "blocked" if missing_required else "pending_review"
        return {
            "state": state,
            "missing_required_prepared_inputs": missing_required,
            "warnings": warnings,
            "final_result_status": "not_applicable_pre_submission",
        }

    def postprocessing_intent(self):
        if self.name == "band":
            return {
                "tool": "vaspkit",
                "task": 211,
                "source_files": ["EIGENVAL", "KPOINTS", "OUTCAR"],
                "output_files": ["BAND_GAP"],
                "status": "intended_runtime_postprocess",
            }
        if self.name == "dos":
            return {
                "tool": "vasp",
                "source_files": ["DOSCAR", "vasprun.xml", "OUTCAR"],
                "output_files": ["DOSCAR"],
                "status": "dos_parser_pending",
            }
        return {
            "tool": None,
            "source_files": [],
            "output_files": [],
            "status": "none",
        }

    def inheritance_policy(self, copy_inputs_from=None):
        """Describe runtime file inheritance from the parent calculation."""
        chg_required = {
            "band", "dos", "hse", "hse_scf", "hse_band",
            "optical", "bader", "ccd", "potential",
            "vacuum", "effective_mass",
        }
        no_wavecar_reuse = {
            "scf", "band", "dos", "hse", "hse_scf", "hse_band",
            "optical", "phonopy", "phonopy_fd", "phonon_dfpt_check",
            "aimd", "effective_mass", "mobility",
            "bader", "ccd", "potential",
        }
        policy = {
            "parent_dir": copy_inputs_from,
            "poscar": {
                "source": (
                    "00_input/POSCAR" if self.name == "opt"
                    else "01_opt/CONTCAR"
                ),
                "required_at_runtime": self.name != "opt",
            },
            "CHGCAR": {
                "mode": "not_used",
                "source": None,
                "reason": "fresh calculation or no parent dependency",
            },
            "WAVECAR": {
                "mode": "not_used",
                "source": None,
                "reason": "fresh calculation or no parent dependency",
            },
        }
        if copy_inputs_from:
            if self.name in chg_required:
                policy["CHGCAR"] = {
                    "mode": "required",
                    "source": os.path.join(copy_inputs_from, "CHGCAR"),
                    "reason": "INCAR reads parent charge density",
                }
            if self.name in no_wavecar_reuse:
                policy["WAVECAR"] = {
                    "mode": "remove",
                    "source": os.path.join(copy_inputs_from, "WAVECAR"),
                    "reason": "KPOINTS/NBANDS/method may differ from parent",
                }
            else:
                policy["WAVECAR"] = {
                    "mode": "copy_if_exists",
                    "source": os.path.join(copy_inputs_from, "WAVECAR"),
                    "reason": "safe continuation from compatible parent task",
                }
        if self.name == "band":
            policy["KPOINTS"] = {
                "mode": "runtime_vaspkit_302",
                "reason": "review placeholder is replaced by KPATH.in",
            }
        elif self.name in ("hse", "hse_band"):
            policy["KPOINTS"] = {
                "mode": "runtime_vaspkit_251",
                "reason": "hybrid band uses uniform grid plus zero-weight path",
            }
        elif self.name == "effective_mass":
            policy["KPOINTS"] = {
                "mode": "effective_mass_manager",
                "reason": "manager job generates explicit local k-lines around band edges",
            }
        elif self.name == "mobility":
            policy["KPOINTS"] = {
                "mode": "mobility_manager",
                "reason": "manager job generates strain, relaxation, SCF, and local band-edge subruns",
            }
        else:
            policy["KPOINTS"] = {"mode": "prepared", "reason": "prepared input"}
        return policy

    def write_module_provenance(self, copy_inputs_from=None):
        """Write reviewable provenance for this prepared module."""
        vaspkit_cfg = self.settings.get("vaspkit", {})
        slurm_cfg = self.settings.get("slurm", {})
        data = {
            "schema_version": "2026-06-20.batch_a.v1",
            "project": self.project.name,
            "module": self.name,
            "module_dir": self.module_dir,
            "prepared_at": datetime.now().isoformat(),
            "work_dir": self.work_dir,
            "module_identity": {
                "name": self.name,
                "actual_module_dir": self.module_dir,
                "normalized_module_label": self.normalized_module_label(),
                "method_label": self.method_label(),
                "calculation_purpose": self.calculation_purpose(),
                "batch_a_baseline": self.name in ("opt", "scf", "band", "dos"),
            },
            "inheritance": self.inheritance_policy(copy_inputs_from),
            "parent_files": self.parent_file_records(copy_inputs_from),
            "generated_inputs": self.generated_input_records(),
            "executable_environment": {
                "vasp_executable": self.get_vasp_executable(),
                "vaspkit_executable": vaspkit_cfg.get("executable"),
                "vaspkit_version": vaspkit_cfg.get("version"),
                "slurm_partition": slurm_cfg.get("partition"),
                "slurm_ntasks": slurm_cfg.get("ntasks"),
                "submit_template": slurm_cfg.get("submit_template"),
            },
            "dependency_status": self.dependency_intent(copy_inputs_from),
            "restart_overwrite": {
                "prepared_inputs_may_overwrite": [
                    "INCAR", "KPOINTS", "POTCAR", "sub.vasp",
                    "kpoints_summary.yaml", "module_provenance.yaml",
                ],
                "restart_intent": "fresh_prepare_no_job_restart",
                "runtime_wavecar_policy": self.inheritance_policy(
                    copy_inputs_from).get("WAVECAR", {}),
            },
            "post_processing": self.postprocessing_intent(),
            "review_state": self.prepared_review_state(copy_inputs_from),
            "vasp_executable": self.get_vasp_executable(),
            "incar_template": self.incar_template,
        }
        path = os.path.join(self.work_dir, "module_provenance.yaml")
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        return path

    # ---- File operations ----

    def setup_dir(self, copy_inputs_from=None):
        """Create working directory and write all input files."""
        os.makedirs(self.work_dir, exist_ok=True)

        if self.name == "phonopy_fd":
            self.setup_phonopy_fd_dir(copy_inputs_from=copy_inputs_from)
            return
        if self.name == "effective_mass":
            self.setup_effective_mass_dir(copy_inputs_from=copy_inputs_from)
            return
        if self.name == "mobility":
            self.setup_mobility_dir(copy_inputs_from=copy_inputs_from)
            return

        # Copy POSCAR from project input
        src_poscar = os.path.join(
            self.project.project_dir, "00_input", "POSCAR")
        if os.path.exists(src_poscar):
            # For opt, use original POSCAR; for others, use CONTCAR from opt
            if self.name != "opt":
                opt_contcar = os.path.join(
                    self.project.project_dir, "01_opt", "CONTCAR")
                if os.path.exists(opt_contcar):
                    shutil.copy(opt_contcar,
                                os.path.join(self.work_dir, "POSCAR"))
                else:
                    shutil.copy(src_poscar,
                                os.path.join(self.work_dir, "POSCAR"))
            else:
                shutil.copy(src_poscar,
                            os.path.join(self.work_dir, "POSCAR"))

        # NOTE: CHGCAR/WAVECAR are NOT copied here (they don't exist yet).
        # Instead, sub.vasp includes a pre-step to copy them from the
        # dependency directory when the job actually runs.

        # Write KPOINTS/POTCAR first. VASPKIT may also write INCAR;
        # INCAR is rendered below and intentionally overwrites it.
        potcar_path = os.path.join(self.work_dir, "POTCAR")
        if not os.path.exists(potcar_path):
            self.reuse_optimization_potcar()

        if (not os.path.exists(os.path.join(self.work_dir, "KPOINTS")) or
                not os.path.exists(potcar_path)):
            self.generate_kpoints_and_potcar()
            self.reuse_optimization_potcar()
        if os.path.exists(potcar_path):
            self._record_potcar_info(potcar_path)
        self.write_runtime_kpoints_placeholder()

        # Write INCAR AFTER KPOINTS (vaspkit may overwrite INCAR)
        incar_content = self.render_incar()
        with open(os.path.join(self.work_dir, "INCAR"), 'w') as f:
            f.write(incar_content)
        inheritance = self.inheritance_policy(copy_inputs_from)

        # Build pre-VASP commands: use optimized structure and dependency data.
        pre_cmds = ""
        opt_contcar = os.path.join(
            self.project.project_dir, "01_opt", "CONTCAR")
        if self.name != "opt":
            pre_cmds += (
                f"# Use optimized structure when available\n"
                f"if [ -f {opt_contcar} ]; then cp {opt_contcar} POSCAR; "
                f"else echo 'ERROR: missing optimized CONTCAR: {opt_contcar}'; exit 2; fi\n"
            )
        if copy_inputs_from:
            chg = inheritance["CHGCAR"]
            wave = inheritance["WAVECAR"]
            pre_cmds += "# Apply reviewed parent-file inheritance policy\n"
            if chg["mode"] == "required":
                pre_cmds += (
                    f"if [ ! -s {chg['source']} ]; then "
                    f"echo 'ERROR: required parent CHGCAR missing: {chg['source']}'; "
                    f"exit 5; fi\n"
                    f"cp {chg['source']} CHGCAR\n"
                )
            elif chg["mode"] == "copy_if_exists":
                pre_cmds += (
                    f"[ -s {chg['source']} ] && cp {chg['source']} CHGCAR\n"
                )
            if wave["mode"] == "remove":
                pre_cmds += (
                    f"# Do not reuse WAVECAR: {wave['reason']}\n"
                    f"rm -f WAVECAR\n"
                )
            elif wave["mode"] == "copy_if_exists":
                pre_cmds += (
                    f"[ -s {wave['source']} ] && cp {wave['source']} WAVECAR\n"
                )
        if self.name in ("band", "hse", "hse_band"):
            vaspkit_exe = self.settings.get("vaspkit", {}).get(
                "executable",
                "/home/lilin/software/vaspkit.1.3.1/bin/vaspkit")
            pre_cmds += (
                f"# Generate 2D k-path with VASPKIT; requires vacuum along c axis\n"
                f"(echo 302) | {vaspkit_exe} > vaspkit_302.log 2>&1\n"
                f"if [ ! -f KPATH.in ]; then echo 'ERROR: VASPKIT 302 did not create KPATH.in'; exit 3; fi\n"
            )
            if self.name in ("hse", "hse_band"):
                pre_cmds += (
                    f"# HSE band KPOINTS: uniform grid + zero-weight path\n"
                    f"(echo 251; echo 2; echo 0.04; echo 0.05) | {vaspkit_exe} "
                    f"> vaspkit_251.log 2>&1\n"
                    f"if [ ! -f KPOINTS ]; then echo 'ERROR: VASPKIT 251 did not create KPOINTS'; exit 4; fi\n"
                )
            elif self.name == "band":
                pre_cmds += (
                    f"cp KPATH.in KPOINTS\n"
                )

        # Add 2D k-points guard before VASP
        pre_cmds += kpoints_2d_runtime_guard()

        # Build post-VASP commands (vaspkit band gap extraction)
        post_cmds = ""
        if self.name == "band":
            vaspkit_exe = self.settings.get("vaspkit", {}).get(
                "executable",
                "/home/lilin/software/vaspkit.1.3.1/bin/vaspkit")
            post_cmds += (
                f"# Extract PBE band gap via vaspkit 211\n"
                f"(echo 211; echo 1; echo 1) | {vaspkit_exe} "
                f"> vaspkit_211.log 2>&1 || test -s BAND_GAP\n"
            )
        if self.name in ("hse", "hse_band"):
            vaspkit_exe = self.settings.get("vaspkit", {}).get(
                "executable",
                "/home/lilin/software/vaspkit.1.3.1/bin/vaspkit")
            post_cmds += (
                f"# Extract HSE band gap via vaspkit 252\n"
                f"(echo 252) | {vaspkit_exe} > vaspkit_252.log 2>&1\n"
            )
        if self.name == "optical":
            vaspkit_exe = self.settings.get("vaspkit", {}).get(
                "executable",
                "/home/lilin/software/vaspkit.1.3.1/bin/vaspkit")
            energy_unit = self.module_params.get(
                "vaspkit_710_energy_unit", 1)
            quantities = self.module_params.get(
                "vaspkit_710_quantities", [1, 2, 3])
            if isinstance(quantities, int):
                quantities = [quantities]
            post_cmds += (
                f"# Convert low-dimensional optical data via vaspkit 710\n"
            )
            for quantity in quantities:
                post_cmds += (
                    f"(echo 710; echo {energy_unit}; echo {quantity}) | "
                    f"{vaspkit_exe} >> vaspkit_710.log 2>&1\n"
                )

        # Write submit script with pre/post commands as template parameters
        sub_content = self.render_submit_script(
            pre_cmds=pre_cmds, post_cmds=post_cmds)
        with open(os.path.join(self.work_dir, "sub.vasp"), 'w') as f:
            f.write(sub_content)
        os.chmod(os.path.join(self.work_dir, "sub.vasp"), 0o755)

        # Write kpoints_summary.yaml
        kpath = os.path.join(self.work_dir, "KPOINTS")
        kpoints_summary = write_kpoints_summary(
            self.name, kpath, os.path.join(self.work_dir, "kpoints_summary.yaml"))
        if kpoints_summary.get("passed") is False:
            errors = "; ".join(kpoints_summary.get("errors", []))
            raise RuntimeError(
                f"{self.module_dir} KPOINTS failed 2D validation: {errors}"
            )

        # Write OPTCELL for 2D materials (fix c-axis during optimization)
        if self.name == "opt":
            optcell_content = self.render_optcell(fix_c_axis=True)
            with open(os.path.join(self.work_dir, "OPTCELL"), 'w') as f:
                f.write(optcell_content)

        self.write_module_provenance(copy_inputs_from)

    def setup_effective_mass_dir(self, copy_inputs_from=None):
        """Prepare the 2D effective-mass manager directory."""
        src_poscar = os.path.join(
            self.project.project_dir, "00_input", "POSCAR")
        shutil.copy(src_poscar, os.path.join(self.work_dir, "POSCAR"))

        if not os.path.exists(os.path.join(self.work_dir, "POTCAR")):
            self.reuse_optimization_potcar()
        if not os.path.exists(os.path.join(self.work_dir, "POTCAR")):
            self.generate_potcar()
        potcar_path = os.path.join(self.work_dir, "POTCAR")
        if os.path.exists(potcar_path):
            self._record_potcar_info(potcar_path)

        with open(os.path.join(self.work_dir, "KPOINTS"), "w") as f:
            f.write(
                "Effective-mass manager placeholder\n"
                "0\n"
                "Gamma\n"
                "1 1 1\n"
                "0 0 0\n"
                "# Local explicit k-point files are generated in cbm/vbm "
                "subdirectories at job runtime.\n"
            )

        incar_content = self.render_incar()
        with open(os.path.join(self.work_dir, "INCAR"), 'w') as f:
            f.write(incar_content)

        em_settings = self.get_effective_mass_settings()
        with open(os.path.join(self.work_dir, "effective_mass_settings.yaml"), "w") as f:
            yaml.dump(em_settings, f, default_flow_style=False)
        with open(os.path.join(self.work_dir, "effective_mass_runtime.py"), "w") as f:
            f.write(self.render_effective_mass_runtime_script())
        os.chmod(os.path.join(self.work_dir, "effective_mass_runtime.py"), 0o755)

        provenance_path = self.write_module_provenance(copy_inputs_from)
        with open(provenance_path, "r") as f:
            provenance = yaml.safe_load(f) or {}
        provenance["effective_mass"] = {
            "method": em_settings["method"],
            "edge_source": em_settings["edge_source"],
            "charge_parent": em_settings["charge_parent"],
            "directions": em_settings["directions"],
            "carriers": em_settings["carriers"],
            "delta_k_inv_angstrom": em_settings["delta_k"],
            "points_each_side": em_settings["points_each_side"],
            "fit_windows": em_settings["fit_windows"],
            "basis": "in-plane reciprocal-lattice directions a* and b*",
            "z_direction_policy": "disabled for monolayer 2D materials",
        }
        with open(provenance_path, "w") as f:
            yaml.dump(provenance, f, default_flow_style=False)

        sub_content = self.render_effective_mass_submit_script()
        with open(os.path.join(self.work_dir, "sub.vasp"), 'w') as f:
            f.write(sub_content)
        os.chmod(os.path.join(self.work_dir, "sub.vasp"), 0o755)

        kpoints_summary = write_kpoints_summary(
            self.name,
            os.path.join(self.work_dir, "KPOINTS"),
            os.path.join(self.work_dir, "kpoints_summary.yaml"))
        kpoints_summary["mode"] = "effective_mass_manager_placeholder"
        kpoints_summary["passed"] = None
        kpoints_summary["warning"] = (
            "Root KPOINTS is not used by VASP. The manager job generates "
            "explicit kz=0 local k-lines in each effective-mass subdirectory."
        )
        with open(os.path.join(self.work_dir, "kpoints_summary.yaml"), "w") as f:
            yaml.dump(kpoints_summary, f, default_flow_style=False)

    def get_effective_mass_settings(self):
        """Return reviewed defaults for 2D local-curvature effective masses."""
        cfg = self.module_params
        edge_source = cfg.get("edge_source", "03_pbeband")
        charge_parent = cfg.get("charge_parent", "02_scf")
        directions = cfg.get("directions", ["a", "b"])
        carriers = cfg.get("carriers", ["electron", "hole"])
        fit_windows = cfg.get("fit_windows")
        points_each_side = int(cfg.get("points_each_side", 5))
        if not fit_windows:
            fit_windows = [points_each_side]
        return {
            "method": cfg.get("method", "pbe"),
            "edge_source": edge_source,
            "edge_source_dir": os.path.join(self.project.project_dir, edge_source),
            "charge_parent": charge_parent,
            "charge_parent_dir": os.path.join(self.project.project_dir, charge_parent),
            "optimized_contcar": os.path.join(self.project.project_dir, "01_opt", "CONTCAR"),
            "directions": directions,
            "carriers": carriers,
            "delta_k": float(cfg.get("delta_k", 0.005)),
            "points_each_side": points_each_side,
            "fit_windows": [int(x) for x in fit_windows],
            "max_fit_energy_meV": float(cfg.get("max_fit_energy_meV", 50.0)),
            "max_residual_meV": float(cfg.get("max_residual_meV", 5.0)),
            "valley_tolerance_meV": float(cfg.get("valley_tolerance_meV", 5.0)),
            "max_valleys": int(cfg.get("max_valleys", 2)),
            "occupation_threshold": float(cfg.get("occupation_threshold", 0.5)),
            "min_gap_eV": float(cfg.get("min_gap_eV", 0.01)),
        }

    def render_effective_mass_submit_script(self):
        """Render the Slurm manager script for 2D effective masses."""
        slurm = self.settings.get("slurm", {})
        env = self.settings.get("env", {})
        vasp_exe = self.get_vasp_executable()
        job_name = f"{self.project.name}_{self.name}"
        return f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --ntasks={slurm.get("ntasks", 16)}
#SBATCH --partition={slurm.get("partition", "cpus")}
#SBATCH --output=slurm_%j.log
set -eo pipefail
trap 'echo $? > effective_mass.exitcode' EXIT

echo "Date              = $(date)"
echo "Hostname          = $(hostname -s)"
echo "Working Directory = $(pwd)"
echo "Number of Nodes Allocated = $SLURM_JOB_NUM_NODES"
echo "Number of Tasks           = $SLURM_JOB_CPUS_PER_NODE"

export PATH={env.get("PATH_MPI", "/home/soft/openmpi/bin")}:$PATH
export LD_LIBRARY_PATH={env.get("LD_MPI", "/home/soft/openmpi/lib")}:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH={env.get("LD_AOCL", "/home/soft/AOCL/5.2.0/gcc/lib_LP64")}:$LD_LIBRARY_PATH
export OMP_NUM_THREADS={env.get("OMP_NUM_THREADS", 1)}

python3 effective_mass_runtime.py prepare-runs

while IFS= read -r run_dir; do
    [ -n "$run_dir" ] || continue
    echo "Starting effective-mass VASP run in $run_dir at $(date)"
    (
        cd "$run_dir"
        if ! awk 'NF>=4 && $1+0==$1 {{if($3+0!=0) {{print "ERROR: kz="$3" != 0"; e=1}}}} END {{if(e) exit 1; else exit 0}}' KPOINTS
        then
            echo "FATAL: effective-mass KPOINTS has non-zero kz" >&2
            exit 8
        fi
        set +e
        mpirun -np $SLURM_JOB_CPUS_PER_NODE {vasp_exe} > vasp.stdout 2> vasp.stderr
        code=$?
        set -e
        echo "$code" > vasp.exitcode
        if [ "$code" -ne 0 ]; then
            echo "FATAL: VASP failed in $run_dir with exit code $code" >&2
            tail -50 vasp.stderr >&2
            exit "$code"
        fi
        if [ ! -s EIGENVAL ]; then
            echo "FATAL: missing EIGENVAL in $run_dir" >&2
            exit 9
        fi
    )
done < em_runs.txt

python3 effective_mass_runtime.py collect
echo "Effective-mass workflow completed at $(date)"
"""

    def render_effective_mass_runtime_script(self):
        """Return the runtime Python helper used inside 11_effective_mass."""
        return r'''#!/usr/bin/env python3
import csv
import math
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import yaml

HBAR2_OVER_2M0_EV_A2 = 3.80998212
DIRECTION_TO_AXIS = {"a": 0, "b": 1}


def load_settings():
    with open("effective_mass_settings.yaml", "r") as f:
        return yaml.safe_load(f) or {}


def read_lattice(poscar):
    lines = Path(poscar).read_text().splitlines()
    scale = float(lines[1].split()[0])
    lattice = np.array([
        [float(x) for x in lines[i].split()[:3]]
        for i in range(2, 5)
    ], dtype=float)
    if scale > 0:
        lattice *= scale
    return lattice


def reciprocal_lattice(poscar):
    lattice = read_lattice(poscar)
    return 2.0 * math.pi * np.linalg.inv(lattice).T


def parse_eigenval(path):
    eigenval = Path(path) / "EIGENVAL"
    if not eigenval.exists():
        raise FileNotFoundError(f"missing EIGENVAL: {eigenval}")
    lines = eigenval.read_text(errors="ignore").splitlines()
    header_idx = None
    nkpts = nbands = None
    for idx, line in enumerate(lines[:12]):
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            nkpts = int(float(parts[-2]))
            nbands = int(float(parts[-1]))
        except ValueError:
            continue
        header_idx = idx
        break
    if header_idx is None or nkpts is None or nbands is None:
        raise ValueError(f"cannot parse NKPTS/NBANDS from {eigenval}")

    cursor = header_idx + 1
    kpoints = []
    records = []
    for _ in range(nkpts):
        while cursor < len(lines) and not lines[cursor].split():
            cursor += 1
        if cursor >= len(lines):
            break
        kparts = lines[cursor].split()
        if len(kparts) < 3:
            raise ValueError(f"invalid k-point line in {eigenval}: {lines[cursor]}")
        kpoints.append([float(kparts[0]), float(kparts[1]), float(kparts[2])])
        cursor += 1
        bands = []
        for _band in range(nbands):
            while cursor < len(lines) and not lines[cursor].split():
                cursor += 1
            parts = lines[cursor].split()
            cursor += 1
            if len(parts) == 3:
                bands.append([(float(parts[1]), float(parts[2]))])
            elif len(parts) >= 5:
                bands.append([
                    (float(parts[1]), float(parts[3])),
                    (float(parts[2]), float(parts[4])),
                ])
            else:
                raise ValueError(f"invalid band line in {eigenval}: {' '.join(parts)}")
        records.append(bands)

    nspin = max(len(band) for krec in records for band in krec)
    energies = np.full((nspin, len(records), nbands), np.nan)
    occs = np.full((nspin, len(records), nbands), np.nan)
    for ik, krec in enumerate(records):
        for ib, band in enumerate(krec):
            for ispin, (energy, occ) in enumerate(band):
                energies[ispin, ik, ib] = energy
                occs[ispin, ik, ib] = occ
    return {
        "kpoints": np.array(kpoints, dtype=float),
        "energies": energies,
        "occupancies": occs,
        "nspin": nspin,
        "nkpts": len(records),
        "nbands": nbands,
    }


def find_band_edges(data, occ_threshold, valley_tolerance_meV):
    energies = data["energies"]
    occs = data["occupancies"]
    kpoints = data["kpoints"]
    vbm = None
    cbm = None
    for ispin in range(energies.shape[0]):
        for ik in range(energies.shape[1]):
            for ib in range(energies.shape[2]):
                energy = energies[ispin, ik, ib]
                occ = occs[ispin, ik, ib]
                if np.isnan(energy) or np.isnan(occ):
                    continue
                item = {
                    "energy": float(energy),
                    "spin": int(ispin),
                    "k_index": int(ik),
                    "band_index": int(ib),
                    "kpoint": [float(x) for x in kpoints[ik]],
                }
                if occ > occ_threshold and (vbm is None or energy > vbm["energy"]):
                    vbm = item
                if occ < occ_threshold and (cbm is None or energy < cbm["energy"]):
                    cbm = item
    if vbm is None or cbm is None:
        raise RuntimeError("cannot identify VBM/CBM from EIGENVAL occupancies")

    tol = valley_tolerance_meV / 1000.0
    valleys = {"vbm": [], "cbm": []}
    for ispin in range(energies.shape[0]):
        for ik in range(energies.shape[1]):
            for ib in range(energies.shape[2]):
                energy = energies[ispin, ik, ib]
                if np.isnan(energy):
                    continue
                item = {
                    "energy": float(energy),
                    "spin": int(ispin),
                    "k_index": int(ik),
                    "band_index": int(ib),
                    "kpoint": [float(x) for x in kpoints[ik]],
                }
                if abs(energy - vbm["energy"]) <= tol:
                    valleys["vbm"].append(item)
                if abs(energy - cbm["energy"]) <= tol:
                    valleys["cbm"].append(item)
    valleys["vbm"].sort(key=lambda x: (-x["energy"], x["k_index"], x["band_index"]))
    valleys["cbm"].sort(key=lambda x: (x["energy"], x["k_index"], x["band_index"]))
    return {
        "vbm": vbm,
        "cbm": cbm,
        "gap_eV": float(cbm["energy"] - vbm["energy"]),
        "equivalent_valleys": valleys,
    }


def write_explicit_kpoints(path, target, direction, rec, delta_k, points_each_side):
    axis = DIRECTION_TO_AXIS[direction]
    rec_norm = float(np.linalg.norm(rec[axis]))
    if rec_norm <= 0:
        raise RuntimeError(f"invalid reciprocal vector norm for {direction}")
    step_frac = delta_k / rec_norm
    center = np.array(target["kpoint"], dtype=float)
    offsets = list(range(-points_each_side, points_each_side + 1))
    with open(path / "KPOINTS", "w") as f:
        f.write(f"Effective mass local line: {target['carrier']} {target['valley_label']} {direction}\n")
        f.write(f"{len(offsets)}\n")
        f.write("Reciprocal\n")
        for offset in offsets:
            kpt = center.copy()
            kpt[axis] += offset * step_frac
            kpt[2] = 0.0
            f.write(f"{kpt[0]: .10f} {kpt[1]: .10f} {kpt[2]: .10f} 1.0\n")
    target["offsets"] = offsets
    target["signed_k_inv_angstrom"] = [float(x * delta_k) for x in offsets]


def prepare_runs():
    settings = load_settings()
    edge_dir = Path(settings["edge_source_dir"])
    edge_data = parse_eigenval(edge_dir)
    edges = find_band_edges(
        edge_data,
        float(settings["occupation_threshold"]),
        float(settings["valley_tolerance_meV"]),
    )
    if edges["gap_eV"] < float(settings["min_gap_eV"]):
        raise RuntimeError(
            f"band gap {edges['gap_eV']:.6f} eV is below min_gap_eV; "
            "effective masses are not reliable for metallic/near-metallic systems"
        )

    Path("00_edge_source").mkdir(exist_ok=True)
    with open("00_edge_source/band_edge.yaml", "w") as f:
        yaml.safe_dump(edges, f, sort_keys=False)

    opt_contcar = Path(settings["optimized_contcar"])
    charge_parent = Path(settings["charge_parent_dir"])
    if not opt_contcar.exists():
        raise FileNotFoundError(f"missing optimized CONTCAR: {opt_contcar}")
    parent_chgcar = charge_parent / "CHGCAR"
    if not parent_chgcar.exists() or parent_chgcar.stat().st_size == 0:
        raise FileNotFoundError(f"missing parent CHGCAR: {parent_chgcar}")

    rec = reciprocal_lattice(opt_contcar)
    carriers = settings["carriers"]
    directions = settings["directions"]
    max_valleys = int(settings["max_valleys"])
    targets = []
    for carrier in carriers:
        edge_key = "cbm" if carrier == "electron" else "vbm"
        valleys = edges["equivalent_valleys"][edge_key][:max_valleys]
        for valley_index, valley in enumerate(valleys, start=1):
            for direction in directions:
                if direction not in DIRECTION_TO_AXIS:
                    raise RuntimeError(f"unsupported 2D EM direction: {direction}")
                run_dir = Path(f"{edge_key}_v{valley_index}_{direction}")
                if run_dir.exists():
                    shutil.rmtree(run_dir)
                run_dir.mkdir()
                shutil.copy2(opt_contcar, run_dir / "POSCAR")
                shutil.copy2("POTCAR", run_dir / "POTCAR")
                shutil.copy2("INCAR", run_dir / "INCAR")
                shutil.copy2(parent_chgcar, run_dir / "CHGCAR")
                target = {
                    **valley,
                    "carrier": carrier,
                    "edge": edge_key,
                    "direction": direction,
                    "valley_index": valley_index,
                    "valley_label": f"v{valley_index}",
                    "run_dir": str(run_dir),
                }
                write_explicit_kpoints(
                    run_dir,
                    target,
                    direction,
                    rec,
                    float(settings["delta_k"]),
                    int(settings["points_each_side"]),
                )
                with open(run_dir / "em_target.yaml", "w") as f:
                    yaml.safe_dump(target, f, sort_keys=False)
                targets.append(target)

    with open("em_runs.txt", "w") as f:
        for target in targets:
            f.write(target["run_dir"] + "\n")
    with open("em_runs.yaml", "w") as f:
        yaml.safe_dump({"targets": targets}, f, sort_keys=False)


def fit_target(target, settings):
    run_dir = Path(target["run_dir"])
    data = parse_eigenval(run_dir)
    ispin = min(int(target["spin"]), data["energies"].shape[0] - 1)
    iband = int(target["band_index"])
    energies = data["energies"][ispin, :, iband]
    x_all = np.array(target["signed_k_inv_angstrom"], dtype=float)
    if len(energies) != len(x_all):
        raise RuntimeError(f"k-point count mismatch in {run_dir}")
    windows = sorted(set(int(x) for x in settings["fit_windows"]))
    fits = []
    for window in windows:
        mask = np.abs(x_all) <= window * float(settings["delta_k"]) + 1e-12
        x = x_all[mask]
        y = energies[mask]
        coeff = np.polyfit(x, y, 2)
        pred = np.polyval(coeff, x)
        residual = y - pred
        center_energy = float(y[np.argmin(np.abs(x))])
        fit_energy_window = float(np.max(np.abs(y - center_energy)) * 1000.0)
        ss_res = float(np.sum(residual ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot
        a = float(coeff[0])
        mass = HBAR2_OVER_2M0_EV_A2 / abs(a) if abs(a) > 0 else None
        expected_sign = 1 if target["edge"] == "cbm" else -1
        fits.append({
            "fit_each_side": window,
            "quadratic_a_eV_A2": a,
            "linear_b_eV_A": float(coeff[1]),
            "energy0_eV": float(coeff[2]),
            "effective_mass_m0": float(mass) if mass is not None else None,
            "r2": float(r2),
            "fit_energy_window_meV": fit_energy_window,
            "max_abs_residual_meV": float(np.max(np.abs(residual)) * 1000.0),
            "curvature_sign_ok": bool(a * expected_sign > 0),
            "energy_window_ok": bool(
                fit_energy_window <= float(settings["max_fit_energy_meV"])
            ),
        })
    primary = fits[-1]
    quality_pass = (
        primary["curvature_sign_ok"]
        and primary["energy_window_ok"]
        and primary["max_abs_residual_meV"] <= float(settings["max_residual_meV"])
    )
    return {
        "run_dir": target["run_dir"],
        "carrier": target["carrier"],
        "edge": target["edge"],
        "direction": target["direction"],
        "valley_index": target["valley_index"],
        "source_kpoint": target["kpoint"],
        "source_band_index_1based": int(target["band_index"]) + 1,
        "source_spin_index_1based": int(target["spin"]) + 1,
        "primary_effective_mass_m0": primary["effective_mass_m0"],
        "quality_pass": bool(quality_pass),
        "fits": fits,
    }


def collect_results():
    settings = load_settings()
    with open("em_runs.yaml", "r") as f:
        targets = (yaml.safe_load(f) or {}).get("targets", [])
    results = [fit_target(target, settings) for target in targets]
    Path("results").mkdir(exist_ok=True)

    dos_masses = {}
    for carrier, edge in (("electron", "cbm"), ("hole", "vbm")):
        by_valley = {}
        for item in results:
            if item["carrier"] != carrier:
                continue
            by_valley.setdefault(item["valley_index"], {})[item["direction"]] = item
        for valley_index, dirs in by_valley.items():
            if "a" in dirs and "b" in dirs:
                ma = dirs["a"]["primary_effective_mass_m0"]
                mb = dirs["b"]["primary_effective_mass_m0"]
                if ma is not None and mb is not None:
                    dos_masses[f"{edge}_v{valley_index}"] = math.sqrt(ma * mb)

    payload = {
        "method": settings["method"],
        "basis": "in-plane reciprocal-lattice directions a* and b*",
        "z_direction_policy": "disabled for monolayer 2D materials",
        "settings": settings,
        "density_of_states_masses_m0": dos_masses,
        "results": results,
    }
    with open("results/em_summary.yaml", "w") as f:
        yaml.safe_dump(payload, f, sort_keys=False)

    with open("results/em_summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "carrier", "edge", "valley_index", "direction",
            "mass_m0", "quality_pass", "r2", "fit_energy_window_meV",
            "max_abs_residual_meV",
            "curvature_sign_ok", "run_dir",
        ])
        writer.writeheader()
        for item in results:
            primary = item["fits"][-1]
            writer.writerow({
                "carrier": item["carrier"],
                "edge": item["edge"],
                "valley_index": item["valley_index"],
                "direction": item["direction"],
                "mass_m0": item["primary_effective_mass_m0"],
                "quality_pass": item["quality_pass"],
                "r2": primary["r2"],
                "fit_energy_window_meV": primary["fit_energy_window_meV"],
                "max_abs_residual_meV": primary["max_abs_residual_meV"],
                "curvature_sign_ok": primary["curvature_sign_ok"],
                "run_dir": item["run_dir"],
            })


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"prepare-runs", "collect"}:
        raise SystemExit("usage: effective_mass_runtime.py prepare-runs|collect")
    if sys.argv[1] == "prepare-runs":
        prepare_runs()
    else:
        collect_results()


if __name__ == "__main__":
    main()
'''

    def setup_mobility_dir(self, copy_inputs_from=None):
        """Prepare the 2D deformation-potential mobility manager directory."""
        src_poscar = os.path.join(
            self.project.project_dir, "00_input", "POSCAR")
        shutil.copy(src_poscar, os.path.join(self.work_dir, "POSCAR"))

        if not os.path.exists(os.path.join(self.work_dir, "POTCAR")):
            self.reuse_optimization_potcar()
        opt_kpoints = os.path.join(self.project.project_dir, "01_opt", "KPOINTS")
        if (not os.path.exists(os.path.join(self.work_dir, "KPOINTS")) and
                os.path.exists(opt_kpoints)):
            shutil.copy2(opt_kpoints, os.path.join(self.work_dir, "KPOINTS"))
        if (not os.path.exists(os.path.join(self.work_dir, "KPOINTS")) or
                not os.path.exists(os.path.join(self.work_dir, "POTCAR"))):
            self.generate_kpoints_and_potcar()
            self.reuse_optimization_potcar()
        potcar_path = os.path.join(self.work_dir, "POTCAR")
        if os.path.exists(potcar_path):
            self._record_potcar_info(potcar_path)

        with open(os.path.join(self.work_dir, "INCAR"), 'w') as f:
            f.write(self.render_incar())

        mobility_settings = self.get_mobility_settings()
        with open(os.path.join(self.work_dir, "mobility_settings.yaml"), "w") as f:
            yaml.dump(mobility_settings, f, default_flow_style=False)
        with open(os.path.join(self.work_dir, "mobility_runtime.py"), "w") as f:
            f.write(self.render_mobility_runtime_script())
        os.chmod(os.path.join(self.work_dir, "mobility_runtime.py"), 0o755)

        provenance_path = self.write_module_provenance(copy_inputs_from)
        with open(provenance_path, "r") as f:
            provenance = yaml.safe_load(f) or {}
        provenance["mobility"] = {
            "method": mobility_settings["method"],
            "model": "2D acoustic-phonon deformation-potential approximation",
            "effective_mass_source": mobility_settings["effective_mass_source"],
            "charge_parent": mobility_settings["charge_parent"],
            "directions": mobility_settings["directions"],
            "carriers": mobility_settings["carriers"],
            "strain_values_percent": mobility_settings["strain_values"],
            "temperature_K": mobility_settings["temperature"],
            "elastic_policy": "fit total energy versus dimensionless strain; do not use 3D VASP stress",
            "relaxation_policy": "strain cell, fix lattice and vacuum, relax internal coordinates only",
        }
        with open(provenance_path, "w") as f:
            yaml.dump(provenance, f, default_flow_style=False)

        sub_content = self.render_mobility_submit_script()
        with open(os.path.join(self.work_dir, "sub.vasp"), 'w') as f:
            f.write(sub_content)
        os.chmod(os.path.join(self.work_dir, "sub.vasp"), 0o755)

        kpoints_summary = write_kpoints_summary(
            self.name,
            os.path.join(self.work_dir, "KPOINTS"),
            os.path.join(self.work_dir, "kpoints_summary.yaml"))
        if kpoints_summary.get("passed") is False:
            errors = "; ".join(kpoints_summary.get("errors", []))
            raise RuntimeError(
                f"{self.module_dir} KPOINTS failed 2D validation: {errors}"
            )

    def get_mobility_settings(self):
        """Return reviewed defaults for 2D deformation-potential mobility."""
        cfg = self.module_params
        directions = cfg.get("directions", ["a", "b"])
        carriers = cfg.get("carriers", ["electron", "hole"])
        strain_values = cfg.get(
            "strain_values", [-1.0, -0.5, 0.0, 0.5, 1.0])
        edge_delta_k = cfg.get(
            "edge_delta_k",
            self.precision_config.get("effective_mass", {}).get("delta_k", 0.005))
        edge_points_each_side = cfg.get(
            "edge_points_each_side",
            self.precision_config.get("effective_mass", {}).get(
                "points_each_side", 5))
        em_source = cfg.get(
            "effective_mass_source",
            os.path.join("11_effective_mass", "results", "em_summary.yaml"))
        if not os.path.isabs(em_source):
            em_source = os.path.join(self.project.project_dir, em_source)
        return {
            "method": cfg.get("method", "pbe"),
            "optimized_contcar": os.path.join(
                self.project.project_dir, "01_opt", "CONTCAR"),
            "charge_parent": cfg.get("charge_parent", "02_scf"),
            "charge_parent_dir": os.path.join(
                self.project.project_dir, cfg.get("charge_parent", "02_scf")),
            "effective_mass_source": em_source,
            "directions": directions,
            "carriers": carriers,
            "strain_values": [float(x) for x in strain_values],
            "temperature": float(cfg.get("temperature", 300.0)),
            "max_valleys": int(cfg.get("max_valleys", 2)),
            "edge_delta_k": float(edge_delta_k),
            "edge_points_each_side": int(edge_points_each_side),
            "elastic_r2_min": float(cfg.get("elastic_r2_min", 0.995)),
            "deformation_potential_r2_min": float(
                cfg.get("deformation_potential_r2_min", 0.98)),
            "emass_quality_required": bool(
                cfg.get("emass_quality_required", True)),
            "max_anisotropy_warning_percent": float(
                cfg.get("max_anisotropy_warning_percent", 10.0)),
            "vacuum_std_warning_eV": float(
                cfg.get("vacuum_std_warning_eV", 0.05)),
            "encut": self.calc_encut(),
            "ncore": self.global_params.get("ncore", 8),
            "ivdw": self.global_params.get("ivdw", 11),
            "lreal": self.global_params.get("lreal", ".FALSE."),
            "addgrid": self.global_params.get("addgrid", ".TRUE."),
            "ediff": cfg.get("ediff", self.global_params.get("ediff", 1e-6)),
            "ediffg": cfg.get("ediffg", self.global_params.get("ediffg", -0.01)),
            "nsw": int(cfg.get("nsw", 80)),
            "ibrion": int(cfg.get("ibrion", 2)),
            "ismear": cfg.get("ismear", self.global_params.get("ismear", 0)),
            "sigma": cfg.get("sigma", self.global_params.get("sigma", 0.05)),
        }

    def render_mobility_submit_script(self):
        """Render the Slurm manager script for 2D mobility."""
        slurm = self.settings.get("slurm", {})
        env = self.settings.get("env", {})
        vasp_exe = self.get_vasp_executable()
        job_name = f"{self.project.name}_{self.name}"
        return f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --ntasks={slurm.get("ntasks", 16)}
#SBATCH --partition={slurm.get("partition", "cpus")}
#SBATCH --output=slurm_%j.log
set -eo pipefail
trap 'echo $? > mobility.exitcode' EXIT

echo "Date              = $(date)"
echo "Hostname          = $(hostname -s)"
echo "Working Directory = $(pwd)"
echo "Number of Nodes Allocated = $SLURM_JOB_NUM_NODES"
echo "Number of Tasks           = $SLURM_JOB_CPUS_PER_NODE"

export PATH={env.get("PATH_MPI", "/home/soft/openmpi/bin")}:$PATH
export LD_LIBRARY_PATH={env.get("LD_MPI", "/home/soft/openmpi/lib")}:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH={env.get("LD_AOCL", "/home/soft/AOCL/5.2.0/gcc/lib_LP64")}:$LD_LIBRARY_PATH
export OMP_NUM_THREADS={env.get("OMP_NUM_THREADS", 1)}

python3 mobility_runtime.py prepare-runs
python3 mobility_runtime.py run-vasp {vasp_exe} "$SLURM_JOB_CPUS_PER_NODE"
python3 mobility_runtime.py collect
echo "Mobility workflow completed at $(date)"
"""

    def render_mobility_runtime_script(self):
        """Return the runtime Python helper used inside 12_mobility."""
        return r'''#!/usr/bin/env python3
import csv
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

DIRECTION_TO_AXIS = {"a": 0, "b": 1}
EDGE_TO_CARRIER = {"cbm": "electron", "vbm": "hole"}
E_CHARGE = 1.602176634e-19
HBAR = 1.054571817e-34
KB = 1.380649e-23
M0 = 9.1093837015e-31


def load_settings():
    with open("mobility_settings.yaml", "r") as f:
        return yaml.safe_load(f) or {}


def read_lattice(poscar):
    lines = Path(poscar).read_text().splitlines()
    scale = float(lines[1].split()[0])
    lattice = np.array([
        [float(x) for x in lines[i].split()[:3]]
        for i in range(2, 5)
    ], dtype=float)
    if scale > 0:
        lattice *= scale
    return lattice


def reciprocal_lattice(poscar):
    lattice = read_lattice(poscar)
    return 2.0 * math.pi * np.linalg.inv(lattice).T


def area_angstrom2(poscar):
    lattice = read_lattice(poscar)
    return float(np.linalg.norm(np.cross(lattice[0], lattice[1])))


def strain_poscar(src, dst, direction, strain_fraction):
    lines = Path(src).read_text().splitlines()
    scale = float(lines[1].split()[0])
    lattice = np.array([
        [float(x) for x in lines[i].split()[:3]]
        for i in range(2, 5)
    ], dtype=float)
    axis = DIRECTION_TO_AXIS[direction]
    lattice[axis] *= (1.0 + strain_fraction)
    out = list(lines)
    out[1] = "1.0"
    for i in range(3):
        vec = lattice[i] * scale
        out[2 + i] = f"  {vec[0]: .12f}  {vec[1]: .12f}  {vec[2]: .12f}"
    Path(dst).write_text("\n".join(out) + "\n")


def strain_label(value):
    sign = "p" if value >= 0 else "m"
    return f"eps_{sign}{abs(value):.2f}".replace(".", "p")


def write_incar(path, settings, mode):
    common = [
        f"SYSTEM  = mobility_{mode}",
        "PREC    = Accurate",
        f"ENCUT   = {settings['encut']}",
        f"NCORE   = {settings['ncore']}",
        f"IVDW    = {settings['ivdw']}",
        f"LREAL   = {settings['lreal']}",
        f"ADDGRID = {settings['addgrid']}",
        f"ISMEAR  = {settings['ismear']}",
        f"SIGMA   = {settings['sigma']}",
        f"EDIFF   = {settings['ediff']}",
    ]
    if mode == "relax":
        lines = common + [
            "ISIF    = 2",
            f"NSW     = {settings['nsw']}",
            f"IBRION  = {settings['ibrion']}",
            f"EDIFFG  = {settings['ediffg']}",
            "LWAVE   = .FALSE.",
            "LCHARG  = .FALSE.",
        ]
    elif mode == "scf":
        lines = common + [
            "NSW     = 0",
            "IBRION  = -1",
            "LWAVE   = .FALSE.",
            "LCHARG  = .TRUE.",
            "LVTOT   = .TRUE.",
            "LVHAR   = .TRUE.",
        ]
    else:
        lines = common + [
            "ICHARG  = 11",
            "ISYM    = 0",
            "LORBIT  = 11",
            "NSW     = 0",
            "IBRION  = -1",
            "LWAVE   = .FALSE.",
            "LCHARG  = .FALSE.",
            "LVTOT   = .TRUE.",
            "LVHAR   = .TRUE.",
        ]
    Path(path).write_text("\n".join(lines) + "\n")


def parse_eigenval(path):
    eigenval = Path(path) / "EIGENVAL"
    if not eigenval.exists():
        raise FileNotFoundError(f"missing EIGENVAL: {eigenval}")
    lines = eigenval.read_text(errors="ignore").splitlines()
    header_idx = None
    nkpts = nbands = None
    for idx, line in enumerate(lines[:12]):
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            nkpts = int(float(parts[-2]))
            nbands = int(float(parts[-1]))
        except ValueError:
            continue
        header_idx = idx
        break
    if header_idx is None:
        raise ValueError(f"cannot parse NKPTS/NBANDS from {eigenval}")
    cursor = header_idx + 1
    kpoints = []
    records = []
    for _ in range(nkpts):
        while cursor < len(lines) and not lines[cursor].split():
            cursor += 1
        kparts = lines[cursor].split()
        kpoints.append([float(kparts[0]), float(kparts[1]), float(kparts[2])])
        cursor += 1
        bands = []
        for _band in range(nbands):
            while cursor < len(lines) and not lines[cursor].split():
                cursor += 1
            parts = lines[cursor].split()
            cursor += 1
            if len(parts) == 3:
                bands.append([(float(parts[1]), float(parts[2]))])
            elif len(parts) >= 5:
                bands.append([
                    (float(parts[1]), float(parts[3])),
                    (float(parts[2]), float(parts[4])),
                ])
            else:
                raise ValueError(f"invalid band line in {eigenval}: {' '.join(parts)}")
        records.append(bands)
    nspin = max(len(band) for krec in records for band in krec)
    energies = np.full((nspin, len(records), nbands), np.nan)
    occs = np.full((nspin, len(records), nbands), np.nan)
    for ik, krec in enumerate(records):
        for ib, band in enumerate(krec):
            for ispin, (energy, occ) in enumerate(band):
                energies[ispin, ik, ib] = energy
                occs[ispin, ik, ib] = occ
    return {
        "kpoints": np.array(kpoints, dtype=float),
        "energies": energies,
        "occupancies": occs,
    }


def write_local_kpoints(path, target, direction, rec, delta_k, points_each_side):
    axis = DIRECTION_TO_AXIS[direction]
    rec_norm = float(np.linalg.norm(rec[axis]))
    if rec_norm <= 0:
        raise RuntimeError(f"invalid reciprocal vector norm for {direction}")
    step_frac = delta_k / rec_norm
    center = np.array(target["source_kpoint"], dtype=float)
    offsets = list(range(-points_each_side, points_each_side + 1))
    with open(Path(path) / "KPOINTS", "w") as f:
        f.write(f"Mobility local edge line: {target['edge']} v{target['valley_index']} {direction}\n")
        f.write(f"{len(offsets)}\n")
        f.write("Reciprocal\n")
        for offset in offsets:
            kpt = center.copy()
            kpt[axis] += offset * step_frac
            kpt[2] = 0.0
            f.write(f"{kpt[0]: .10f} {kpt[1]: .10f} {kpt[2]: .10f} 1.0\n")
    return [float(x * delta_k) for x in offsets]


def load_emass_targets(settings):
    source = Path(settings["effective_mass_source"])
    if not source.exists():
        raise FileNotFoundError(f"missing effective-mass summary: {source}")
    data = yaml.safe_load(source.read_text()) or {}
    targets = []
    for item in data.get("results", []):
        if settings.get("emass_quality_required", True) and not item.get("quality_pass"):
            raise RuntimeError(
                f"effective-mass input failed quality checks: {item.get('run_dir')}"
            )
        if item.get("carrier") not in settings["carriers"]:
            continue
        if item.get("direction") not in settings["directions"]:
            continue
        if int(item.get("valley_index", 1)) > int(settings["max_valleys"]):
            continue
        targets.append({
            "carrier": item["carrier"],
            "edge": item["edge"],
            "direction": item["direction"],
            "valley_index": int(item["valley_index"]),
            "source_kpoint": item["source_kpoint"],
            "band_index": int(item["source_band_index_1based"]) - 1,
            "spin": int(item["source_spin_index_1based"]) - 1,
            "mass_m0": float(item["primary_effective_mass_m0"]),
        })
    if not targets:
        raise RuntimeError("no usable effective-mass targets for mobility")
    return data, targets


def prepare_runs():
    settings = load_settings()
    shutil.rmtree("results", ignore_errors=True)
    for pattern in ("strain_a", "strain_b", "00_inputs"):
        shutil.rmtree(pattern, ignore_errors=True)
    emass_data, targets = load_emass_targets(settings)
    opt_contcar = Path(settings["optimized_contcar"])
    charge_parent = Path(settings["charge_parent_dir"])
    for required in (opt_contcar, Path("POTCAR"), Path("KPOINTS")):
        if not required.exists():
            raise FileNotFoundError(f"missing required input: {required}")
    if not (charge_parent / "CHGCAR").exists():
        raise FileNotFoundError(f"missing reference CHGCAR: {charge_parent / 'CHGCAR'}")

    Path("00_inputs").mkdir(exist_ok=True)
    shutil.copy2(opt_contcar, "00_inputs/opt_CONTCAR")
    shutil.copy2(charge_parent / "CHGCAR", "00_inputs/scf_CHGCAR")
    shutil.copy2(settings["effective_mass_source"], "00_inputs/em_summary.yaml")

    rec = reciprocal_lattice(opt_contcar)
    runs = []
    for direction in settings["directions"]:
        for strain_percent in settings["strain_values"]:
            strain_fraction = float(strain_percent) / 100.0
            label = strain_label(float(strain_percent))
            base = Path(f"strain_{direction}") / label
            relax_dir = base / "relax"
            scf_dir = base / "scf"
            if base.exists():
                shutil.rmtree(base)
            relax_dir.mkdir(parents=True)
            scf_dir.mkdir(parents=True)

            strain_poscar(opt_contcar, relax_dir / "POSCAR", direction, strain_fraction)
            shutil.copy2("POTCAR", relax_dir / "POTCAR")
            shutil.copy2("KPOINTS", relax_dir / "KPOINTS")
            write_incar(relax_dir / "INCAR", settings, "relax")
            shutil.copy2("POTCAR", scf_dir / "POTCAR")
            shutil.copy2("KPOINTS", scf_dir / "KPOINTS")
            write_incar(scf_dir / "INCAR", settings, "scf")

            edge_runs = []
            for target in targets:
                if target["direction"] != direction:
                    continue
                edge_dir = base / (
                    f"{target['edge']}_v{target['valley_index']}_{target['direction']}")
                edge_dir.mkdir()
                shutil.copy2("POTCAR", edge_dir / "POTCAR")
                write_incar(edge_dir / "INCAR", settings, "edge")
                signed_k = write_local_kpoints(
                    edge_dir, target, target["direction"], rec,
                    float(settings["edge_delta_k"]),
                    int(settings["edge_points_each_side"]))
                edge_target = {
                    **target,
                    "run_dir": str(edge_dir),
                    "signed_k_inv_angstrom": signed_k,
                }
                with open(edge_dir / "mobility_edge_target.yaml", "w") as f:
                    yaml.safe_dump(edge_target, f, sort_keys=False)
                edge_runs.append(edge_target)

            runs.append({
                "direction": direction,
                "strain_percent": float(strain_percent),
                "strain_fraction": strain_fraction,
                "relax_dir": str(relax_dir),
                "scf_dir": str(scf_dir),
                "edge_runs": edge_runs,
            })

    with open("mobility_runs.yaml", "w") as f:
        yaml.safe_dump({
            "settings": settings,
            "emass_density_of_states_masses_m0": emass_data.get(
                "density_of_states_masses_m0", {}),
            "runs": runs,
        }, f, sort_keys=False)


def run_vasp_in_dir(run_dir, vasp_exe, ntasks):
    run_dir = Path(run_dir)
    print(f"Starting VASP in {run_dir}")
    with open(run_dir / "vasp.stdout", "w") as out, open(run_dir / "vasp.stderr", "w") as err:
        result = subprocess.run(
            ["mpirun", "-np", str(ntasks), vasp_exe],
            cwd=run_dir, stdout=out, stderr=err)
    (run_dir / "vasp.exitcode").write_text(str(result.returncode) + "\n")
    if result.returncode != 0:
        raise RuntimeError(f"VASP failed in {run_dir} with exit code {result.returncode}")
    return result.returncode


def run_vasp(vasp_exe, ntasks):
    plan = yaml.safe_load(Path("mobility_runs.yaml").read_text()) or {}
    for item in plan.get("runs", []):
        relax_dir = Path(item["relax_dir"])
        scf_dir = Path(item["scf_dir"])
        run_vasp_in_dir(relax_dir, vasp_exe, ntasks)
        contcar = relax_dir / "CONTCAR"
        if not contcar.exists() or contcar.stat().st_size == 0:
            raise RuntimeError(f"missing relaxed CONTCAR: {contcar}")
        shutil.copy2(contcar, scf_dir / "POSCAR")
        run_vasp_in_dir(scf_dir, vasp_exe, ntasks)
        chgcar = scf_dir / "CHGCAR"
        if not chgcar.exists() or chgcar.stat().st_size == 0:
            raise RuntimeError(f"missing SCF CHGCAR: {chgcar}")
        for target in item.get("edge_runs", []):
            edge_dir = Path(target["run_dir"])
            scf_structure = scf_dir / "CONTCAR"
            if not scf_structure.exists() or scf_structure.stat().st_size == 0:
                scf_structure = scf_dir / "POSCAR"
            shutil.copy2(scf_structure, edge_dir / "POSCAR")
            shutil.copy2(chgcar, edge_dir / "CHGCAR")
            run_vasp_in_dir(edge_dir, vasp_exe, ntasks)


def outcar_energy(path):
    outcar = Path(path) / "OUTCAR"
    text = outcar.read_text(errors="ignore")
    matches = re.findall(r"free\s+energy\s+TOTEN\s+=\s+([-+0-9.Ee]+)", text)
    if not matches:
        raise RuntimeError(f"cannot parse TOTEN from {outcar}")
    return float(matches[-1])


def fit_r2(y, pred):
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return 1.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot


def fit_edge_energy(target):
    data = parse_eigenval(target["run_dir"])
    ispin = min(int(target["spin"]), data["energies"].shape[0] - 1)
    iband = int(target["band_index"])
    energies = data["energies"][ispin, :, iband]
    x = np.array(target["signed_k_inv_angstrom"], dtype=float)
    coeff = np.polyfit(x, energies, 2)
    pred = np.polyval(coeff, x)
    return {
        "edge_energy_raw_eV": float(coeff[2]),
        "quadratic_a_eV_A2": float(coeff[0]),
        "r2": float(fit_r2(energies, pred)),
        "max_abs_residual_meV": float(np.max(np.abs(energies - pred)) * 1000.0),
    }


def parse_locpot_vacuum(path):
    locpot = Path(path) / "LOCPOT"
    if not locpot.exists():
        raise FileNotFoundError(f"missing LOCPOT: {locpot}")
    lines = locpot.read_text(errors="ignore").splitlines()
    try:
        counts = [int(x) for x in lines[6].split()]
        natoms = sum(counts)
        coord_start = 8
        if lines[7].strip().lower().startswith("s"):
            coord_start = 9
    except Exception as exc:
        raise RuntimeError(f"cannot parse LOCPOT header: {locpot}") from exc
    idx = coord_start + natoms
    while idx < len(lines) and not lines[idx].split():
        idx += 1
    if idx >= len(lines):
        raise RuntimeError(f"cannot find LOCPOT grid dimensions: {locpot}")
    grid = [int(x) for x in lines[idx].split()[:3]]
    nx, ny, nz = grid
    needed = nx * ny * nz
    values = []
    idx += 1
    while idx < len(lines) and len(values) < needed:
        for token in lines[idx].split():
            try:
                values.append(float(token))
            except ValueError:
                pass
        idx += 1
    if len(values) < needed:
        raise RuntimeError(f"LOCPOT has too few grid values: {locpot}")
    arr = np.array(values[:needed], dtype=float).reshape((nz, ny, nx))
    avg_z = arr.mean(axis=(1, 2))
    window = max(1, int(round(0.1 * nz)))
    order = np.argsort(avg_z)[-window:]
    plateau = avg_z[order]
    return {
        "vacuum_level_eV": float(np.median(plateau)),
        "vacuum_std_eV": float(np.std(plateau)),
        "grid": grid,
    }


def collect_results():
    settings = load_settings()
    plan = yaml.safe_load(Path("mobility_runs.yaml").read_text()) or {}
    emass = yaml.safe_load(Path(settings["effective_mass_source"]).read_text()) or {}
    dos_masses = emass.get("density_of_states_masses_m0", {})
    runs = plan.get("runs", [])
    area0_m2 = area_angstrom2(settings["optimized_contcar"]) * 1e-20

    records = []
    for item in runs:
        vacuum = parse_locpot_vacuum(item["scf_dir"])
        if vacuum["vacuum_std_eV"] > settings["vacuum_std_warning_eV"]:
            warnings.append(
                f"vacuum plateau std for {item['direction']} "
                f"{item['strain_percent']}% is {vacuum['vacuum_std_eV']:.4f} eV")
        edge_values = []
        for target in item.get("edge_runs", []):
            fit = fit_edge_energy(target)
            edge_values.append({
                **target,
                **fit,
                "edge_energy_vac_eV": (
                    fit["edge_energy_raw_eV"] - vacuum["vacuum_level_eV"]
                ),
            })
        records.append({
            "direction": item["direction"],
            "strain_percent": item["strain_percent"],
            "strain_fraction": item["strain_fraction"],
            "energy_eV": outcar_energy(item["scf_dir"]),
            **vacuum,
            "edge_values": edge_values,
        })

    elastic = {}
    mobility = []
    warnings = []
    for direction in settings["directions"]:
        d_records = sorted(
            [r for r in records if r["direction"] == direction],
            key=lambda x: x["strain_fraction"])
        eps = np.array([r["strain_fraction"] for r in d_records], dtype=float)
        energy = np.array([r["energy_eV"] for r in d_records], dtype=float)
        coeff = np.polyfit(eps, energy, 2)
        pred = np.polyval(coeff, eps)
        r2 = fit_r2(energy, pred)
        c2d = 2.0 * float(coeff[0]) * E_CHARGE / area0_m2
        elastic[direction] = {
            "quadratic_a_eV": float(coeff[0]),
            "C2D_N_per_m": float(c2d),
            "r2": float(r2),
            "quality_pass": bool(c2d > 0 and r2 >= settings["elastic_r2_min"]),
        }
        if c2d <= 0:
            raise RuntimeError(f"C2D for {direction} is non-positive")
        if r2 < settings["elastic_r2_min"]:
            warnings.append(f"elastic fit R2 for {direction} is {r2:.6f}")

        grouped = {}
        for r in d_records:
            for edge in r["edge_values"]:
                key = (edge["carrier"], edge["edge"], edge["valley_index"])
                grouped.setdefault(key, []).append((r["strain_fraction"], edge))
        for (carrier, edge_name, valley_index), values in grouped.items():
            values.sort(key=lambda x: x[0])
            x = np.array([v[0] for v in values], dtype=float)
            y = np.array([v[1]["edge_energy_vac_eV"] for v in values], dtype=float)
            line = np.polyfit(x, y, 1)
            pred_y = np.polyval(line, x)
            edge_r2 = fit_r2(y, pred_y)
            if edge_r2 < settings["deformation_potential_r2_min"]:
                warnings.append(
                    f"deformation-potential fit R2 for {carrier} v{valley_index} "
                    f"along {direction} is {edge_r2:.6f}")
            mass_items = [
                item for item in emass.get("results", [])
                if item.get("carrier") == carrier
                and item.get("direction") == direction
                and int(item.get("valley_index", 1)) == int(valley_index)
            ]
            if not mass_items:
                warnings.append(f"missing transport mass for {carrier} v{valley_index} {direction}")
                continue
            m_transport = float(mass_items[0]["primary_effective_mass_m0"])
            md_key = f"{edge_name}_v{valley_index}"
            md = float(dos_masses.get(md_key, m_transport))
            e1_joule = float(line[0]) * E_CHARGE
            mu_m2_vs = (
                E_CHARGE * HBAR ** 3 * c2d /
                (KB * float(settings["temperature"]) *
                 m_transport * md * M0 ** 2 * e1_joule ** 2)
            )
            mobility.append({
                "carrier": carrier,
                "edge": edge_name,
                "valley_index": int(valley_index),
                "direction": direction,
                "m_transport_m0": m_transport,
                "m_dos_m0": md,
                "C2D_N_per_m": float(c2d),
                "E1_eV": float(line[0]),
                "E1_abs_eV": float(abs(line[0])),
                "edge_fit_r2": float(edge_r2),
                "mobility_m2_per_Vs": float(mu_m2_vs),
                "mobility_cm2_per_Vs": float(mu_m2_vs * 1e4),
                "quality_pass": bool(
                    elastic[direction]["quality_pass"] and
                    edge_r2 >= settings["deformation_potential_r2_min"]),
            })

    Path("results").mkdir(exist_ok=True)
    quality_pass_count = sum(1 for item in mobility if item.get("quality_pass"))
    status = "complete" if quality_pass_count == len(mobility) and not warnings else "check_required"
    payload = {
        "status": status,
        "method": settings["method"],
        "model": "intrinsic acoustic-phonon-limited mobility from 2D deformation-potential theory",
        "temperature_K": settings["temperature"],
        "area0_m2": area0_m2,
        "n_mobility_targets": len(mobility),
        "n_quality_pass": quality_pass_count,
        "settings": settings,
        "elastic": elastic,
        "mobility": mobility,
        "strain_records": records,
        "warnings": warnings,
    }
    with open("results/mobility_summary.yaml", "w") as f:
        yaml.safe_dump(payload, f, sort_keys=False)
    with open("results/mobility_summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "carrier", "edge", "valley_index", "direction",
            "m_transport_m0", "m_dos_m0", "C2D_N_per_m", "E1_eV",
            "edge_fit_r2", "mobility_cm2_per_Vs", "quality_pass",
        ])
        writer.writeheader()
        for item in mobility:
            writer.writerow({key: item.get(key) for key in writer.fieldnames})
    with open("results/mobility_points.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "direction", "strain_percent", "strain_fraction",
            "energy_eV", "vacuum_level_eV", "vacuum_std_eV",
            "carrier", "edge", "valley_index", "band_index_1based",
            "spin_index_1based", "edge_energy_raw_eV", "edge_energy_vac_eV",
            "edge_fit_r2", "edge_fit_residual_meV", "run_dir",
        ])
        writer.writeheader()
        for record in records:
            for edge in record["edge_values"]:
                writer.writerow({
                    "direction": record["direction"],
                    "strain_percent": record["strain_percent"],
                    "strain_fraction": record["strain_fraction"],
                    "energy_eV": record["energy_eV"],
                    "vacuum_level_eV": record["vacuum_level_eV"],
                    "vacuum_std_eV": record["vacuum_std_eV"],
                    "carrier": edge["carrier"],
                    "edge": edge["edge"],
                    "valley_index": edge["valley_index"],
                    "band_index_1based": edge["band_index"] + 1,
                    "spin_index_1based": edge["spin"] + 1,
                    "edge_energy_raw_eV": edge["edge_energy_raw_eV"],
                    "edge_energy_vac_eV": edge["edge_energy_vac_eV"],
                    "edge_fit_r2": edge["r2"],
                    "edge_fit_residual_meV": edge["max_abs_residual_meV"],
                    "run_dir": edge["run_dir"],
                })


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: mobility_runtime.py prepare-runs|run-vasp|collect")
    if sys.argv[1] == "prepare-runs":
        prepare_runs()
    elif sys.argv[1] == "run-vasp":
        if len(sys.argv) != 4:
            raise SystemExit("usage: mobility_runtime.py run-vasp VASP_EXE NTASKS")
        run_vasp(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "collect":
        collect_results()
    else:
        raise SystemExit(f"unknown command: {sys.argv[1]}")


if __name__ == "__main__":
    main()
'''

    def setup_phonopy_fd_dir(self, copy_inputs_from=None):
        """Prepare the finite-displacement phonopy manager directory."""
        src_poscar = os.path.join(
            self.project.project_dir, "00_input", "POSCAR")
        shutil.copy(src_poscar, os.path.join(self.work_dir, "POSCAR"))

        if not os.path.exists(os.path.join(self.work_dir, "POTCAR")):
            self.reuse_optimization_potcar()
        if (not os.path.exists(os.path.join(self.work_dir, "KPOINTS")) or
                not os.path.exists(os.path.join(self.work_dir, "POTCAR"))):
            self.generate_kpoints_and_potcar()
            self.reuse_optimization_potcar()
        if os.path.exists(os.path.join(self.work_dir, "POTCAR")):
            self._record_potcar_info(os.path.join(self.work_dir, "POTCAR"))

        fd_settings = self.get_phonopy_fd_settings()
        mesh_info = self.write_supercell_kpoints(fd_settings["dim"])

        incar_content = self.render_incar()
        with open(os.path.join(self.work_dir, "INCAR"), 'w') as f:
            f.write(incar_content)

        provenance_path = self.write_module_provenance(copy_inputs_from)
        with open(provenance_path, "r") as f:
            provenance = yaml.safe_load(f) or {}
        provenance["phonopy_fd"] = {
            **fd_settings,
            **mesh_info,
            "method": "finite_displacement",
            "vacuum_axis_policy": "c-axis fixed; supercell dim_z forced to 1",
        }
        with open(provenance_path, "w") as f:
            yaml.dump(provenance, f, default_flow_style=False)
        with open(os.path.join(self.work_dir, "phonopy_fd_settings.yaml"), "w") as f:
            yaml.dump(provenance["phonopy_fd"], f, default_flow_style=False)

        sub_content = self.render_phonopy_fd_submit_script(fd_settings)
        with open(os.path.join(self.work_dir, "sub.vasp"), 'w') as f:
            f.write(sub_content)
        os.chmod(os.path.join(self.work_dir, "sub.vasp"), 0o755)

        kpoints_summary = write_kpoints_summary(
            self.name,
            os.path.join(self.work_dir, "KPOINTS"),
            os.path.join(self.work_dir, "kpoints_summary.yaml"))
        if kpoints_summary.get("passed") is False:
            errors = "; ".join(kpoints_summary.get("errors", []))
            raise RuntimeError(
                f"{self.module_dir} KPOINTS failed 2D validation: {errors}"
            )

    def generate_potcar(self):
        """Generate POTCAR using vaspkit task 103."""
        vaspkit_exe = self.settings.get("vaspkit", {}).get(
            "executable",
            "/home/lilin/software/vaspkit.1.3.1/bin/vaspkit")

        cwd = os.getcwd()
        os.chdir(self.work_dir)
        try:
            result = subprocess.run(
                [vaspkit_exe, "-task", "103"],
                capture_output=True, text=True, timeout=120)
            if "Illegal Argument" in result.stdout + result.stderr:
                result = subprocess.run(
                    [vaspkit_exe],
                    input="103\n",
                    capture_output=True, text=True, timeout=120)
        finally:
            os.chdir(cwd)

        potcar_path = os.path.join(self.work_dir, "POTCAR")
        if not os.path.exists(potcar_path):
            raise RuntimeError(
                f"POTCAR generation failed in {self.work_dir}")

        self._record_potcar_info(potcar_path)

    def _record_potcar_info(self, potcar_path):
        """Extract and record POTCAR version information."""
        info = {}
        with open(potcar_path, 'r') as f:
            content = f.read()
        titels = re.findall(
            r'TITEL\s*=\s*PAW_PBE\s+(\S+)\s+(\S+)', content)
        enmaxs = re.findall(r'ENMAX\s*=\s*([\d.]+)', content)
        zvals = re.findall(r'ZVAL\s*=\s*([\d.]+)', content)

        info["elements"] = []
        for i, titel in enumerate(titels):
            info["elements"].append({
                "symbol": titel[0],
                "date": titel[1],
                "enmax": float(enmaxs[i]) if i < len(enmaxs) else None,
                "zval": float(zvals[i]) if i < len(zvals) else None,
            })
        real_enmaxs = [
            item["enmax"] for item in info["elements"]
            if item["enmax"] is not None
        ]
        if real_enmaxs:
            factor = self.global_params.get("encut_factor", 1.5)
            info["max_enmax"] = max(real_enmaxs)
            info["encut_factor"] = factor
            info["recommended_encut"] = int(max(real_enmaxs) * factor)

        info_path = os.path.join(self.work_dir, "potcar_info.yaml")
        with open(info_path, 'w') as f:
            yaml.dump(info, f)

    # ---- Status checks ----

    def is_completed(self):
        """Check if calculation has completed successfully."""
        outcar = os.path.join(self.work_dir, "OUTCAR")
        if not os.path.exists(outcar):
            return False
        with open(outcar, 'r', errors='ignore') as f:
            content = f.read()
        return ("General timing and accounting informations"
                in content)

    def get_convergence_status(self):
        """Check convergence status from OUTCAR."""
        outcar = os.path.join(self.work_dir, "OUTCAR")
        if not os.path.exists(outcar):
            return "NOT_STARTED"
        with open(outcar, 'r', errors='ignore') as f:
            content = f.read()
        if "reached required accuracy" in content:
            return "CONVERGED"
        if "General timing and accounting" in content:
            return "COMPLETED_BUT_CHECK"
        return "INCOMPLETE"

    def get_energy(self):
        """Extract final total energy (eV) from OUTCAR."""
        outcar = os.path.join(self.work_dir, "OUTCAR")
        if not os.path.exists(outcar):
            return None
        last_line = None
        with open(outcar, 'r', errors='ignore') as f:
            for line in f:
                if "free  energy   TOTEN" in line:
                    last_line = line
        if last_line:
            try:
                return float(last_line.strip().split()[-2])
            except (ValueError, IndexError):
                pass
        return None

    def get_fermi_level(self):
        """Extract Fermi level (eV) from OUTCAR."""
        outcar = os.path.join(self.work_dir, "OUTCAR")
        if not os.path.exists(outcar):
            return None
        with open(outcar, 'r', errors='ignore') as f:
            for line in f:
                if "E-fermi" in line:
                    try:
                        return float(line.strip().split()[2])
                    except (IndexError, ValueError):
                        pass
        return None
