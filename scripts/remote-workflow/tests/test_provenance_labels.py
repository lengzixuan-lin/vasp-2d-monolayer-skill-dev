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


if __name__ == "__main__":
    unittest.main()
