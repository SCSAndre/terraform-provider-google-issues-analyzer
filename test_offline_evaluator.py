"""Tests for offline evaluator harness."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from offline_evaluator import (
    compute_binary_metrics,
    evaluate_shadow_regression,
    filter_issues_by_split,
    LabeledIssue,
    load_labeled_issues,
    main,
    run_evaluation,
    suggest_gate_thresholds,
)


class TestOfflineEvaluator(unittest.TestCase):
    """Validate offline evaluation behavior and result shape."""

    def test_compute_binary_metrics(self):
        metrics = compute_binary_metrics(
            y_true=[True, True, False, False],
            y_pred=[True, False, True, False],
        )
        self.assertEqual(metrics["tp"], 1.0)
        self.assertEqual(metrics["tn"], 1.0)
        self.assertEqual(metrics["fp"], 1.0)
        self.assertEqual(metrics["fn"], 1.0)
        self.assertAlmostEqual(metrics["precision"], 0.5)
        self.assertAlmostEqual(metrics["recall"], 0.5)
        self.assertAlmostEqual(metrics["f1"], 0.5)
        self.assertAlmostEqual(metrics["accuracy"], 0.5)

    def test_load_labeled_issues(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "dataset.csv"
            csv_path.write_text(
                "title,body,labels,is_relevant,category\n"
                "Cloud Armor issue,Policy fails,cloud-armor|bug,true,Cloud Armor\n",
                encoding="utf-8",
            )

            rows = load_labeled_issues(csv_path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].title, "Cloud Armor issue")
            self.assertEqual(rows[0].labels, ["cloud-armor", "bug"])
            self.assertTrue(rows[0].is_relevant)
            self.assertEqual(rows[0].category, "Cloud Armor")
            self.assertEqual(rows[0].split, "unspecified")

    def test_filter_issues_by_split(self):
        issues = [
            LabeledIssue("a", "b", [], True, "Cloud Armor", split="train"),
            LabeledIssue("c", "d", [], False, None, split="test"),
        ]
        filtered = filter_issues_by_split(issues, split="test")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].split, "test")

    def test_run_evaluation_writes_output(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "dataset.csv"
            output_path = Path(tmp_dir) / "metrics" / "result.json"

            csv_path.write_text(
                "title,body,labels,is_relevant,category,split\n"
                "Cloud Armor security policy issue,Policy rule mismatch,cloud-armor,true,Cloud Armor,train\n"
                "Compute docs typo,Update docs,documentation,false,,train\n"
                "google_compute_security_policy bug,Terraform apply fails,,true,Cloud Armor,test\n"
                "General networking question,Routing table confusion,,false,,test\n",
                encoding="utf-8",
            )

            result = run_evaluation(csv_path, output_path)

            self.assertTrue(output_path.exists())
            self.assertEqual(result["dataset_size"], 4)
            self.assertIn("baseline", result)
            self.assertIn("shadow", result)
            self.assertIn("category_accuracy", result)
            self.assertIn("shadow_classification_flips", result)
            self.assertIn("slice_metrics", result)
            self.assertIn("category_metrics", result)
            self.assertIn("split_distribution", result)
            self.assertEqual(result["split_distribution"]["train"], 2)
            self.assertEqual(result["split_distribution"]["test"], 2)

    def test_run_evaluation_with_split_filter(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "dataset.csv"
            csv_path.write_text(
                "title,body,labels,is_relevant,category,split\n"
                "Cloud Armor issue one,Body one,cloud-armor,true,Cloud Armor,train\n"
                "Cloud Armor issue two,Body two,cloud-armor,true,Cloud Armor,test\n",
                encoding="utf-8",
            )
            result = run_evaluation(csv_path, split="test")
            self.assertEqual(result["dataset_size"], 1)

    def test_evaluate_shadow_regression_pass(self):
        result = {
            "baseline": {"precision": 0.9, "recall": 0.9, "f1": 0.9},
            "shadow": {"precision": 0.89, "recall": 0.885, "f1": 0.89},
        }
        failures = evaluate_shadow_regression(
            result=result,
            max_precision_drop=0.02,
            max_recall_drop=0.02,
            max_f1_drop=0.02,
        )
        self.assertEqual(failures, [])

    def test_evaluate_shadow_regression_fail(self):
        result = {
            "baseline": {"precision": 0.9, "recall": 0.9, "f1": 0.9},
            "shadow": {"precision": 0.7, "recall": 0.82, "f1": 0.75},
        }
        failures = evaluate_shadow_regression(
            result=result,
            max_precision_drop=0.02,
            max_recall_drop=0.05,
            max_f1_drop=0.02,
        )
        self.assertEqual(len(failures), 3)

    def test_main_returns_non_zero_on_quality_gate_failure(self):
        fake_result = {
            "dataset_size": 50,
            "labeled_relevant_count": 20,
            "baseline": {"precision": 0.9, "recall": 0.9, "f1": 0.9},
            "shadow": {"precision": 0.5, "recall": 0.5, "f1": 0.5},
        }
        with patch("offline_evaluator.run_evaluation", return_value=fake_result):
            with patch(
                "sys.argv",
                [
                    "offline_evaluator.py",
                    "--input",
                    "fake.csv",
                    "--fail-on-shadow-regression",
                    "--max-precision-drop",
                    "0.01",
                    "--max-recall-drop",
                    "0.01",
                    "--max-f1-drop",
                    "0.01",
                ],
            ):
                exit_code = main()
        self.assertEqual(exit_code, 2)

    def test_suggest_gate_thresholds(self):
        result = {
            "baseline": {"precision": 0.9, "recall": 0.85, "f1": 0.87},
            "shadow": {"precision": 0.86, "recall": 0.8, "f1": 0.82},
        }
        thresholds = suggest_gate_thresholds(result, safety_margin=0.01)
        self.assertEqual(thresholds["max_precision_drop"], 0.05)
        self.assertEqual(thresholds["max_recall_drop"], 0.06)
        self.assertEqual(thresholds["max_f1_drop"], 0.06)

    def test_main_skips_gate_when_support_too_low(self):
        fake_result = {
            "dataset_size": 4,
            "labeled_relevant_count": 1,
            "baseline": {"precision": 0.9, "recall": 0.9, "f1": 0.9},
            "shadow": {"precision": 0.5, "recall": 0.5, "f1": 0.5},
        }
        with patch("offline_evaluator.run_evaluation", return_value=fake_result):
            with patch(
                "sys.argv",
                [
                    "offline_evaluator.py",
                    "--input",
                    "fake.csv",
                    "--fail-on-shadow-regression",
                    "--min-support",
                    "30",
                    "--min-relevant-support",
                    "10",
                ],
            ):
                exit_code = main()
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()

