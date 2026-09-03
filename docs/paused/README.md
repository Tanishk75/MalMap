# Paused — the graph branch and trimodal fusion

This folder holds the design for the parts of the project that are **built but not being
delivered**: the control-flow-graph branch (M4), the trimodal fusion stage (M5), and everything
that exists only to support them.

**Nothing here is cancelled or wrong.** Every decision in this folder was reached deliberately
and still stands. The work is paused, not the reasoning. No resumption trigger has been set.

The delivered project is the image + audio bimodal system described in
[`../Development_Plan_Multimodal_Malware.md`](../Development_Plan_Multimodal_Malware.md) and
governed by [`../adr/`](../adr/). That system is complete in its own terms — a multimodal
classifier with two genuine views of a sample — not a trimodal design with a branch missing.
Active documents are written that way, and this folder is why they can be: the graph work is
preserved here rather than apologised for there.

See [`../adr/0017-v2-bimodal-scope.md`](../adr/0017-v2-bimodal-scope.md) for the scope decision
itself.

## What is here

| Path | What it is |
|---|---|
| [`adr/0004-instrument-set-not-training-corpus.md`](./adr/0004-instrument-set-not-training-corpus.md) | Real PE binaries as a small curated instrument set |
| [`adr/0005-no-raw-malware-on-the-workstation.md`](./adr/0005-no-raw-malware-on-the-workstation.md) | Malware handling policy — still `proposed`, never confirmed |
| [`adr/0009-asm-parsing-over-live-disassembly.md`](./adr/0009-asm-parsing-over-live-disassembly.md) | The graph branch parses BIG2015's shipped `.asm` |
| [`adr/0010-nested-two-stage-fusion.md`](./adr/0010-nested-two-stage-fusion.md) | Fusion is nested (M3 + M4 into M5), not a flat concatenation |
| [`adr/0012-m3-fallback-on-missing-graph.md`](./adr/0012-m3-fallback-on-missing-graph.md) | A sample with no CFG falls back to M3 at inference |
| [`Milestones_3_and_4_graph_and_trimodal.md`](./Milestones_3_and_4_graph_and_trimodal.md) | The two extracted milestone plans, with their gates intact |

Elsewhere in `docs/`, paused material is marked in place rather than extracted — the
architecture, data dictionary, module interface spec and evaluation spec each carry
`PAUSED (V3)` markers on their M4 and M5 sections. Pulling those apart would have gutted five
coherent specifications and made a restart harder than it needs to be.

## If work resumes

Read this folder before touching anything, in this order: ADR-0017 for what was scoped out and
why, then `Milestones_3_and_4_graph_and_trimodal.md` for the plan, then the ADRs above. Then:

1. Re-extract BIG2015's `.asm` files. V2 extracts `.bytes` only (ADR-0003), so the shipped
   disassembly the graph branch depends on is not on disk. This is a full re-extraction, and it
   was accepted knowingly as the price of a smaller V2.
2. Settle ADR-0005 before any instrument-set work begins. It is still `proposed` and was never
   confirmed or overridden.
3. Restore the `PAUSED (V3)` sections in the active specs, and re-add M4/M5 rows to the
   comparison tables in the evaluation spec.
4. Reinstate the M5 path-coverage metric (ADR-0012). It is dormant, not deleted — a metric that
   only means something once M5 exists.
