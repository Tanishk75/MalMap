---
status: accepted
---

# Kaggle is the primary environment for BIG2015; Colab is unconstrained

BIG2015 is a Kaggle competition dataset, so a Kaggle notebook can attach `train.7z` read-only
as a competition input without it consuming the working-disk quota. That is the only free-tier
path to producing the subsample in ADR-0003. Colab remains available for training, which
operates on derived caches small enough to move freely.

## Consequences

Session limits and the read-only input mount shape the Milestone 0 extraction job, which must
be resumable rather than a single long run. Derived caches have to be deliberately exported
from the Kaggle session — as a Kaggle Dataset, or to Drive — or they vanish when it ends, and
losing a cache costs a re-extraction rather than just a re-run.
