"""Offline evaluator for baseline vs shadow classifier quality."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from issue_classifier import IssueClassifier


@dataclass
class LabeledIssue:
    """Represents one labeled issue record from a CSV file."""

    title: str
    body: str
    labels: List[str]
    is_relevant: bool
    category: Optional[str] = None
    split: str = "unspecified"


def _parse_bool(value: str) -> bool:
    """Parse a CSV boolean field."""
    return value.strip().lower() in {"1", "true", "yes", "y"}


def _parse_labels(raw: str) -> List[str]:
    """Parse labels from a delimited field."""
    if not raw:
        return []
    return [token.strip() for token in re.split(r"[|,;]", raw) if token.strip()]


def load_labeled_issues(csv_path: Path) -> List[LabeledIssue]:
    """Load labeled issues from CSV.

    Required columns: title, body, is_relevant
    Optional columns: labels, category
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {csv_path}")

    issues: List[LabeledIssue] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"title", "body", "is_relevant"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        for row in reader:
            issues.append(
                LabeledIssue(
                    title=(row.get("title") or "").strip(),
                    body=(row.get("body") or "").strip(),
                    labels=_parse_labels((row.get("labels") or "").strip()),
                    is_relevant=_parse_bool((row.get("is_relevant") or "").strip()),
                    category=((row.get("category") or "").strip() or None),
                    split=((row.get("split") or "unspecified").strip().lower() or "unspecified"),
                )
            )
    return issues


def filter_issues_by_split(issues: List[LabeledIssue], split: Optional[str]) -> List[LabeledIssue]:
    """Filter labeled issues by split if provided."""
    if not split:
        return issues
    normalized = split.strip().lower()
    filtered = [issue for issue in issues if issue.split == normalized]
    if not filtered:
        raise ValueError(f"No issues found for split '{split}'")
    return filtered


def _slice_metrics_by_label(
    issues: List[LabeledIssue],
    baseline_pred: List[bool],
    shadow_pred: List[bool],
) -> Dict[str, Dict[str, Any]]:
    """Compute binary metrics for each label slice."""
    label_metrics: Dict[str, Dict[str, Any]] = {}
    all_labels = sorted({label for issue in issues for label in issue.labels})

    for label in all_labels:
        idx = [i for i, issue in enumerate(issues) if label in issue.labels]
        y_true = [issues[i].is_relevant for i in idx]
        y_base = [baseline_pred[i] for i in idx]
        y_shadow = [shadow_pred[i] for i in idx]
        label_metrics[label] = {
            "support": len(idx),
            "baseline": compute_binary_metrics(y_true, y_base),
            "shadow": compute_binary_metrics(y_true, y_shadow),
        }

    return label_metrics


