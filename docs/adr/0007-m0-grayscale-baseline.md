---
status: accepted
---

# A plain-grayscale M0 baseline is the first checkpoint on every track

The project's founding claim is that an entropy-aware multi-channel image beats a plain
grayscale byte-image, but the original six-checkpoint ladder began at M1 and never produced the
grayscale number, leaving that claim unsupported by the project's own experiments. We add M0 —
single channel, same backbone, same splits, same seed — as the first tagged stage on each
track, and report every later delta against it.

## Considered Options

Reporting the comparison as an ablation inside M1 was rejected because it buries the reference
number instead of making it a first-class, tagged, reproducible artifact. Citing published
grayscale figures from the Nataraj-era literature was rejected because those come from
different splits and preprocessing, so the comparison would not be a delta in the sense
`CONTEXT.md` defines.

## Consequences

Two extra training runs and two extra tags. In exchange the entropy channel's contribution
becomes a measured quantity rather than an assertion, and M0 doubles as the cheapest possible
end-to-end smoke test of the data layer: if M0 will not train, nothing downstream is worth
attempting.
