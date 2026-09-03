# Multimodal Malware Family Classification

Classifies Windows PE malware into known families by fusing **two views of one
byte stream**: an entropy-aware byte image and an audio spectrogram of the same
bytes. A solo university capstone — report, demo, viva.

The claim under test is not that any single view works. It is that fusing two
views beats either alone, that the fused representation transfers across
corpora, and that fusion inherits robustness rather than fragility when the
bytes are tampered with.

## Where the design lives

Read [`docs/README.md`](docs/README.md) first — it carries the reading order and
the precedence rules. In short:

- [`docs/CONTEXT.md`](docs/CONTEXT.md) — the glossary. Wins over wording anywhere else.
- [`docs/adr/`](docs/adr/) — one decision per file, plus what is deliberately still open.
- [`docs/Development_Plan_Multimodal_Malware.md`](docs/Development_Plan_Multimodal_Malware.md) — the milestone ladder and its exit gates.
- [`docs/paused/`](docs/paused/) — the graph branch and trimodal fusion: designed, preserved, not being built (ADR-0017).

## The ladder

| Stage | What it is | Tag |
|---|---|---|
| M0 | Plain grayscale byte image — the reference every delta is measured against | `m0-grayscale-{track}` |
| M1 | Entropy-aware two-channel image | `m1-image-{track}` |
| M2 | Spectrogram of the byte stream | `m2-audio-{track}` |
| M3 | Image + audio fusion, branches frozen | `m3-bimodal-{track}` |

Everything runs twice, once per **track** — Malimg and BIG2015 — with separate
label spaces, splits, caches and checkpoints. They are never merged: a combined
34-class problem lets a model score well by identifying the dataset rather than
the family, which would inflate every number this project reports (ADR-0001).

Every stage is trained under three seeds, and every headline delta is reported
as mean ± std (ADR-0013).

## Layout

```
src/          data layer, preprocessing, models, evaluation, explainability
tests/        unit tests that run without the datasets
notebooks/    per-stage training and the demo (ADR-0016)
protocols/    frozen protocol files -- sampling, recovery, padding
data_cache/   registries, splits, cached tensors + offset maps   (gitignored)
checkpoints/  per-track, per-seed weights                        (gitignored)
results/      metrics CSVs, figures, comparison tables           (gitignored)
logs/         run logs                                            (gitignored)
docs/         the design: ADRs, glossary, plan, specifications
```

Caches and checkpoints are gitignored because they are regenerable from the code
and the protocol files. The demo's committed artifacts are the deliberate
exception (ADR-0016) — the demo must run offline from a clean checkout.

## Setup

Python **3.12** — not 3.14, whose torch wheels lag.

```bash
py -3.12 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m pytest
```

Training runs on Kaggle or Colab GPU (ADR-0006); the local install is CPU-only
and exists for smoke tests and shape checks.

## Status

Milestone 0 — foundations. The repository skeleton, seed policy and tag
convention are fixed in [`src/config.py`](src/config.py). Byte recovery
([`src/data/recover.py`](src/data/recover.py)) is written and unit-tested
against synthesised images; it has not yet been run against Malimg, because the
corpus has not been acquired. That acquisition, and the byte-recovery gate it
feeds, is the next step and the highest-consequence one in the project.
