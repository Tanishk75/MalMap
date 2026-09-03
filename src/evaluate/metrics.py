"""Evaluation metrics core (Module Interface Spec Section 5, Data Dictionary
Section 6, ADR-0013).

Pure metric computation and CSV row writing/aggregation -- the parts of
evaluate() that need neither a trained model nor a dataloader, and so can be
built and tested before either exists.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix as sk_confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

from src.config import Track, metrics_path

EVAL_DATASETS = ("in_distribution", "cross_track", "perturbed")


def compute_metrics(y_true, y_pred, family_id_map: dict[str, int]) -> dict:
    """Returns {'accuracy', 'macro_f1', 'weighted_f1', 'per_family', 'confusion_matrix'}.

    per_family is keyed by family name (not id) and covers every family in
    family_id_map, including ones absent from this batch (support=0), so
    rows from different eval runs on the same track stay comparable.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    labels = sorted(family_id_map.values())
    id_to_family = {v: k for k, v in family_id_map.items()}

    accuracy = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0))
    weighted_f1 = float(
        f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)
    )

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )
    per_family = {
        id_to_family[label]: {
            "precision": float(p), "recall": float(r), "f1": float(f), "support": int(s),
        }
        for label, p, r, f, s in zip(labels, precision, recall, f1, support)
    }

    confusion = sk_confusion_matrix(y_true, y_pred, labels=labels)

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_family": per_family,
        "confusion_matrix": confusion,
    }


def write_metrics_row(
    stage: str,
    track: Track,
    eval_dataset: str,
    metrics: dict,
    n_eval: int,
    seed: int,
    padding_strength: float | None = None,
    junk_composition: str | None = None,
) -> None:
    """Appends one row to results/{track}/{stage}_metrics.csv (Data Dictionary
    Section 6). Creates the file with a header on first write."""
    if eval_dataset not in EVAL_DATASETS:
        raise ValueError(f"unknown eval_dataset {eval_dataset!r}, expected one of {EVAL_DATASETS}")
    if (padding_strength is None) != (junk_composition is None):
        raise ValueError(
            "padding_strength and junk_composition must both be set or both be null "
            "(ADR-0015: a perturbed row always carries both)"
        )

    row = {
        "stage": stage,
        "track": track,
        "eval_dataset": eval_dataset,
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "weighted_f1": metrics["weighted_f1"],
        "per_family_json": json.dumps(metrics["per_family"], sort_keys=True),
        "n_eval": n_eval,
        "padding_strength": padding_strength,
        "junk_composition": junk_composition,
        "seed": seed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    path = metrics_path(stage, track)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = not path.exists()
    pd.DataFrame([row]).to_csv(path, mode="a", header=header, index=False)


def summarize_seeds(csv_path) -> pd.DataFrame:
    """Aggregates a metrics CSV to mean +/- std over seed, grouped by every
    other identifying column -- a single-seed delta is not evidence (ADR-0013).

    junk_composition is grouped, never averaged over (ADR-0015): 'zero' and
    'random' rows stay separate panels rather than being blended together.
    """
    df = pd.read_csv(csv_path)
    group_cols = [
        c for c in ("stage", "track", "eval_dataset", "padding_strength", "junk_composition")
        if c in df.columns
    ]
    metric_cols = [c for c in ("accuracy", "macro_f1", "weighted_f1") if c in df.columns]

    grouped = df.groupby(group_cols, dropna=False)[metric_cols]
    summary = grouped.agg(["mean", "std", "count"])
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    return summary.reset_index()
