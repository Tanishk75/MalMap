"""Builds the frozen MOTIF subsample (ADR-0020, protocols/motif_sampling.md).

Runs locally, not on Kaggle -- MOTIF.7z is 1.58GB, well under any disk-quota
concern the BIG2015 notebook had to work around. Requires a clone of
https://github.com/boozallen/MOTIF with `git lfs pull --include=MOTIF.7z`
already run, so both dataset/motif_dataset.jsonl and MOTIF.7z are present.

Usage:
    python scripts/build_motif_subsample.py --motif-repo <path to MOTIF clone>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import py7zr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import MOTIF_SAMPLE_SEED, MOTIF_SAMPLES_PER_FAMILY, MOTIF_TOP_N_FAMILIES
from src.data.registry import build_registry, make_splits

MOTIF_PASSWORD = "i_assume_all_risk_opening_malware"
EXPECTED_TOTAL = MOTIF_TOP_N_FAMILIES * MOTIF_SAMPLES_PER_FAMILY


def select_frozen_sample(motif_dataset_jsonl: Path) -> pd.DataFrame:
    """Reproduces protocols/motif_sampling.md's selection rule exactly."""
    records = []
    with open(motif_dataset_jsonl, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            records.append({"md5": rec["md5"], "family_label": rec["reported_family"]})
    df = pd.DataFrame(records)

    counts = df["family_label"].value_counts()
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    top_families = [fam for fam, _ in ranked[:MOTIF_TOP_N_FAMILIES]]

    for fam in top_families:
        available = int((df["family_label"] == fam).sum())
        if available < MOTIF_SAMPLES_PER_FAMILY:
            raise AssertionError(
                f"family {fam!r} has only {available} samples, below the frozen cap of "
                f"{MOTIF_SAMPLES_PER_FAMILY} -- protocols/motif_sampling.md is stale, fix the "
                "protocol before extracting anything"
            )

    rng = np.random.RandomState(MOTIF_SAMPLE_SEED)
    selected_rows = []
    for fam in sorted(top_families):
        candidates = np.array(sorted(df.loc[df["family_label"] == fam, "md5"].tolist()))
        rng.shuffle(candidates)
        for md5 in candidates[:MOTIF_SAMPLES_PER_FAMILY]:
            selected_rows.append({"md5": md5, "family_label": fam})

    out = pd.DataFrame(selected_rows)
    out.insert(0, "sample_id", "motif_" + out["md5"])
    if len(out) != EXPECTED_TOTAL:
        raise AssertionError(f"selected {len(out)} samples, expected exactly {EXPECTED_TOTAL}")
    return out


def _still_missing(out_dir: Path, by_basename: dict) -> dict:
    return {
        base: name for base, name in by_basename.items()
        if not (out_dir / base).exists() and next(out_dir.rglob(base), None) is None
    }


def extract_selected(motif_7z: Path, selected: pd.DataFrame, out_dir: Path) -> None:
    """Batch-extracts all targets in one decompression pass (fast), retrying
    only the still-missing subset a few times if an attempt raises -- observed
    once to lose a single file to what turned out to be two extraction
    processes racing on the same output directory, not a py7zr bug per se.
    Idempotent: an interrupted run can be re-run and picks up where it left
    off, whether from a previous partial success or a genuinely fresh start."""
    wanted_basenames = {f"MOTIF_{md5}" for md5 in selected["md5"]}
    out_dir.mkdir(parents=True, exist_ok=True)

    with py7zr.SevenZipFile(motif_7z, mode="r", password=MOTIF_PASSWORD) as archive:
        by_basename = {}
        for name in archive.getnames():
            base = Path(name).name
            if base in wanted_basenames:
                by_basename[base] = name
        missing = wanted_basenames - by_basename.keys()
        if missing:
            raise FileNotFoundError(
                f"{len(missing)} selected MOTIF files not found in archive, e.g. "
                f"{sorted(missing)[0]}"
            )

        for attempt in range(5):
            remaining = _still_missing(out_dir, by_basename)
            if not remaining:
                break
            print(f"  extraction attempt {attempt + 1}: {len(remaining)} files remaining")
            archive.reset()
            try:
                archive.extract(path=out_dir, targets=list(remaining.values()))
            except Exception as e:
                print(f"    attempt {attempt + 1} raised {e!r}, will retry what's still missing")
        else:
            remaining = _still_missing(out_dir, by_basename)
            if remaining:
                raise RuntimeError(f"failed to extract after retries: {sorted(remaining)}")

    # Flatten in case the archive stored files under a subdirectory.
    for base in wanted_basenames:
        target = out_dir / base
        if target.exists():
            continue
        found = next(out_dir.rglob(base), None)
        if found is None:
            raise FileNotFoundError(f"{base} was in the extraction list but not on disk after extract")
        found.rename(target)


def verify_pefile_parses(bytes_dir: Path, sample_ids: list[str]) -> tuple[int, int]:
    import pefile

    parsed = 0
    for md5 in sample_ids:
        path = bytes_dir / f"MOTIF_{md5}"
        try:
            pe = pefile.PE(str(path))
            pe.close()
            parsed += 1
        except Exception:
            pass
    return parsed, len(sample_ids)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--motif-repo", required=True, help="path to a cloned boozallen/MOTIF repo")
    parser.add_argument("--out", default="data/raw/motif", help="output directory")
    args = parser.parse_args()

    motif_repo = Path(args.motif_repo)
    motif_dataset_jsonl = motif_repo / "dataset" / "motif_dataset.jsonl"
    motif_7z = motif_repo / "MOTIF.7z"
    out_dir = Path(args.out)
    bytes_dir = out_dir / "bytes"

    print("Selecting frozen sample per protocols/motif_sampling.md ...")
    selected = select_frozen_sample(motif_dataset_jsonl)
    print(f"  {len(selected)} samples across {selected['family_label'].nunique()} families")

    print(f"Extracting from {motif_7z} (password-protected) ...")
    extract_selected(motif_7z, selected, bytes_dir)
    print(f"  extracted {len(list(bytes_dir.glob('MOTIF_*')))} files to {bytes_dir}")

    labels_path = out_dir / "motif_labels.csv"
    selected.to_csv(labels_path, index=False)
    print(f"  wrote {labels_path}")

    print("Building registry and splits ...")
    df = build_registry("motif", str(out_dir))
    df = make_splits(df)
    print(f"  registry: {len(df)} rows, splits {df['split'].value_counts().to_dict()}")

    print("Verifying pefile can parse at least one sample (Milestone 0 exit gate) ...")
    check_ids = selected["md5"].tolist()[:20]
    parsed, total = verify_pefile_parses(bytes_dir, check_ids)
    print(f"  pefile parsed {parsed}/{total} sampled files")
    if parsed == 0:
        print(
            "  WARNING: pefile parsed none of the sampled files. FR6 falls back to the "
            "benign-binary mechanism check (ADR-0018) per ADR-0020's contingency."
        )


if __name__ == "__main__":
    main()
