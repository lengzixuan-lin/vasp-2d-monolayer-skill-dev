#!/usr/bin/env python3
"""Local-only tests for Batch A provenance/result-label helpers."""

import os
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class FakeProject:
    def __init__(self, project_dir):
        self.name = "fake_project"
        self.project_dir = project_dir


class TestBatchAResultLabels(unittest.TestCase):
    def assert_result_schema_keys(self, result):
        self.assertIn("value_name", result)
        self.assertIn("parser_or_tool", result)
        self.assertIn("name", result["parser_or_tool"])
        self.assertIn("transformation", result)
        self.assertIn("label", result["transformation"])
        self.assertIn("parent_calculation", result)
        self.assertIn("convergence_status", result)
        self.assertIn("task_status", result["convergence_status"])
        self.assertIn("result_status", result)

    def test_prepared_module_without_outcar_is_pending_review(self):
        import workflow

        with tempfile.TemporaryDirectory() as tmp:
            project = FakeProject(tmp)
            os.makedirs(os.path.join(tmp, "02_scf"))
            labels = workflow.build_baseline_result_labels(
                project, "02_scf", {"state": "prepared"})

        self.assertEqual(
            labels["module_identity"]["normalized_module_label"], "02_scf")
        self.assertEqual(labels["review_state"]["state"], "pending_review")
        self.assertEqual(
            labels["results"][0]["result_status"], "pending_review")
        self.assert_result_schema_keys(labels["results"][0])
        self.assertEqual(labels["results"][0]["value_name"],
                         "module_collection_status")
        self.assertEqual(labels["results"][0]["parent_calculation"], "01_opt")

    def test_completed_band_without_band_gap_is_diagnostic(self):
        import workflow
        from collect.outcar_parser import OutcarParser

        with tempfile.TemporaryDirectory() as tmp:
            project = FakeProject(tmp)
            band_dir = os.path.join(tmp, "03_pbeband")
            os.makedirs(band_dir)
            outcar = os.path.join(band_dir, "OUTCAR")
            with open(outcar, "w") as f:
                f.write("General timing and accounting\n")
            labels = workflow.build_baseline_result_labels(
                project, "03_pbeband", {"state": "completed"},
                parser=OutcarParser(outcar))

        self.assertEqual(
            labels["module_identity"]["normalized_module_label"], "03_band")
        band_gap = [
            item for item in labels["results"]
            if item["value_name"] == "band_gap"
        ][0]
        self.assert_result_schema_keys(band_gap)
        self.assertEqual(band_gap["parent_calculation"], "02_scf")
        self.assertEqual(band_gap["parser_or_tool"]["name"],
                         "VASPKIT 211 output")
        self.assertEqual(band_gap["transformation"]["label"],
                         "band_gap_extraction")
        self.assertEqual(band_gap["result_status"], "diagnostic")
        self.assertIsNone(band_gap["value"])


