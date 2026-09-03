"""Tests for src/evaluate/metrics.py using synthetic predictions -- no real
model or dataloader needed to verify the metrics core."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

import src.config as config
from src.evaluate.metrics import compute_metrics, summarize_seeds, write_metrics_row


@pytest.fixture(autouse=True)
def isolated_results(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RESULTS", tmp_path / "results")


FAMILY_ID_MAP = {"Allaple.A": 0, "Yuner.A": 1, "Rare.Family": 2}


def test_compute_metrics_perfect_predictions():
    y_true = [0, 0, 1, 1, 2]
    y_pred = [0, 0, 1, 1, 2]

    metrics = compute_metrics(y_true, y_pred, FAMILY_ID_MAP)

    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["weighted_f1"] == 1.0
    assert metrics["confusion_matrix"].shape == (3, 3)


def test_compute_metrics_includes_absent_family_with_zero_support():
    # "Rare.Family" (id 2) never appears in this batch.
    y_true = [0, 0, 1, 1]
    y_pred = [0, 1, 1, 1]

    metrics = compute_metrics(y_true, y_pred, FAMILY_ID_MAP)

    assert "Rare.Family" in metrics["per_family"]
    assert metrics["per_family"]["Rare.Family"]["support"] == 0
    assert metrics["accuracy"] == 0.75


def test_compute_metrics_per_family_keyed_by_name_not_id():
    y_true = [0, 1, 2]
    y_pred = [0, 1, 2]
    metrics = compute_metrics(y_true, y_pred, FAMILY_ID_MAP)
    assert set(metrics["per_family"]) == set(FAMILY_ID_MAP)


def test_write_metrics_row_creates_file_with_header():
    metrics = compute_metrics([0, 1], [0, 1], FAMILY_ID_MAP)
    write_metrics_row("m0", "malimg", "in_distribution", metrics, n_eval=2, seed=42)

    path = config.metrics_path("m0", "malimg")
    assert path.exists()
    df = pd.read_csv(path)
    assert len(df) == 1
    assert df.iloc[0]["stage"] == "m0"
    assert df.iloc[0]["seed"] == 42
    assert pd.isna(df.iloc[0]["padding_strength"])


def test_write_metrics_row_appends():
    metrics = compute_metrics([0, 1], [0, 1], FAMILY_ID_MAP)
    write_metrics_row("m1", "malimg", "in_distribution", metrics, n_eval=2, seed=42)
    write_metrics_row("m1", "malimg", "in_distribution", metrics, n_eval=2, seed=43)

    df = pd.read_csv(config.metrics_path("m1", "malimg"))
    assert len(df) == 2
    assert sorted(df["seed"]) == [42, 43]


def test_write_metrics_row_per_family_json_round_trips():
    metrics = compute_metrics([0, 1, 2], [0, 1, 2], FAMILY_ID_MAP)
    write_metrics_row("m0", "big2015", "in_distribution", metrics, n_eval=3, seed=42)

    df = pd.read_csv(config.metrics_path("m0", "big2015"))
    per_family = json.loads(df.iloc[0]["per_family_json"])
    assert per_family["Allaple.A"]["f1"] == 1.0


def test_write_metrics_row_rejects_bad_eval_dataset():
    metrics = compute_metrics([0], [0], FAMILY_ID_MAP)
    with pytest.raises(ValueError):
        write_metrics_row("m0", "malimg", "not_a_real_dataset", metrics, n_eval=1, seed=42)


def test_write_metrics_row_requires_both_perturbation_fields_or_neither():
    metrics = compute_metrics([0], [0], FAMILY_ID_MAP)
    with pytest.raises(ValueError):
        write_metrics_row(
            "m0", "malimg", "perturbed", metrics, n_eval=1, seed=42, padding_strength=0.1
        )


def test_write_metrics_row_accepts_perturbed_row():
    metrics = compute_metrics([0], [0], FAMILY_ID_MAP)
    write_metrics_row(
        "m1", "malimg", "perturbed", metrics, n_eval=1, seed=42,
        padding_strength=0.1, junk_composition="random",
    )
    df = pd.read_csv(config.metrics_path("m1", "malimg"))
    assert df.iloc[0]["junk_composition"] == "random"
    assert df.iloc[0]["padding_strength"] == 0.1


def test_summarize_seeds_aggregates_mean_std_over_seed():
    metrics_a = compute_metrics([0, 1], [0, 1], FAMILY_ID_MAP)  # perfect
    metrics_b = compute_metrics([0, 1], [0, 0], FAMILY_ID_MAP)  # imperfect
    write_metrics_row("m0", "malimg", "in_distribution", metrics_a, n_eval=2, seed=42)
    write_metrics_row("m0", "malimg", "in_distribution", metrics_b, n_eval=2, seed=43)
    write_metrics_row("m0", "malimg", "in_distribution", metrics_a, n_eval=2, seed=44)

    summary = summarize_seeds(config.metrics_path("m0", "malimg"))

    assert len(summary) == 1  # one (stage, track, eval_dataset) group
    row = summary.iloc[0]
    assert row["accuracy_count"] == 3
    assert row["accuracy_mean"] == pytest.approx((1.0 + 0.5 + 1.0) / 3)
    assert row["accuracy_std"] > 0


def test_summarize_seeds_keeps_junk_compositions_separate():
    metrics = compute_metrics([0, 1], [0, 1], FAMILY_ID_MAP)
    write_metrics_row(
        "m1", "malimg", "perturbed", metrics, n_eval=2, seed=42,
        padding_strength=0.1, junk_composition="zero",
    )
    write_metrics_row(
        "m1", "malimg", "perturbed", metrics, n_eval=2, seed=42,
        padding_strength=0.1, junk_composition="random",
    )

    summary = summarize_seeds(config.metrics_path("m1", "malimg"))
    assert len(summary) == 2
    assert set(summary["junk_composition"]) == {"zero", "random"}
