#!/usr/bin/env python3
"""Tests for parameter merging: module-level overrides of global settings.

All tests use stdlib only. No VaspModule instantiation (requires POSCAR/POTCAR
files on disk). Parameter merge logic is tested directly on dicts.
"""

import os
import sys
import unittest
import tempfile

# Add parent to path for importing modules.base functions
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================================
# Helpers: replicate the merge logic from VaspModule.get_incar_vars()
# ============================================================

def _merge(g, m, key, default):
    """Module-level param overrides global param: m[key] > g[key] > default."""
    return m.get(key, g.get(key, default))


def _merge_encut_factor(g, m):
    """Replicate calc_encut factor resolution."""
    return m.get("encut_factor", g.get("encut_factor", 1.5))


def _make_g():
    """Return a representative global params dict."""
    return {
        "encut_factor": 1.5,
        "ediff": 1.0E-06,
        "ediffg": -0.01,
        "ismear": 0,
        "sigma": 0.05,
        "nelm": 90,
        "nelmin": 6,
        "ncore": 8,
        "ivdw": 11,
        "lreal": ".FALSE.",
        "addgrid": ".TRUE.",
        "ispin": 1,
        "lwave": ".FALSE.",
        "lcharg": ".FALSE.",
    }


# ============================================================
# Parameter merge tests
# ============================================================

class TestParameterMerge(unittest.TestCase):
    """Tests that module-level settings override global settings."""

    def test_phonopy_ediff_overrides_global_ediff(self):
        """phonopy.ediff=1E-08 overrides global.ediff=1E-06."""
        g = _make_g()
        m = {"ediff": 1.0E-08}
        self.assertEqual(_merge(g, m, "ediff", 1.0E-06), 1.0E-08)

    def test_aimd_encut_factor_overrides_global(self):
        """aimd.encut_factor=1.3 overrides global.encut_factor=1.5."""
        g = _make_g()
        m = {"encut_factor": 1.3}
        self.assertEqual(_merge_encut_factor(g, m), 1.3)

    def test_module_sigma_overrides_global_sigma(self):
        g = _make_g()
        m = {"sigma": 0.2}
        self.assertEqual(_merge(g, m, "sigma", 0.1), 0.2)

    def test_module_nelm_overrides_global_nelm(self):
        g = _make_g()
        m = {"nelm": 200}
        self.assertEqual(_merge(g, m, "nelm", 90), 200)

    def test_module_lwave_overrides_global_lwave(self):
        g = _make_g()
        m = {"lwave": ".TRUE."}
        self.assertEqual(_merge(g, m, "lwave", ".FALSE."), ".TRUE.")

    def test_fallback_to_global_when_module_missing(self):
        g = _make_g()
        m = {}  # no module-specific ediff
        self.assertEqual(_merge(g, m, "ediff", 1.0E-06), 1.0E-06)

    def test_ediffg_override(self):
        g = _make_g()
        m = {"ediffg": -0.005}
        self.assertEqual(_merge(g, m, "ediffg", -0.01), -0.005)

    def test_multiple_overrides_simultaneously(self):
        g = _make_g()
        m = {"ediff": 1.0E-08, "sigma": 0.02, "nelm": 200, "ismear": -5}
        self.assertEqual(_merge(g, m, "ediff", 1.0E-06), 1.0E-08)
        self.assertEqual(_merge(g, m, "sigma", 0.05), 0.02)
        self.assertEqual(_merge(g, m, "nelm", 90), 200)
        self.assertEqual(_merge(g, m, "ismear", 0), -5)

    def test_ismear_override(self):
        g = _make_g()
        m = {"ismear": -5}
        self.assertEqual(_merge(g, m, "ismear", 0), -5)

    def test_lcharg_override(self):
        g = _make_g()
        m = {"lcharg": ".TRUE."}
        self.assertEqual(_merge(g, m, "lcharg", ".FALSE."), ".TRUE.")


# ============================================================
# Material type tests
# ============================================================