class TestBatchBResultLabels(unittest.TestCase):
    def assert_result_schema_keys(self, result):
        self.assertIn("value_name", result)
        self.assertIn("parser_or_tool", result)
        self.assertIn("name", result["parser_or_tool"])
        self.assertIn("transformation", result)
        self.assertIn("label", result["transformation"])
        self.assertIn("parent_calculation", result)
        self.assertIn("convergence_status", result)
        self.assertIn("task_status", result["convergence_status"])
        self.assertIn("result_status", result)

    def test_hse_band_missing_parent_and_output_is_not_final(self):
        import workflow

        with tempfile.TemporaryDirectory() as tmp:
            project = FakeProject(tmp)
            os.makedirs(os.path.join(tmp, "05_hse_band"))
            labels = workflow.build_batch_b_result_labels(
                project, "05_hse_band", {"state": "completed"})

        hse_gap = labels["results"][0]
        self.assert_result_schema_keys(hse_gap)
        self.assertEqual(hse_gap["value_name"], "hse_band_gap")
        self.assertEqual(hse_gap["parent_calculation"], "05_hse_scf")
        self.assertEqual(hse_gap["result_status"], "diagnostic")
        self.assertNotEqual(hse_gap["result_status"], "final")
        self.assertFalse(labels["source_files"]["05_hse_scf/CHGCAR"]["exists"])

    def test_optical_missing_converted_2d_outputs_is_not_final(self):
        import workflow

        with tempfile.TemporaryDirectory() as tmp:
            project = FakeProject(tmp)
            optical_dir = os.path.join(tmp, "08_optical")
            os.makedirs(optical_dir)
            with open(os.path.join(optical_dir, "INCAR"), "w") as f:
                f.write("LOPTICS = .TRUE.\nNBANDS = 128\n")
            labels = workflow.build_batch_b_result_labels(
                project, "08_optical", {"state": "completed"})

        spectra = [
            item for item in labels["results"]
            if item["value_name"] == "vaspkit_710_2d_spectra"
        ][0]
        self.assert_result_schema_keys(spectra)
        self.assertEqual(spectra["parent_calculation"], "02_scf")
        self.assertEqual(spectra["result_status"], "diagnostic")
        self.assertNotEqual(spectra["result_status"], "final")
        self.assertEqual(
            spectra["transformation"]["label"],
            "vaspkit_710_2d_optical_conversion")

    def test_optical_710_is_2d_and_711_is_bulk_only_invalid(self):
        import workflow

        task_710 = workflow.optical_vaspkit_task_policy(710)
        task_711 = workflow.optical_vaspkit_task_policy(711)

        self.assertTrue(task_710["valid_for_monolayer_absorption"])
        self.assertEqual(task_710["label"], "vaspkit_710_2d_optical_conversion")
        self.assertFalse(task_711["valid_for_monolayer_absorption"])
        self.assertIn("bulk", task_711["scope"])

    def test_phonopy_missing_force_sets_and_summary_is_not_final(self):
        import workflow

        with tempfile.TemporaryDirectory() as tmp:
            project = FakeProject(tmp)
            phonopy_dir = os.path.join(tmp, "09_phonopy_fd")
            os.makedirs(phonopy_dir)
            with open(os.path.join(phonopy_dir, "displacement_manifest.yaml"), "w") as f:
                f.write("subtasks: []\n")
            labels = workflow.build_batch_b_result_labels(
                project, "09_phonopy_fd", {"state": "completed"})

        summary = labels["results"][0]
        self.assert_result_schema_keys(summary)
        self.assertEqual(summary["parent_calculation"], "01_opt")
        self.assertEqual(summary["result_status"], "diagnostic")
        self.assertNotEqual(summary["result_status"], "final")
        self.assertFalse(labels["source_files"]["FORCE_SETS"]["exists"])

    def test_batch_b_entries_keep_schema_aligned_keys(self):
        import workflow

        with tempfile.TemporaryDirectory() as tmp:
            project = FakeProject(tmp)
            for mod_dir in ("05_hse_scf", "05_hse_band",
                            "08_optical", "09_phonopy_fd"):
                os.makedirs(os.path.join(tmp, mod_dir))
                labels = workflow.build_batch_b_result_labels(
                    project, mod_dir, {"state": "prepared"})
                self.assertTrue(labels["results"])
                for result in labels["results"]:
                    self.assert_result_schema_keys(result)


