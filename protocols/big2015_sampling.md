# BIG2015 Sampling Protocol

**Status: FROZEN before extraction.** Governed by [ADR-0003](../docs/adr/0003-big2015-stratified-subsample.md)
and [ADR-0006](../docs/adr/0006-kaggle-as-primary-compute.md). If any number in this file needs
to change, that is a new frozen version of this protocol — recorded here with a reason — never a
silent edit after extraction has run.

Executed by [`notebooks/big2015_subsample.ipynb`](../notebooks/big2015_subsample.ipynb).

## Why a subsample

`train.7z` extracts to roughly 200GB for `.bytes` + `.asm` combined. This project uses `.bytes`
only (ADR-0003) and, on top of that, extracts a fixed per-family subsample rather than the full
corpus — the free-tier Kaggle working-disk quota cannot hold the full `.bytes` set at comfortable
margin once cache and registry overhead are counted.

## Published per-family counts

The Microsoft Malware Classification Challenge (BIG 2015) train set has 10,868 labelled samples
across 9 families. These counts are well known from the competition's public `trainLabels.csv`:

| Class | Family | Published count |
|---|---|---|
| 1 | Ramnit | 1,541 |
| 2 | Lollipop | 2,478 |
| 3 | Kelihos_ver3 | 2,942 |
| 4 | Vundo | 475 |
| 5 | Simda | 42 |
| 6 | Tracur | 751 |
| 7 | Kelihos_ver1 | 398 |
| 8 | Obfuscator.ACY | 1,228 |
| 9 | Gatak | 1,013 |
| | **Total** | **10,868** |

**These are recorded from memory of a well-known public dataset, not read from a live file.**
The notebook's first job is to load the attached `trainLabels.csv` and recompute this table
itself. If the live counts disagree with this table, the notebook stops before extracting
anything and this file gets corrected first — a silent mismatch here would make the "exact
match" exit-gate check in the Development Plan meaningless.

## Selection rule

- **Cap:** `BIG2015_SAMPLES_PER_FAMILY = 100` (`src/config.py`). A family with fewer than 100
  available samples contributes all of them (this only affects Simda, at 42).
- **Seed:** `BIG2015_SAMPLE_SEED = 2015` (`src/config.py`), separate from `SPLIT_SEED` — this
  seed decides which raw samples exist in the track's corpus at all, a different decision from
  how those samples later get partitioned into train/val/test.
- **Procedure:** families are visited in a fixed order (sorted by name). Within each family, the
  candidate `Id` list is sorted ascending, then shuffled with a single `numpy.random.RandomState`
  stream seeded once at the start (not re-seeded per family — the same discipline as
  `make_splits` in `src/data/registry.py`, so the draw regenerates byte-identically forever). The
  first `min(cap, available)` ids after shuffling are selected.

## Expected result

| Class | Family | Selected |
|---|---|---|
| 1 | Ramnit | 100 |
| 2 | Lollipop | 100 |
| 3 | Kelihos_ver3 | 100 |
| 4 | Vundo | 100 |
| 5 | Simda | 42 |
| 6 | Tracur | 100 |
| 7 | Kelihos_ver1 | 100 |
| 8 | Obfuscator.ACY | 100 |
| 9 | Gatak | 100 |
| | **Total** | **842** |

## Extraction scope and safety ceiling

Only `<id>.bytes` for the 842 selected ids is extracted from `train.7z` — never `.asm`, and never
any id outside the selected list. Per-file uncompressed sizes are read from the archive index
before extracting anything; if the projected total exceeds a **15GB safety ceiling**, the notebook
aborts extraction rather than risk exhausting the Kaggle working-disk quota. If that happens, the
fix is to lower `BIG2015_SAMPLES_PER_FAMILY` here and re-freeze this file — not to extract anyway.

## Output layout

Written to `/kaggle/working/big2015_subsample/`:

```
big2015_subsample/
  bytes/<id>.bytes          # exactly the 842 selected files
  trainLabels.csv           # subset to the 842 selected rows only
  registry_big2015.csv      # built by src.data.registry.build_registry
  family_to_id_big2015.json # built by src.data.registry.get_family_id_map
```

`registry_big2015.csv` includes the seeded 70/15/15 split column (`src.data.registry.make_splits`,
`SPLIT_SEED` from `src/config.py`) so the exported directory is immediately usable by
`build_registry("big2015", ...)` on any later machine without re-running Kaggle.

Per ADR-0006, this directory must be exported (Kaggle Dataset output or downloaded) before the
session ends — nothing here survives session termination on its own.
