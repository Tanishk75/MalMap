---
status: accepted
---

# The delivered system is bimodal: image and audio, with the graph branch paused

The project is delivered as the image + audio fusion system — M0 through M3 on both tracks, plus
the generalization probe, the robustness study and the demo. The control-flow-graph branch (M4)
and the trimodal fusion stage (M5) are designed, documented and preserved in
[`../paused/`](../paused/), but are not being built. No resumption trigger has been set; this is
a pause, not a cancellation.

## Considered Options

Building the full trimodal ladder was the original plan and remains the more ambitious result.
It was not rejected on merit — it was descoped because the graph branch carries the project's
highest schedule variance by a wide margin (two disassembly paths that must be made comparable
by construction, a failure rate that is unknown until measured, and an irreversible
`node_feature_dim` freeze that gates every graph cache downstream) and it is the one branch
whose absence still leaves a coherent thesis.

Keeping V3 as a stretch goal with the plan intact was rejected as worse than either committing
or pausing: a stretch goal that is never explicitly cut gets planned around, half-built, and
defended half-heartedly. Marking the graph material as "not done" inside the active documents
was rejected for the same reason — it would leave every reader, including the examiner, reading
the delivered system as a trimodal design with a hole in it.

## Consequences

**The delivered system is a complete multimodal classifier, and every active document is written
that way.** Two independent views of a sample — spatial byte structure and its frequency-domain
counterpart — fused into a joint representation is multimodality in full. Active documents carry
no apologetic framing, no "limitations" line about the missing branch, and no defensive
comparison against the trimodal design. The graph work lives in `../paused/` so that it does not
have to be explained away here.

Three things get *better*, not merely smaller:

- FR7 now runs on **both** tracks. It was pinned to Malimg byte-recovered files only because the
  graph branch needed genuine re-disassembly; with no graph branch, padded BIG2015 `.bytes` work
  too, and the robustness result gains a replication it could not previously have (ADR-0015).
- Three seeds becomes mandatory rather than a descope candidate, because the ladder is four
  stages instead of six (ADR-0013).
- Every stage of the ladder is now trainable inside a single free-tier session, so the plan has
  no step that depends on a long uninterrupted run.

Two things get harder. The Malimg byte-recovery gate is now the project's sole source of
parseable PE headers, since the instrument set is deferred with the graph branch (ADR-0002,
ADR-0018). And BIG2015 is extracted as `.bytes` only, so resuming V3 means a full re-extraction
of that track (ADR-0003).