class TestMaterialType(unittest.TestCase):
    """Tests for material-type detection."""

    def _write_poscar(self, path, elements, counts, lattice_vectors=None,
                      selective=False, coord_mode="Direct"):
        lines = ["test_poscar", "1.0"]
        for v in (lattice_vectors or [
            [3.0, 0.0, 0.0],
            [0.0, 3.0, 0.0],
            [0.0, 0.0, 20.0],
        ]):
            lines.append(f"  {v[0]:.8f}  {v[1]:.8f}  {v[2]:.8f}")
        lines.append("  ".join(elements))
        lines.append("  ".join(str(c) for c in counts))
        if selective:
            lines.append("Selective dynamics")
        lines.append(coord_mode)
        natoms = sum(counts)
        for i in range(natoms):
            z = i * 0.3 % 1.0
            lines.append(f"  0.33333333  0.66666667  {z:.8f}")
        with open(path, 'w') as f:
            f.write("\n".join(lines) + "\n")

    def test_detect_monolayer_by_heuristic(self):
        from modules.base import detect_material_type
        path = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode='w', suffix='_POSCAR', delete=False) as f:
                self._write_poscar(f.name, ["Mo", "S"], [1, 2])
                path = f.name
            result = detect_material_type(path)
            self.assertEqual(result, "monolayer")
        finally:
            if path and os.path.exists(path):
                os.unlink(path)

    def test_detect_heterojunction_by_heuristic(self):
        from modules.base import detect_material_type
        path = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode='w', suffix='_POSCAR', delete=False) as f:
                self._write_poscar(f.name, ["Mo", "S", "Se", "W"], [1, 2, 2, 1])
                path = f.name
            result = detect_material_type(path)
            self.assertEqual(result, "heterojunction")
        finally:
            if path and os.path.exists(path):
                os.unlink(path)

    def test_material_type_cli_flag(self):
        import argparse
        parser = argparse.ArgumentParser()
        subs = parser.add_subparsers(dest="command")
        p = subs.add_parser("new")
        p.add_argument("project_name")
        p.add_argument("--poscar", required=True)
        p.add_argument("--material-type", choices=["monolayer", "heterojunction"])
        p.add_argument("--precision", choices=["standard", "quick"], default="standard")
        ns = parser.parse_args(
            ["new", "test", "--poscar", "POSCAR", "--material-type", "monolayer"])
        self.assertEqual(ns.material_type, "monolayer")


# ============================================================
# KPOINTS validation tests (stdlib only)
# ============================================================