def compute_binary_metrics(y_true: List[bool], y_pred: List[bool]) -> Dict[str, float]:
    """Compute binary classification metrics without external dependencies."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")

    tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
    tn = sum(1 for t, p in zip(y_true, y_pred) if (not t) and (not p))
    fp = sum(1 for t, p in zip(y_true, y_pred) if (not t) and p)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t and (not p))

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / len(y_true) if y_true else 0.0

    return {
        "support": float(len(y_true)),
        "tp": float(tp),
        "tn": float(tn),
        "fp": float(fp),
        "fn": float(fn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


def evaluate_baseline_vs_shadow(issues: List[LabeledIssue]) -> Dict[str, Any]:
    """Evaluate baseline and shadow performance on a labeled dataset."""
    classifier = IssueClassifier()

    truth: List[bool] = []
    baseline_pred: List[bool] = []
    shadow_pred: List[bool] = []
    shadow_flips = 0

    expected_category_count = 0
    baseline_category_correct = 0
    shadow_category_correct = 0

    for issue in issues:
        payload = {
            "title": issue.title,
            "body": issue.body,
            "labels": [{"name": value} for value in issue.labels],
        }

        base_relevant, base_category, _, _ = classifier.classify_issue(payload)
        comparison = classifier.get_shadow_score_comparison(payload)
        shadow_relevant = bool(comparison["shadow"]["is_relevant"])
        shadow_category = comparison["shadow"]["category"] if shadow_relevant else None

        truth.append(issue.is_relevant)
        baseline_pred.append(base_relevant)
        shadow_pred.append(shadow_relevant)

        if base_relevant != shadow_relevant:
            shadow_flips += 1

        if issue.is_relevant and issue.category:
            expected_category_count += 1
            if base_relevant and base_category == issue.category:
                baseline_category_correct += 1
            if shadow_relevant and shadow_category == issue.category:
                shadow_category_correct += 1

    category_metrics: Dict[str, Dict[str, Any]] = {}
    categories = sorted({issue.category for issue in issues if issue.category})
    for category in categories:
        idx = [
            i for i, issue in enumerate(issues)
            if issue.category == category and issue.is_relevant
        ]
        base_hits = sum(1 for i in idx if baseline_pred[i])
        shadow_hits = sum(1 for i in idx if shadow_pred[i])
        support = len(idx)
        category_metrics[category] = {
            "support": support,
            "baseline_relevant_hit_rate": (base_hits / support) if support else 0.0,
            "shadow_relevant_hit_rate": (shadow_hits / support) if support else 0.0,
        }

    baseline_metrics = compute_binary_metrics(truth, baseline_pred)
    shadow_metrics = compute_binary_metrics(truth, shadow_pred)

    category_accuracy_baseline = (
        baseline_category_correct / expected_category_count if expected_category_count else 0.0
    )
    category_accuracy_shadow = (
        shadow_category_correct / expected_category_count if expected_category_count else 0.0
    )

    return {
        "dataset_size": len(issues),
        "labeled_relevant_count": sum(1 for value in truth if value),
        "split_distribution": {
            split_name: sum(1 for issue in issues if issue.split == split_name)
            for split_name in sorted({issue.split for issue in issues})
        },
        "baseline": baseline_metrics,
        "shadow": shadow_metrics,
        "shadow_classification_flips": shadow_flips,
        "category_accuracy": {
            "support": expected_category_count,
            "baseline": category_accuracy_baseline,
            "shadow": category_accuracy_shadow,
        },
        "category_metrics": category_metrics,
        "slice_metrics": {
            "with_labels": {
                "support": sum(1 for issue in issues if issue.labels),
                "baseline": compute_binary_metrics(
                    [issue.is_relevant for issue in issues if issue.labels],
                    [baseline_pred[i] for i, issue in enumerate(issues) if issue.labels],
                ) if any(issue.labels for issue in issues) else compute_binary_metrics([], []),
                "shadow": compute_binary_metrics(
                    [issue.is_relevant for issue in issues if issue.labels],
                    [shadow_pred[i] for i, issue in enumerate(issues) if issue.labels],
                ) if any(issue.labels for issue in issues) else compute_binary_metrics([], []),
            },
            "without_labels": {
                "support": sum(1 for issue in issues if not issue.labels),
                "baseline": compute_binary_metrics(
                    [issue.is_relevant for issue in issues if not issue.labels],
                    [baseline_pred[i] for i, issue in enumerate(issues) if not issue.labels],
                ) if any(not issue.labels for issue in issues) else compute_binary_metrics([], []),
                "shadow": compute_binary_metrics(
                    [issue.is_relevant for issue in issues if not issue.labels],
                    [shadow_pred[i] for i, issue in enumerate(issues) if not issue.labels],
                ) if any(not issue.labels for issue in issues) else compute_binary_metrics([], []),
            },
            "per_label": _slice_metrics_by_label(issues, baseline_pred, shadow_pred),
        },
    }


def run_evaluation(
    input_csv: Path,
    output_json: Optional[Path] = None,
    split: Optional[str] = None,
) -> Dict[str, Any]:
    """Load dataset, evaluate quality metrics, and optionally persist JSON output."""
    issues = filter_issues_by_split(load_labeled_issues(input_csv), split=split)
    result = evaluate_baseline_vs_shadow(issues)

    if output_json is not None:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return result


def evaluate_shadow_regression(
    result: Dict[str, Any],
    max_precision_drop: float,
    max_recall_drop: float,
    max_f1_drop: float,
) -> List[str]:
    """Return quality gate failures when shadow metrics regress too far from baseline."""
    failures: List[str] = []

    baseline = result.get("baseline", {})
    shadow = result.get("shadow", {})

    precision_drop = float(baseline.get("precision", 0.0)) - float(shadow.get("precision", 0.0))
    recall_drop = float(baseline.get("recall", 0.0)) - float(shadow.get("recall", 0.0))
    f1_drop = float(baseline.get("f1", 0.0)) - float(shadow.get("f1", 0.0))

    if precision_drop > max_precision_drop:
        failures.append(
            f"Shadow precision drop {precision_drop:.4f} exceeds allowed {max_precision_drop:.4f}"
        )
    if recall_drop > max_recall_drop:
        failures.append(
            f"Shadow recall drop {recall_drop:.4f} exceeds allowed {max_recall_drop:.4f}"
        )
    if f1_drop > max_f1_drop:
        failures.append(f"Shadow F1 drop {f1_drop:.4f} exceeds allowed {max_f1_drop:.4f}")

    return failures


def suggest_gate_thresholds(result: Dict[str, Any], safety_margin: float = 0.02) -> Dict[str, float]:
    """Suggest gate thresholds from observed baseline-shadow metric deltas.

    Thresholds are based on observed drops plus a configurable margin.
    """
    baseline = result.get("baseline", {})
    shadow = result.get("shadow", {})

    precision_drop = max(0.0, float(baseline.get("precision", 0.0)) - float(shadow.get("precision", 0.0)))
    recall_drop = max(0.0, float(baseline.get("recall", 0.0)) - float(shadow.get("recall", 0.0)))
    f1_drop = max(0.0, float(baseline.get("f1", 0.0)) - float(shadow.get("f1", 0.0)))

    return {
        "max_precision_drop": round(precision_drop + safety_margin, 4),
        "max_recall_drop": round(recall_drop + safety_margin, 4),
        "max_f1_drop": round(f1_drop + safety_margin, 4),
    }


def main() -> int:
    """CLI entrypoint for offline quality evaluation."""
    parser = argparse.ArgumentParser(
        description="Evaluate baseline vs shadow classifier quality on a labeled CSV dataset."
    )
    parser.add_argument("--input", required=True, help="Path to labeled CSV input dataset")
    parser.add_argument(
        "--output",
        required=False,
        help="Optional path for JSON output file",
    )
    parser.add_argument(
        "--split",
        required=False,
        help="Optional dataset split filter (for example: train, validation, test)",
    )
    parser.add_argument(
        "--fail-on-shadow-regression",
        action="store_true",
        help="Exit non-zero if shadow metrics regress past configured tolerances",
    )
    parser.add_argument(
        "--max-precision-drop",
        type=float,
        default=0.02,
        help="Maximum allowed precision drop (baseline - shadow)",
    )
    parser.add_argument(
        "--max-recall-drop",
        type=float,
        default=0.02,
        help="Maximum allowed recall drop (baseline - shadow)",
    )
    parser.add_argument(
        "--max-f1-drop",
        type=float,
        default=0.02,
        help="Maximum allowed F1 drop (baseline - shadow)",
    )
    parser.add_argument(
        "--min-support",
        type=int,
        default=30,
        help="Minimum dataset size required to enforce a quality gate",
    )
    parser.add_argument(
        "--min-relevant-support",
        type=int,
        default=10,
        help="Minimum number of relevant labeled issues required to enforce a quality gate",
    )
    parser.add_argument(
        "--suggest-thresholds",
        action="store_true",
        help="Include suggested gate thresholds based on observed deltas",
    )
    args = parser.parse_args()

    result = run_evaluation(
        input_csv=Path(args.input),
        output_json=Path(args.output) if args.output else None,
        split=args.split,
    )

    if args.fail_on_shadow_regression:
        dataset_size = int(result.get("dataset_size", 0))
        relevant_support = int(result.get("labeled_relevant_count", 0))

        if dataset_size < args.min_support or relevant_support < args.min_relevant_support:
            result["quality_gate"] = {
                "enabled": True,
                "passed": True,
                "skipped": True,
                "reason": (
                    f"Insufficient support for gate enforcement: dataset_size={dataset_size} "
                    f"(min={args.min_support}), relevant_count={relevant_support} "
                    f"(min={args.min_relevant_support})"
                ),
                "max_precision_drop": args.max_precision_drop,
                "max_recall_drop": args.max_recall_drop,
                "max_f1_drop": args.max_f1_drop,
            }
            if args.suggest_thresholds:
                result["suggested_gate_thresholds"] = suggest_gate_thresholds(result)
            print(json.dumps(result, indent=2))
            return 0

        failures = evaluate_shadow_regression(
            result=result,
            max_precision_drop=args.max_precision_drop,
            max_recall_drop=args.max_recall_drop,
            max_f1_drop=args.max_f1_drop,
        )
        result["quality_gate"] = {
            "enabled": True,
            "max_precision_drop": args.max_precision_drop,
            "max_recall_drop": args.max_recall_drop,
            "max_f1_drop": args.max_f1_drop,
            "passed": len(failures) == 0,
            "failures": failures,
            "skipped": False,
        }
        if args.suggest_thresholds:
            result["suggested_gate_thresholds"] = suggest_gate_thresholds(result)
        print(json.dumps(result, indent=2))
        return 0 if not failures else 2

    if args.suggest_thresholds:
        result["suggested_gate_thresholds"] = suggest_gate_thresholds(result)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

