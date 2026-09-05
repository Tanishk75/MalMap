# Architecture Decision Records

One decision per file. Numbering is sequential; the highest number wins ties on
recency, not authority. Vocabulary is in [`../CONTEXT.md`](../CONTEXT.md); the plan
these decisions shape is in
[`../Development_Plan_Multimodal_Malware.md`](../Development_Plan_Multimodal_Malware.md).

Where an ADR contradicts one of the older specification documents, the ADR wins and
the older document has been reconciled to match.

Numbers have gaps. Five ADRs moved to [`../paused/adr/`](../paused/adr/) with the graph branch
(ADR-0017) and kept their numbers, because renumbering would break citations across seven
documents and make a resumption harder to read. They are listed below so nothing looks lost.

| # | Decision | Status |
|---|---|---|
| [0001](./0001-two-parallel-corpus-tracks.md) | Two parallel corpus tracks, not one merged label space | accepted |
| [0002](./0002-malimg-original-resolution-only.md) | Only the original variable-resolution Malimg distribution is usable | accepted |
| [0003](./0003-big2015-stratified-subsample.md) | BIG2015 is a stratified per-family subsample of `.bytes` only | accepted |
| 0004 | *Real PE binaries as a curated instrument set* — [paused](../paused/adr/0004-instrument-set-not-training-corpus.md) | paused |
| 0005 | *Raw malware binaries never touch the workstation* — [paused](../paused/adr/0005-no-raw-malware-on-the-workstation.md) | paused, still **proposed** |
| [0006](./0006-kaggle-as-primary-compute.md) | Kaggle is the primary environment for BIG2015; Colab is unconstrained | accepted |
| [0007](./0007-m0-grayscale-baseline.md) | A plain-grayscale M0 baseline is the first checkpoint on every track | accepted |
| [0008](./0008-offset-map-alongside-resized-images.md) | Image tensors may be resized, but each carries an explicit byte-offset map | accepted |
| 0009 | *The graph branch parses BIG2015's shipped `.asm`* — [paused](../paused/adr/0009-asm-parsing-over-live-disassembly.md) | paused |
| 0010 | *Fusion is nested (M3 + M4 into M5)* — [paused](../paused/adr/0010-nested-two-stage-fusion.md) | paused |
| [0011](./0011-frozen-branch-staged-training.md) | Fusion stages train with their branches frozen | accepted |
| 0012 | *A sample with no CFG falls back to M3 at inference* — [paused](../paused/adr/0012-m3-fallback-on-missing-graph.md) | paused |
| [0013](./0013-macro-f1-primary-metric.md) | Macro-F1 over three seeds is the single primary comparison metric | accepted |
| [0014](./0014-fr5-as-embedding-probe.md) | FR5 generalization is measured as an embedding probe | accepted |
| [0015](./0015-robustness-as-fusion-inheritance.md) | FR7 asks whether fusion inherits robustness | accepted |
| [0016](./0016-no-serving-layer.md) | No serving layer; the demo is the entropy comparison | accepted |
| [0017](./0017-v2-bimodal-scope.md) | The delivered system is bimodal; the graph branch is paused | accepted |
| [0018](./0018-benign-pe-mechanism-fallback.md) | Benign Windows binaries are FR6's mechanism fallback | accepted |
| [0019](./0019-malimg-paused-big2015-sole-track.md) | Malimg is paused; BIG2015 is the project's sole delivered track | accepted, superseded by 0020 |
| [0020](./0020-motif-replaces-malimg-second-track.md) | MOTIF replaces Malimg as the project's second track | accepted |

## Decisions deliberately not yet made

These are open on purpose. Each is pinned to the milestone that settles it, so none of
them is silently assumed in the meantime.

| Open question | Settled at |
|---|---|
| Entropy window size | Milestone 1 (swept, not guessed) |
| Audio sample rate and mel-band count | Milestone 2 |
| Padding strengths to sweep | Milestone 6 |
| Whether BODMAS is worth acquiring at all, given BIG2015 and MOTIF already probe each other | Milestone 5 |

Two questions left this list when the graph branch was paused — the instruction-type bucket
scheme behind `node_feature_dim`, and `radare2` versus `angr` — and are recorded in
[`../paused/`](../paused/). The seed-repetition budget left it by being answered: three seeds,
fixed in ADR-0013.
