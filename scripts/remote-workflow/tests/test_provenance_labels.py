#!/usr/bin/env python3
"""Local-only tests for Batch A provenance/result-label helpers."""

import os
import sys
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
