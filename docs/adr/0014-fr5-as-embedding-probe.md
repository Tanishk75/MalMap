---
status: accepted
---

# FR5 generalization is measured as an embedding probe, not zero-shot classification

FR5 as originally written — evaluate a frozen checkpoint on an unseen dataset with no
retraining — presumes a shared label space that does not exist here. Malimg's and BIG2015's
families are disjoint, and BODMAS family names come from a different labelling process
entirely, so a softmax head trained on one taxonomy has nothing meaningful to emit on another.
Generalization is therefore measured by freezing the trunk and evaluating the representation on
out-of-track data by k-nearest-neighbour retrieval and a linear probe.

The probed trunks are M0, M1 and M3 — the plain-grayscale baseline, the entropy-aware image
branch, and the bimodal fusion. Three trunks rather than two makes the probe a small ladder in
its own right: it can say not just whether fusion transfers better than the image branch, but
whether the entropy channel alone already accounts for the difference.

## Considered Options

Restricting evaluation to overlapping families was rejected because the overlap may be
near-empty, leaving nothing to report and no way to know that until late. Few-shot head
retraining is retained as a secondary result but not the primary measure, since retraining a
head is no longer the thing FR5 set out to test.

## Consequences

This tests directly whether the fused representation encodes malware structure or track-specific
artifacts, which is both the more interesting question and the sharpest available answer to the
confound that ADR-0001 was written to avoid. The two tracks probe each other at zero acquisition
cost, making BODMAS optional rather than required. The resulting number is not comparable to
accuracy figures reported elsewhere in the literature, and the report must say so.
