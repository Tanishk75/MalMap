"""Tests for src/data/registry.py using synthetic directory layouts --
no real Malimg/BIG2015 data is needed to verify this logic."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from PIL import Image

import src.config as config
from src.data.registry import (
    BIG2015_CLASS_NAMES,
    build_registry,
    get_family_id_map,
    make_splits,
)


@pytest.fixture(autouse=True)
def isolated_data_cache(tmp_path, monkeypatch):
    """Every test in this file must write under a throwaway data_cache, never
    the real project one -- registry.py resolves paths via src.config at call
    time, so patching the config module's DATA_CACHE here is sufficient."""
    monkeypatch.setattr(config, "DATA_CACHE", tmp_path / "data_cache")


def _make_malimg_tree(root, families_and_counts):
    for family, count in families_and_counts.items():
        d = root / family
        d.mkdir(parents=True)
        for i in range(count):
            Image.new("L", (32, 32), color=i % 256).save(d / f"sample_{i:03d}.png")


def _make_big2015_tree(root, class_and_counts):
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    sample_id = 0
    for class_num, count in class_and_counts.items():
        for _ in range(count):
            (root / f"{sample_id}.bytes").write_text("00 01 02 03\n")
            rows.append({"Id": sample_id, "Class": class_num})
            sample_id += 1
    pd.DataFrame(rows).to_csv(root / "trainLabels.csv", index=False)


def test_build_registry_malimg(tmp_path):
    raw = tmp_path / "raw_malimg"
    _make_malimg_tree(raw, {"Allaple.A": 5, "Yuner.A": 3})

    df = build_registry("malimg", str(raw))

    assert len(df) == 8
    assert set(df["family_label"]) == {"Allaple.A", "Yuner.A"}
    assert set(df["track"]) == {"malimg"}
    assert set(df["source_dataset"]) == {"malimg"}
    assert df["sample_id"].is_unique
    assert all(Path(p).exists() for p in df["binary_path"])
    assert set(df["family_id"]) == {0, 1}
    assert config.registry_path("malimg").exists()
    assert config.family_map_path("malimg").exists()


def test_build_registry_malimg_missing_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_registry("malimg", str(tmp_path / "does_not_exist"))


def test_build_registry_malimg_no_families(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError):
        build_registry("malimg", str(empty))


def test_build_registry_big2015(tmp_path):
    raw = tmp_path / "raw_big2015"
    _make_big2015_tree(raw, {1: 4, 3: 6})  # Ramnit, Kelihos_ver3

    df = build_registry("big2015", str(raw))

    assert len(df) == 10
    assert set(df["family_label"]) == {"Ramnit", "Kelihos_ver3"}
    assert set(df["track"]) == {"big2015"}
    assert df["sample_id"].str.startswith("big2015_").all()


def test_build_registry_big2015_missing_bytes_file(tmp_path):
    raw = tmp_path / "raw_big2015_missing"
    raw.mkdir()
    pd.DataFrame([{"Id": 0, "Class": 1}]).to_csv(raw / "trainLabels.csv", index=False)
    # deliberately do not write 0.bytes
    with pytest.raises(FileNotFoundError):
        build_registry("big2015", str(raw))


def _make_motif_tree(root, family_and_counts):
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for family, count in family_and_counts.items():
        for i in range(count):
            md5 = f"{family[:4]}{i:028d}"
            (root / f"MOTIF_{md5}").write_bytes(b"\x00disarmed-pe-bytes")
            rows.append({
                "sample_id": f"motif_{md5}",
                "md5": md5,
                "family_label": family,
            })
    pd.DataFrame(rows).to_csv(root / "motif_labels.csv", index=False)


def test_build_registry_motif(tmp_path):
    raw = tmp_path / "raw_motif"
    _make_motif_tree(raw, {"icedid": 5, "azorult": 3})

    df = build_registry("motif", str(raw))

    assert len(df) == 8
    assert set(df["family_label"]) == {"icedid", "azorult"}
    assert set(df["track"]) == {"motif"}
    assert set(df["source_dataset"]) == {"motif"}
    assert df["sample_id"].is_unique
    assert all(Path(p).exists() for p in df["binary_path"])
    assert config.registry_path("motif").exists()
    assert config.family_map_path("motif").exists()


def test_build_registry_motif_missing_file(tmp_path):
    raw = tmp_path / "raw_motif_missing"
    raw.mkdir()
    pd.DataFrame([{"sample_id": "motif_abc", "md5": "abc", "family_label": "icedid"}]).to_csv(
        raw / "motif_labels.csv", index=False
    )
    # deliberately do not write MOTIF_abc
    with pytest.raises(FileNotFoundError):
        build_registry("motif", str(raw))


def test_get_family_id_map_sorted_and_deterministic():
    registry = pd.DataFrame({"family_label": ["Zeta", "Alpha", "Alpha", "Mid"]})
    id_map = get_family_id_map("malimg", registry)
    assert id_map == {"Alpha": 0, "Mid": 1, "Zeta": 2}


def test_make_splits_every_family_represented():
    registry = pd.DataFrame({
        "sample_id": [f"s{i}" for i in range(30)],
        "family_label": ["A"] * 20 + ["B"] * 10,
        "track": "malimg",
    })

    out = make_splits(registry, seed=42, ratios=(0.7, 0.15, 0.15))

    assert set(out["split"].unique()) <= {"train", "val", "test"}
    for family in ("A", "B"):
        fam_splits = set(out.loc[out["family_label"] == family, "split"])
        assert fam_splits == {"train", "val", "test"}


def test_make_splits_tiny_family_goes_to_train():
    registry = pd.DataFrame({
        "sample_id": ["s0", "s1"],
        "family_label": ["Rare", "Rare"],
        "track": "big2015",
    })
    out = make_splits(registry, seed=42)
    assert set(out["split"]) == {"train"}


def test_make_splits_deterministic_across_calls():
    registry = pd.DataFrame({
        "sample_id": [f"s{i}" for i in range(50)],
        "family_label": (["A"] * 25 + ["B"] * 25),
        "track": "malimg",
    })
    out1 = make_splits(registry, seed=42)
    out2 = make_splits(registry, seed=42)
    assert (out1["split"].to_numpy() == out2["split"].to_numpy()).all()


def test_make_splits_rejects_multi_track_registry():
    registry = pd.DataFrame({
        "sample_id": ["s0", "s1"],
        "family_label": ["A", "B"],
        "track": ["malimg", "big2015"],
    })
    with pytest.raises(ValueError):
        make_splits(registry, seed=42)


def test_make_splits_rejects_bad_ratios():
    registry = pd.DataFrame({
        "sample_id": ["s0"],
        "family_label": ["A"],
        "track": ["malimg"],
    })
    with pytest.raises(ValueError):
        make_splits(registry, seed=42, ratios=(0.5, 0.5, 0.5))


def test_big2015_class_names_fixed():
    assert BIG2015_CLASS_NAMES[1] == "Ramnit"
    assert BIG2015_CLASS_NAMES[9] == "Gatak"
    assert len(BIG2015_CLASS_NAMES) == 9
