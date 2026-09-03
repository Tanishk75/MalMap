---
status: accepted
---

# Two parallel corpus tracks, not one merged label space

Malimg's 25 families and BIG2015's 9 families do not overlap, and the two sources have
distinguishable byte statistics — BIG2015 ships with its PE headers scrubbed for sterility,
Malimg does not — so a model trained on a merged 34-class label space could score well by
identifying the source dataset first and the family second, inflating every fusion delta the
project's thesis rests on. We therefore run the entire M0-to-M5 ladder independently on each
track, with separate label spaces, splits, caches, checkpoints and result tables.

## Considered Options

Merging into one 34-class problem, as the original Data Dictionary §7 specified, was rejected:
the confound is unfalsifiable after the fact, and is the first thing an examiner would probe.
Nominating one track as primary and the other as secondary was rejected because it throws away
a free replication.

## Consequences

Roughly double the training runs, and each track individually has less data than the merged
corpus would. In exchange, a fusion delta that replicates across two independent corpora is far
stronger evidence than one larger number from a confounded one, and the two tracks give each
other a genuine cross-dataset probe at no acquisition cost (ADR-0014). Supersedes the single
shared `family_to_id.json`: there is now one label map per track.