class TestKpointsValidation(unittest.TestCase):
    """Tests for 2D KPOINTS validation helpers."""

    def _write_regular_kpoints(self, path, nx, ny, nz):
        content = (
            "Regular KPOINTS\n"
            "0\n"
            "Gamma\n"
            f"{nx} {ny} {nz}\n"
            "0 0 0\n"
        )
        with open(path, 'w') as f:
            f.write(content)

    def _write_line_mode_kpoints(self, path, kpoints):
        lines = [
            "Line-mode KPOINTS for band structure",
            str(len(kpoints)),
            "Reciprocal",
        ]
        for kp in kpoints:
            lines.append(f"  {kp[0]:.8f}  {kp[1]:.8f}  {kp[2]:.8f}  1.0")
        lines.append("")
        with open(path, 'w') as f:
            f.write("\n".join(lines))

    def _write_placeholder_kpoints(self, path):
        content = (
            "KPOINTS generated at job runtime by VASPKIT 302\n"
            "0\n"
            "Line-mode placeholder\n"
            "# sub.vasp will run `(echo 302) | vaspkit` and copy "
            "KPATH.in to KPOINTS before VASP starts.\n"
        )
        with open(path, 'w') as f:
            f.write(content)

    # ---- Regular mesh ----

    def test_regular_mesh_nkz_1_passes(self):
        from modules.base import validate_kpoints_2d_regular
        path = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode='w', suffix='_KPOINTS', delete=False) as f:
                self._write_regular_kpoints(f.name, 6, 6, 1)
                path = f.name
            result = validate_kpoints_2d_regular(path)
            self.assertTrue(result["passed"], f"Expected pass, got: {result}")
            self.assertEqual(result["mesh"], [6, 6, 1])
        finally:
            if path and os.path.exists(path):
                os.unlink(path)

    def test_regular_mesh_nkz_gt_1_fails(self):
        from modules.base import validate_kpoints_2d_regular
        path = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode='w', suffix='_KPOINTS', delete=False) as f:
                self._write_regular_kpoints(f.name, 6, 6, 2)
                path = f.name
            result = validate_kpoints_2d_regular(path)
            self.assertFalse(result["passed"],
                             f"Expected failure for Nkz=2, got: {result}")
        finally:
            if path and os.path.exists(path):
                os.unlink(path)

    # ---- Line mode ----

    def test_line_mode_all_kz_zero_passes(self):
        from modules.base import validate_kpoints_2d_line_mode
        kpoints = [
            (0.0, 0.0, 0.0),
            (0.5, 0.0, 0.0),
            (0.3333, 0.3333, 0.0),
            (0.0, 0.0, 0.0),
        ]
        path = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode='w', suffix='_KPOINTS', delete=False) as f:
                self._write_line_mode_kpoints(f.name, kpoints)
                path = f.name
            result = validate_kpoints_2d_line_mode(path)
            self.assertTrue(result["passed"], f"Expected pass, got: {result}")
        finally:
            if path and os.path.exists(path):
                os.unlink(path)

    def test_line_mode_nonzero_kz_fails(self):
        from modules.base import validate_kpoints_2d_line_mode
        kpoints = [
            (0.0, 0.0, 0.0),
            (0.5, 0.0, 0.01),
            (0.3333, 0.3333, 0.0),
        ]
        path = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode='w', suffix='_KPOINTS', delete=False) as f:
                self._write_line_mode_kpoints(f.name, kpoints)
                path = f.name
            result = validate_kpoints_2d_line_mode(path)
            self.assertFalse(result["passed"],
                             f"Expected failure for nonzero kz, got: {result}")
        finally:
            if path and os.path.exists(path):
                os.unlink(path)

    # ---- Placeholder detection ----

    def test_placeholder_not_marked_passed(self):
        """Runtime placeholder KPOINTS must not be marked as passed."""
        from modules.base import write_kpoints_summary
        kpath = None
        spath = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode='w', suffix='_KPOINTS', delete=False) as f:
                self._write_placeholder_kpoints(f.name)
                kpath = f.name
            spath = kpath + "_summary.yaml"
            try:
                summary = write_kpoints_summary("band", kpath, spath)
                self.assertEqual(summary["mode"], "runtime_placeholder")
                self.assertIsNone(summary["passed"])
                self.assertIn("warning", summary)
                self.assertIn("runtime", summary["warning"])
            finally:
                if os.path.exists(spath):
                    os.unlink(spath)
        finally:
            if kpath and os.path.exists(kpath):
                os.unlink(kpath)

    # ---- Runtime guard ----

    def test_runtime_guard_uses_exit_codes(self):
        """Runtime guard must use command exit status, not awk shell vars."""
        from modules.base import kpoints_2d_runtime_guard
        guard = kpoints_2d_runtime_guard()
        self.assertIsInstance(guard, str)
        self.assertIn("kz", guard.lower())
        # Must use command exit status, not ${e} shell variables set by awk.
        # `if ! awk ...; then` is safe under set -e.
        self.assertIn("if ! awk", guard)
        # Must NOT check awk-internal variables as shell variables
        self.assertNotIn("${e:", guard)

    def test_runtime_guard_no_0_grep_bypass(self):
        """Runtime guard must not skip regular mesh check via grep '^0$'."""
        from modules.base import kpoints_2d_runtime_guard
        guard = kpoints_2d_runtime_guard()
        # The old guard used `grep -q '^0$'` to skip, which matches normal
        # VASP auto-generation lines. New guard must not have this bypass.
        self.assertNotIn("grep -q '^0$'", guard)
        # Both line-mode and regular checks should run unconditionally
        self.assertIn("Nkz != 1", guard)


if __name__ == "__main__":
    unittest.main()
