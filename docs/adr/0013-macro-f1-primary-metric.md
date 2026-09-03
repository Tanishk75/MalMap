---
status: accepted
---

# Macro-F1 on a fixed test split is the single primary comparison metric, over three seeds

Family sizes are heavily imbalanced on both tracks, Malimg's 25 families especially, so accuracy
rewards a model that learns the largest families and ignores the rest. Every claim of the form
"stage X beats stage Y" means macro-F1 on the identical held-out split with the identical label
map, reported as mean and standard deviation over three seeds; accuracy and weighted-F1 are
reported alongside for context only.

## Consequences

No claim may be restated in terms of a different metric because macro-F1 did not favour it, and
no delta is reported from a single run. Three seeds is a requirement, not a target: with the
graph branch out of scope (ADR-0017) the ladder is four stages rather than six, so the full
three-seed sweep is roughly twenty-four training runs — affordable on the available compute in a
way it was not before.

Seed repetition is therefore **off the descope list entirely**. It was on it as item four when
the ladder was longer. Cutting it now would be trading the one thing that makes a small delta
believable for compute the project has.
