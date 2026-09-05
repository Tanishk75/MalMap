"""Per-track dataset registries and splits (Module Interface Spec Section 1,
Data Dictionary Section 1).

Malimg layout expected under dataset_path: one subdirectory per family,
each containing that family's image files.

BIG2015 layout expected under dataset_path: a trainLabels.csv (Id,Class
columns) plus the matching .bytes files, either directly under dataset_path
or under dataset_path/bytes (ADR-0003 -- .bytes only, no .asm).

MOTIF layout expected under dataset_path: a motif_labels.csv (sample_id,md5,
family_label columns) plus the matching disarmed PE files named MOTIF_<md5>,
either directly under dataset_path or under dataset_path/bytes (ADR-0020,
protocols/motif_sampling.md).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import SPLIT_RATIOS, SPLIT_SEED, Track, family_map_path, registry_path

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif")

# Kaggle Microsoft Malware Classification Challenge (BIG2015) class names.
# Fixed by the competition; never re-derived from the data.
BIG2015_CLASS_NAMES = {
    1: "Ramnit",
    2: "Lollipop",
    3: "Kelihos_ver3",
    4: "Vundo",
    5: "Simda",
    6: "Tracur",
    7: "Kelihos_ver1",
    8: "Obfuscator.ACY",
    9: "Gatak",
}


def _build_malimg_registry(dataset_path: Path) -> pd.DataFrame:
    families = sorted(p.name for p in dataset_path.iterdir() if p.is_dir())
    if not families:
        raise ValueError(f"no family subdirectories found under {dataset_path}")

    rows = []
    for family in families:
        files = sorted(
            p for p in (dataset_path / family).iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )
        for f in files:
            rows.append({"family_label": family, "binary_path": str(f.resolve())})
    if not rows:
        raise ValueError(f"no image files found under {dataset_path}")

    df = pd.DataFrame(rows)
    df.insert(0, "sample_id", [f"malimg_{i:05d}" for i in range(len(df))])
    df["source_dataset"] = "malimg"
    df["track"] = "malimg"
    df["disasm_status"] = "not_attempted"  # PAUSED (V3) column, kept for schema stability
    return df


def _build_big2015_registry(dataset_path: Path) -> pd.DataFrame:
    labels_path = dataset_path / "trainLabels.csv"
    if not labels_path.exists():
        raise FileNotFoundError(f"expected {labels_path} (Id,Class columns)")

    labels = pd.read_csv(labels_path)
    bytes_dir = dataset_path / "bytes" if (dataset_path / "bytes").is_dir() else dataset_path

    rows = []
    missing = []
    for _, row in labels.iterrows():
        sample_bytes = bytes_dir / f"{row['Id']}.bytes"
        if not sample_bytes.exists():
            missing.append(row["Id"])
            continue
        rows.append({
            "sample_id": f"big2015_{row['Id']}",
            "binary_path": str(sample_bytes.resolve()),
            "family_label": BIG2015_CLASS_NAMES[int(row["Class"])],
        })
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} .bytes files listed in trainLabels.csv were not found "
            f"under {bytes_dir} (e.g. {missing[0]}.bytes)"
        )
    if not rows:
        raise ValueError(f"trainLabels.csv at {labels_path} produced zero samples")

    df = pd.DataFrame(rows)
    df["source_dataset"] = "big2015"
    df["track"] = "big2015"
    df["disasm_status"] = "not_attempted"
    return df


def _build_motif_registry(dataset_path: Path) -> pd.DataFrame:
    labels_path = dataset_path / "motif_labels.csv"
    if not labels_path.exists():
        raise FileNotFoundError(f"expected {labels_path} (sample_id,md5,family_label columns)")

    labels = pd.read_csv(labels_path)
    bytes_dir = dataset_path / "bytes" if (dataset_path / "bytes").is_dir() else dataset_path

    rows = []
    missing = []
    for _, row in labels.iterrows():
        sample_file = bytes_dir / f"MOTIF_{row['md5']}"
        if not sample_file.exists():
            missing.append(row["md5"])
            continue
        rows.append({
            "sample_id": row["sample_id"],
            "binary_path": str(sample_file.resolve()),
            "family_label": row["family_label"],
        })
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} MOTIF files listed in motif_labels.csv were not found "
            f"under {bytes_dir} (e.g. MOTIF_{missing[0]})"
        )
    if not rows:
        raise ValueError(f"motif_labels.csv at {labels_path} produced zero samples")

    df = pd.DataFrame(rows)
    df["source_dataset"] = "motif"
    df["track"] = "motif"
    df["disasm_status"] = "not_attempted"
    return df


def build_registry(track: Track, dataset_path: str) -> pd.DataFrame:
    """Builds and persists that track's registry to data_cache/registry_{track}.csv.

    There is deliberately no combined registry across tracks (ADR-0001).
    """
    path = Path(dataset_path)
    if not path.is_dir():
        raise FileNotFoundError(f"dataset_path does not exist: {path}")

    if track == "malimg":
        df = _build_malimg_registry(path)
    elif track == "big2015":
        df = _build_big2015_registry(path)
    elif track == "motif":
        df = _build_motif_registry(path)
    else:
        raise ValueError(f"unknown track {track!r}")

    id_map = get_family_id_map(track, df)
    df["family_id"] = df["family_label"].map(id_map)

    out_path = registry_path(track)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


def get_family_id_map(track: Track, registry: pd.DataFrame) -> dict[str, int]:
    """Builds and persists family_to_id_{track}.json.

    Called once per track and reused across every stage on that track. Never
    merged across tracks (ADR-0001). Families are sorted alphabetically so the
    mapping is stable across reruns, independent of file-system iteration order.
    """
    families = sorted(registry["family_label"].unique())
    id_map = {family: i for i, family in enumerate(families)}

    out_path = family_map_path(track)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(id_map, f, indent=2, sort_keys=True)
    return id_map


def make_splits(
    registry: pd.DataFrame,
    seed: int = SPLIT_SEED,
    ratios: tuple[float, float, float] = SPLIT_RATIOS,
) -> pd.DataFrame:
    """Adds a stratified 'split' column on a copy of registry, then persists
    it in place to that track's registry CSV (registry must be single-track).

    Splits per family so every split sees every family in roughly the given
    proportion. A family with fewer than 3 samples cannot supply all three
    splits and goes entirely to train.

    Must regenerate byte-identically from the same seed: families are visited
    in a fixed (sorted) order against a single RandomState stream, never one
    RandomState per family.
    """
    if abs(sum(ratios) - 1.0) > 1e-9:
        raise ValueError(f"ratios must sum to 1.0, got {ratios}")
    tracks = registry["track"].unique()
    if len(tracks) != 1:
        raise ValueError(f"make_splits requires a single-track registry, got {tracks}")

    out = registry.copy()
    split = pd.Series("train", index=out.index, dtype=object)
    rng = np.random.RandomState(seed)

    for family in sorted(out["family_label"].unique()):
        idx = out.index[out["family_label"] == family].to_numpy().copy()
        rng.shuffle(idx)
        n = len(idx)
        if n < 3:
            continue  # too few to give every split a sample; all stay 'train'

        n_test = max(1, round(n * ratios[2]))
        n_val = max(1, round(n * ratios[1]))
        if n_val + n_test >= n:
            n_val, n_test = 1, 1
        n_train = n - n_val - n_test

        split.loc[idx[:n_train]] = "train"
        split.loc[idx[n_train:n_train + n_val]] = "val"
        split.loc[idx[n_train + n_val:]] = "test"

    out["split"] = split

    out_path = registry_path(tracks[0])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    return out