class TestBatchCResultLabels(unittest.TestCase):
    def assert_result_schema_keys(self, result):
        self.assertIn("value_name", result)
        self.assertIn("parser_or_tool", result)
        self.assertIn("name", result["parser_or_tool"])
        self.assertIn("transformation", result)
        self.assertIn("label", result["transformation"])
        self.assertIn("parent_calculation", result)
        self.assertIn("convergence_status", result)
        self.assertIn("task_status", result["convergence_status"])
        self.assertIn("uncertainty_or_fit_quality", result)
        self.assertIn("result_status", result)

    def write_yaml(self, path, payload):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            yaml.safe_dump(payload, f, sort_keys=False)

    def touch(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("synthetic local-only evidence\n")

    def test_effective_mass_missing_evidence_is_not_final(self):
        import workflow

        with tempfile.TemporaryDirectory() as tmp:
            project = FakeProject(tmp)
            os.makedirs(os.path.join(tmp, "11_effective_mass"))
            labels = workflow.build_batch_c_result_labels(
                project, "11_effective_mass", {"state": "completed"})

        result = labels["results"][0]
        self.assert_result_schema_keys(result)
        self.assertEqual(result["value_name"], "effective_mass_fit_summary")
        self.assertEqual(result["transformation"]["label"],
                         "effective_mass_curvature_fit")
        self.assertNotEqual(result["result_status"], "final")

    def test_effective_mass_entries_include_fit_source_metadata(self):
        import workflow

        with tempfile.TemporaryDirectory() as tmp:
            project = FakeProject(tmp)
            em_dir = os.path.join(tmp, "11_effective_mass")
            run_dir = os.path.join(em_dir, "cbm_v1_a")
            self.write_yaml(os.path.join(em_dir, "effective_mass_settings.yaml"), {
                "edge_source": "03_pbeband",
                "charge_parent": "02_scf",
                "delta_k": 0.005,
            })
            self.write_yaml(
                os.path.join(em_dir, "00_edge_source", "band_edge.yaml"),
                {"gap_eV": 1.0})
            self.write_yaml(os.path.join(em_dir, "em_runs.yaml"), {
                "targets": [{
                    "run_dir": "cbm_v1_a",
                    "carrier": "electron",
                    "edge": "cbm",
                    "valley_label": "v1",
                    "direction": "a",
                }]
            })
            self.touch(os.path.join(run_dir, "EIGENVAL"))
            self.touch(os.path.join(run_dir, "KPOINTS"))
            self.write_yaml(os.path.join(run_dir, "em_target.yaml"),
                            {"carrier": "electron"})
            self.touch(os.path.join(tmp, "02_scf", "CHGCAR"))
            self.touch(os.path.join(tmp, "03_pbeband", "EIGENVAL"))
            self.write_yaml(os.path.join(em_dir, "results", "em_summary.yaml"), {
                "results": [{
                    "run_dir": "cbm_v1_a",
                    "carrier": "electron",
                    "edge": "cbm",
                    "direction": "a",
                    "valley_index": 1,
                    "source_kpoint": [0.0, 0.0, 0.0],
                    "source_band_index_1based": 2,
                    "source_spin_index_1based": 1,
                    "primary_effective_mass_m0": 0.42,
                    "quality_pass": True,
                    "fits": [{
                        "fit_each_side": 5,
                        "r2": 0.999,
                        "fit_energy_window_meV": 21.0,
                        "max_abs_residual_meV": 0.7,
                        "curvature_sign_ok": True,
                    }],
                }]
            })
            self.touch(os.path.join(em_dir, "results", "em_summary.csv"))
            labels = workflow.build_batch_c_result_labels(
                project, "11_effective_mass", {"state": "completed"})

        result = labels["results"][0]
        self.assert_result_schema_keys(result)
        self.assertEqual(result["value_name"], "effective_mass_m0")
        self.assertEqual(result["parent_calculation"], "02_scf + 03_pbeband")
        self.assertEqual(result["transformation"]["label"],
                         "effective_mass_curvature_fit")
        self.assertEqual(result["transformation"]["details"]["carrier"],
                         "electron")
        self.assertEqual(
            result["uncertainty_or_fit_quality"]["type"],
            "quadratic_curvature_fit")
        self.assertEqual(result["uncertainty_or_fit_quality"]["r2"], 0.999)
        self.assertEqual(result["result_status"], "final")
        self.assertIn("target_runs", labels)

    def test_mobility_missing_evidence_is_not_final(self):
        import workflow

        with tempfile.TemporaryDirectory() as tmp:
            project = FakeProject(tmp)
            os.makedirs(os.path.join(tmp, "12_mobility"))
            labels = workflow.build_batch_c_result_labels(
                project, "12_mobility", {"state": "completed"})

        result = labels["results"][0]
        self.assert_result_schema_keys(result)
        self.assertEqual(result["value_name"], "mobility_fit_summary")
        self.assertEqual(result["transformation"]["label"],
                         "deformation_potential_mobility_fit")
        self.assertNotEqual(result["result_status"], "final")

    def test_mobility_entries_include_fit_source_metadata(self):
        import workflow

        with tempfile.TemporaryDirectory() as tmp:
            project = FakeProject(tmp)
            mob_dir = os.path.join(tmp, "12_mobility")
            em_source = os.path.join(
                tmp, "11_effective_mass", "results", "em_summary.yaml")
            self.write_yaml(em_source, {"results": []})
            self.write_yaml(os.path.join(mob_dir, "mobility_settings.yaml"), {
                "effective_mass_source": em_source,
                "charge_parent": "02_scf",
                "strain_values": [-1.0, 0.0, 1.0],
            })
            strain_runs = []
            for strain in (-1.0, 0.0, 1.0):
                label = str(strain).replace("-", "m").replace(".", "p")
                relax_dir = os.path.join("strain_a", label, "relax")
                scf_dir = os.path.join("strain_a", label, "scf")
                edge_dir = os.path.join("strain_a", label, "cbm_v1_a")
                strain_runs.append({
                    "direction": "a",
                    "strain_percent": strain,
                    "strain_fraction": strain / 100.0,
                    "relax_dir": relax_dir,
                    "scf_dir": scf_dir,
                    "edge_runs": [{"run_dir": edge_dir}],
                })
                self.touch(os.path.join(mob_dir, relax_dir, "CONTCAR"))
                self.touch(os.path.join(mob_dir, scf_dir, "CHGCAR"))
                self.touch(os.path.join(mob_dir, scf_dir, "LOCPOT"))
                self.touch(os.path.join(mob_dir, edge_dir, "EIGENVAL"))
                self.touch(os.path.join(mob_dir, edge_dir, "KPOINTS"))
            self.write_yaml(os.path.join(mob_dir, "mobility_runs.yaml"), {
                "runs": strain_runs,
            })
            self.touch(os.path.join(tmp, "01_opt", "CONTCAR"))
            self.touch(os.path.join(tmp, "02_scf", "CHGCAR"))
            self.write_yaml(
                os.path.join(mob_dir, "results", "mobility_summary.yaml"), {
                    "elastic": {
                        "a": {
                            "C2D_N_per_m": 123.0,
                            "r2": 0.999,
                            "quality_pass": True,
                        }
                    },
                    "mobility": [{
                        "carrier": "electron",
                        "edge": "cbm",
                        "valley_index": 1,
                        "direction": "a",
                        "m_transport_m0": 0.42,
                        "m_dos_m0": 0.50,
                        "C2D_N_per_m": 123.0,
                        "E1_eV": 4.2,
                        "edge_fit_r2": 0.998,
                        "mobility_cm2_per_Vs": 321.0,
                        "quality_pass": True,
                    }],
                })
            self.touch(os.path.join(mob_dir, "results", "mobility_summary.csv"))
            self.touch(os.path.join(mob_dir, "results", "mobility_points.csv"))
            labels = workflow.build_batch_c_result_labels(
                project, "12_mobility", {"state": "completed"})

        result = labels["results"][0]
        self.assert_result_schema_keys(result)
        self.assertEqual(result["value_name"], "mobility_cm2_per_Vs")
        self.assertEqual(result["parent_calculation"],
                         "11_effective_mass + 02_scf + 01_opt")
        self.assertEqual(result["transformation"]["label"],
                         "deformation_potential_mobility_fit")
        self.assertEqual(result["uncertainty_or_fit_quality"]["C2D_N_per_m"],
                         123.0)
        self.assertEqual(result["uncertainty_or_fit_quality"]["E1_eV"], 4.2)
        self.assertEqual(
            result["uncertainty_or_fit_quality"]["effective_mass_source"],
            em_source)
        self.assertEqual(result["result_status"], "final")
        self.assertIn("strain_run_evidence", labels)


if __name__ == "__main__":
    unittest.main()
