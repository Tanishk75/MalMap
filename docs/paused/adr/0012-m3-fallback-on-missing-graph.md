---
status: accepted
---

# A sample with no CFG falls back to the M3 bimodal path at inference

Disassembly failure on packed samples is expected rather than exceptional, and refusing to
predict on those samples would make the system's coverage a function of the packer rather than
of the model. At inference, a sample whose `disasm_status` is `failed` is routed through M3
instead of M5, and the prediction records which path it took.

## Considered Options

Zero-imputing the graph embedding was rejected because a zero vector is a value the fusion
layer never saw in training, so its behaviour there is undefined rather than merely degraded.
Learned modality dropout was rejected as scope the project does not need in order to answer its
research question.

## Consequences

Any reported M5 metric must state what fraction of the evaluation set actually took the M5
path. A headline M5 macro-F1 computed over a set where a third of samples silently ran M3 is
not an M5 result, and presenting it as one would be the most damaging error available to this
project.
