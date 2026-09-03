---
status: accepted
---

# Fusion is nested (M3 + M4 into M5), not a flat three-way concatenation

A flat concatenation of all three branch embeddings is the obvious design, so its absence needs
explaining. Fusing image and audio first and then fusing that representation with the graph
embedding mirrors the build order, and lets the graph branch's marginal contribution be read
directly off the M5-minus-M3 delta rather than inferred from a separate ablation sweep. It also
means the bimodal model stays a complete, submittable artifact if the graph branch never lands.

## Consequences

M5's input width is the M3 fused dimension plus the graph embedding dimension, not the sum of
three branch dimensions, and `FusionModel` must expose `embed()` so that a fusion model can
itself be nested as a branch. The design cannot answer "what does audio contribute given the
graph branch?" without an additional run that is not currently planned.
