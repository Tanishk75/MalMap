---
status: accepted
---

# Fusion stages train with their branches frozen

Free-tier GPU sessions are short and interruptible, and end-to-end training of a multimodal
model across two preprocessing pipelines does not fit reliably inside one. The bimodal fusion
stage therefore trains only its new layers, with the image and audio branches frozen, making it
a small resumable job whose result is attributable to the fusion layer alone.

## Consequences

Fusion cannot adapt the branch representations to one another, which probably costs some
accuracy relative to end-to-end training. That biases the reported deltas downward, which is
the safe direction for a claim — a fusion win measured this way is a floor, not a ceiling, and
should be described that way. Optional low-learning-rate end-to-end fine-tuning remains a
stretch goal and sits first on the descope list.

The rule is written for M3 because M3 is the only fusion stage in scope (ADR-0017). It was
written to hold for any fusion stage, and applies unchanged to the paused second stage.
