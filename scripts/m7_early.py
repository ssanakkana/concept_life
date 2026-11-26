#!/usr/bin/env python3
"""M7: predict the lifecycle type from the first three years.

Outputs:
  runs/m7/early_metrics.json
  data/processed/early_predictions.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from concept_life.config import load_config  # noqa: E402
from concept_life.early import (  # noqa: E402
    FEATURE_NAMES,
    accuracy,
    build_early_rows,
    confusion_matrix,
    macro_f1,
    majority_accuracy,
    per_class_metrics,
    predict_proba,
    stratified_folds,
    train_softmax,
)


def load_series(path: Path) -> dict[str, dict[int, int]]:
    series: dict[str, dict[int, int]] = {}
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            series.setdefault(row["concept_id"], {})[int(row["year"])] = int(
                row["count"]
            )
    return series


def load_totals(path: Path) -> dict[int, int]:
    totals: dict[int, int] = {}
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            totals[int(row["year"])] = int(row["papers"])
    return totals


def load_clusters(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def counts_by_label(labels: np.ndarray, names: list[str]) -> dict[str, int]:
    return {
        name: int((labels == index).sum()) for index, name in enumerate(names)
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--series", type=Path, default=ROOT / "data" / "processed" / "concept_series.csv"
    )
    parser.add_argument(
        "--totals", type=Path, default=ROOT / "runs" / "m1" / "report" / "year_histogram.csv"
    )
    parser.add_argument(
        "--clusters",
        type=Path,
        default=ROOT / "data" / "processed" / "lifecycle_clusters.csv",
    )
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "m7.json")
    parser.add_argument(
        "--metrics", type=Path, default=ROOT / "runs" / "m7" / "early_metrics.json"
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        default=ROOT / "data" / "processed" / "early_predictions.csv",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    analysis = config["analysis"]
    early_config = config["early"]

    series = load_series(args.series)
    totals = load_totals(args.totals)
    rows = build_early_rows(
        series,
        totals,
        load_clusters(args.clusters),
        early_window_years=int(early_config["early_window_years"]),
        min_early_count=int(early_config["min_early_count"]),
        active_min_count=int(early_config["active_min_count"]),
        max_birth_year=int(early_config["max_birth_year"]),
        start_year=int(analysis["start_year"]),
        end_year=int(analysis["end_year"]),
    )
    if not rows:
        raise SystemExit("no concepts with early features")

    labels = sorted({row["label"] for row in rows})
    label_to_index = {label: index for index, label in enumerate(labels)}
    matrix = np.asarray([[row[name] for name in FEATURE_NAMES] for row in rows])
    target = np.asarray([label_to_index[row["label"]] for row in rows])
    birth = np.asarray([row["birth_year"] for row in rows])
    n_classes = len(labels)

    # Same-era evaluation: stratified 5-fold cross-validation.
    folds = stratified_folds(target, int(early_config["folds"]), int(early_config["seed"]))
    fold_accuracy = []
    fold_macro_f1 = []
    fold_majority = []
    out_of_fold = np.zeros(len(target), dtype=int)
    for train_index, test_index in folds:
        mean = matrix[train_index].mean(axis=0)
        std = matrix[train_index].std(axis=0)
        std[std == 0] = 1.0
        train_matrix = (matrix[train_index] - mean) / std
        test_matrix = (matrix[test_index] - mean) / std
        weights, bias = train_softmax(
            train_matrix,
            target[train_index],
            n_classes,
            l2=float(early_config["l2"]),
            lr=float(early_config["lr"]),
            epochs=int(early_config["epochs"]),
        )
        predicted = np.argmax(predict_proba(test_matrix, weights, bias), axis=1)
        out_of_fold[test_index] = predicted
        fold_accuracy.append(accuracy(target[test_index], predicted))
        fold_macro_f1.append(macro_f1(target[test_index], predicted, n_classes))
        fold_majority.append(majority_accuracy(target[train_index], target[test_index]))

    # Temporal stress test: train on concepts born <= 2012, test 2013-2018.
    train_mask = birth <= int(early_config["temporal_train_max_birth"])
    test_mask = (birth >= int(early_config["temporal_train_max_birth"]) + 1) & (
        birth <= int(early_config["temporal_test_max_birth"])
    )
    mean = matrix[train_mask].mean(axis=0)
    std = matrix[train_mask].std(axis=0)
    std[std == 0] = 1.0
    train_matrix = (matrix[train_mask] - mean) / std
    test_matrix = (matrix[test_mask] - mean) / std
    weights, bias = train_softmax(
        train_matrix,
        target[train_mask],
        n_classes,
        l2=float(early_config["l2"]),
        lr=float(early_config["lr"]),
        epochs=int(early_config["epochs"]),
    )
    probabilities = predict_proba(test_matrix, weights, bias)
    predicted = np.argmax(probabilities, axis=1)
    temporal_accuracy = accuracy(target[test_mask], predicted)
    temporal_macro_f1 = macro_f1(target[test_mask], predicted, n_classes)
    temporal_majority = majority_accuracy(target[train_mask], target[test_mask])
    temporal_confusion = confusion_matrix(target[test_mask], predicted, n_classes)
    temporal_per_class = per_class_metrics(target[test_mask], predicted, labels)

    metrics = {
        "labels": labels,
        "features": FEATURE_NAMES,
        "n_concepts": len(rows),
        "random_cv": {
            "folds": len(folds),
            "accuracy_mean": round(float(np.mean(fold_accuracy)), 4),
            "accuracy_std": round(float(np.std(fold_accuracy)), 4),
            "macro_f1_mean": round(float(np.mean(fold_macro_f1)), 4),
            "macro_f1_std": round(float(np.std(fold_macro_f1)), 4),
            "majority_accuracy_mean": round(float(np.mean(fold_majority)), 4),
            "confusion": confusion_matrix(target, out_of_fold, n_classes),
        },
        "temporal": {
            "train_n": int(train_mask.sum()),
            "test_n": int(test_mask.sum()),
            "accuracy": round(temporal_accuracy, 4),
            "macro_f1": round(temporal_macro_f1, 4),
            "majority_accuracy": round(temporal_majority, 4),
            "confusion": temporal_confusion,
            "per_class": temporal_per_class,
            "train_label_counts": counts_by_label(target[train_mask], labels),
            "test_label_counts": counts_by_label(target[test_mask], labels),
        },
        "config": early_config,
    }
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    test_rows = [row for row, keep in zip(rows, test_mask) if keep]
    args.predictions.parent.mkdir(parents=True, exist_ok=True)
    with args.predictions.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = [
            "concept_id", "name", "birth_year", "true_label", "predicted_label",
            "confidence", "correct", "early_share_mean", "early_growth",
            "early_decline", "early_peak_position",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row, probability, prediction in zip(test_rows, probabilities, predicted):
            true_index = label_to_index[row["label"]]
            writer.writerow(
                {
                    "concept_id": row["concept_id"],
                    "name": row["name"],
                    "birth_year": row["birth_year"],
                    "true_label": row["label"],
                    "predicted_label": labels[int(prediction)],
                    "confidence": round(float(probability.max()), 4),
                    "correct": bool(int(prediction) == true_index),
                    "early_share_mean": round(row["early_share_mean"], 8),
                    "early_growth": round(row["early_growth"], 6),
                    "early_decline": round(row["early_decline"], 6),
                    "early_peak_position": round(row["early_peak_position"], 6),
                }
            )

    print(json.dumps({
        "n_concepts": len(rows),
        "random_cv": {
            "accuracy": metrics["random_cv"]["accuracy_mean"],
            "macro_f1": metrics["random_cv"]["macro_f1_mean"],
        },
        "temporal": {
            "train_n": metrics["temporal"]["train_n"],
            "test_n": metrics["temporal"]["test_n"],
            "accuracy": metrics["temporal"]["accuracy"],
            "macro_f1": metrics["temporal"]["macro_f1"],
            "majority": metrics["temporal"]["majority_accuracy"],
        },
    }, ensure_ascii=False, indent=2))
    print(f"wrote {args.metrics}")
    print(f"wrote {args.predictions}")


if __name__ == "__main__":
    main()
