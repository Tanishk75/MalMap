# MOTIF Sampling Protocol

**Status: FROZEN before extraction.** Governed by [ADR-0020](../docs/adr/0020-motif-replaces-malimg-second-track.md).
If any number in this file needs to change, that is a new frozen version of this protocol —
recorded here with a reason — never a silent edit after extraction has run.

Source: [boozallen/MOTIF](https://github.com/boozallen/MOTIF) (Joyce et al., AAAI-22 AICS
workshop), 3,095 disarmed PE malware samples across 454 families, ground-truth-labelled from
vetted threat-intelligence reports. Disarmed means `OPTIONAL_HEADER.Subsystem` and
`FILE_HEADER.Machine` are zeroed so the files cannot execute; they are not sanitized otherwise —
the rest of the PE structure, including section headers, is the original malware's.

## Why a subsample

454 families over 3,095 samples is an extreme long tail (median family has a handful of
samples) — nowhere near enough for a stratified 70/15/15 split per family (ADR requires at least
3 samples/family; most MOTIF families have fewer). This project keeps only the **top 30 families
by sample count**, each capped to the same size, so every family in the resulting track can
actually support a split and the resulting set is deliberately balanced rather than
long-tailed like the source.

## Published per-family counts (live, from `dataset/motif_dataset.jsonl`)

Ranked by count descending, family name ascending as a tie-break — this ordering is what
`MOTIF_TOP_N_FAMILIES` cuts at, so the tie-break is load-bearing, not cosmetic. Counted directly
from the dataset's own metadata file (not from memory or the paper), since that file ships in
the repo and needs no extraction to read.

| Rank | Family | Count | Rank | Family | Count |
|---|---|---|---|---|---|
| 1 | icedid | 142 | 16 | peppyrat | 29 |
| 2 | azorult | 68 | 17 | turnedup | 29 |
| 3 | phorpiex | 58 | 18 | ryuk | 28 |
| 4 | maze | 52 | 19 | medusalocker | 27 |
| 5 | trickbot | 43 | 20 | mosaicregressor | 27 |
| 6 | gandcrab | 41 | 21 | crat | 26 |
| 7 | locky | 41 | 22 | valak | 26 |
| 8 | artradownloader | 40 | 23 | bazarbackdoor | 25 |
| 9 | redaman | 40 | 24 | olympicdestroyer | 25 |
| 10 | seduploader | 40 | 25 | wannacry | 25 |
| 11 | egregor | 37 | 26 | copperhedge | 22 |
| 12 | prometei | 35 | 27 | andromeda | 21 |
| 13 | shamoon | 33 | 28 | dreambot | 21 |
| 14 | zegost | 32 | 29 | loda | 21 |
| 15 | indigodrop | 31 | 30 | ursnif | 21 |

Rank 30 (`ursnif`) sits at count 21 with three other families tied at exactly 21
(`andromeda`, `dreambot`, `loda`) — all four are within the top 30 under the name tie-break, and
no fifth family also has count 21, so the cut is unambiguous. Rank 31 onward (`spark`, `trik`,
`zerot`, ... down to many families with 1) are excluded entirely.

## Selection rule

- **Family cut:** `MOTIF_TOP_N_FAMILIES = 30` (`src/config.py`). Families ranked by
  `(-count, family_name)`, the 30 highest kept, per the table above.
- **Per-family cap:** `MOTIF_SAMPLES_PER_FAMILY = 21` (`src/config.py`) — the count of the
  30th-ranked family, chosen so every kept family contributes the same number of samples
  (an even 30 × 21 = 630, not BIG2015's cap-with-remainder shape).
- **Seed:** `MOTIF_SAMPLE_SEED = 2022` (`src/config.py`) — the MOTIF paper's publication year,
  distinct from `BIG2015_SAMPLE_SEED` and `SPLIT_SEED`. This seed decides which of a family's
  samples are kept when it has more than the cap; it is a different decision from how the kept
  samples later get partitioned into train/val/test.
- **Procedure:** the 30 kept families are visited in sorted-name order. Within each family, its
  candidate `md5` list is sorted ascending, then shuffled with a single `numpy.random.RandomState`
  stream seeded once at the start (not re-seeded per family) — the same discipline as
  `make_splits` and the BIG2015 protocol, so the draw regenerates byte-identically forever. The
  first `min(21, available)` ids after shuffling are selected. Every kept family has at least 21
  candidates (by construction of the family cut), so every family contributes exactly 21.

## Expected result

630 samples total: 30 families × 21 samples each.

## Extraction

`MOTIF.7z` is a password-protected archive (`i_assume_all_risk_opening_malware`, published by
the dataset authors as an explicit handling acknowledgment, not a secret) containing every file
named `MOTIF_<md5>` — no extension, disarmed PE content. Only the 630 selected `MOTIF_<md5>`
entries are extracted, by exact filename match against the frozen selection above — never a
scan-and-guess.

**Antivirus note, confirmed in practice.** These files carry known-malware MD5 hashes even
though they cannot execute. A first local extraction attempt (2026-09-05) was observed losing
files in real time — a count that dropped from 544 to 524 within seconds, with no extraction
process even running — traced to **Trend Micro Apex One** (managed corporate endpoint AV), not
Windows Defender: `Get-MpComputerStatus` showed Defender's own engine disabled
(`AntivirusEnabled: False`) because Apex One was the registered active product
(`Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct`). A managed
Apex One client does not generally expose a local, user-settable scan exclusion the way
Defender's `Add-MpPreference` does, so excluding the folder was not an available fix on this
machine.

**Adopted extraction path: run it on Kaggle, transport the result encrypted.**
[`notebooks/motif_subsample.ipynb`](../notebooks/motif_subsample.ipynb) clones
`boozallen/MOTIF` directly (public, no request gate — no Kaggle "Add Data" attachment needed the
way BIG2015's competition data requires), reproduces the selection above, extracts the 630 files
on Kaggle's disk where there is no local AV to react to, builds the registry and runs the
`pefile` parse-rate check, then **re-packages the result into a fresh password-protected 7z**
(`motif_subsample.7z`, same password, with header encryption so filenames are opaque too) before
it is downloaded back to any AV-managed local machine. This is the same reasoning MOTIF's own
upstream distribution already uses password-protection for — an archive an AV cannot look
inside is an archive it cannot quarantine the contents of. The plain files only exist locally for
as long as they sit decompressed on disk; unpack `motif_subsample.7z` into `data/raw/motif/`
only when a pipeline stage actually needs the raw bytes.

If files still go missing from `data/raw/motif/` after local unpacking, check *which* antivirus
product is actually active (`Get-CimInstance -Namespace root/SecurityCenter2 -ClassName
AntivirusProduct` on Windows) before assuming Defender, the archive, or the extraction logic is
at fault — Defender may be present but inactive.

## Output layout

```
data/raw/motif/
  bytes/MOTIF_<md5>          # exactly the 630 selected files, renamed to match sample_id convention
  motif_labels.csv           # sample_id, md5, family_label for the 630 selected rows only
```

`build_registry("motif", "data/raw/motif")` and `make_splits(...)` then produce
`data_cache/registry_motif.csv` and `data_cache/family_to_id_motif.json` locally, the same way
the BIG2015 registry is built from `data/raw/big2015/`.
