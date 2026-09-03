---
status: accepted
---

# FR7 asks whether fusion inherits robustness, not whether any one branch is invariant

"Which branch degrades least under appended junk bytes?" is a property of each branch's
construction and is largely predictable before running anything. The reportable question is
whether the fused model tracks its more robust branch or its more fragile one as padding
strength rises — a genuinely open property of a frozen-branch fusion layer (ADR-0011), since
nothing in its training told it which branch to trust when one of them is being corrupted.
FR7 is therefore a degradation curve over padding strength for M0, M1, M2 and M3 on the same
perturbed samples.

The experiment has a second axis, and it is the sharper one. Junk is appended in two
compositions — zero bytes and uniformly random bytes — because the entropy channel exists
precisely to flag high-randomness regions, so random padding manufactures exactly the feature
M1 was built to detect. If M1 degrades *worse* than the plain-grayscale M0 under random padding,
the entropy channel is an attack surface as well as a signal, and that is a genuine finding
rather than a confirmation.

## The figure

Two panels, one per junk composition. x-axis padding strength as a fraction of original file
size (0 / 5 / 10 / 20%, exact strengths fixed at Milestone 6), y-axis macro-F1, four lines
M0 / M1 / M2 / M3, shaded bands for the standard deviation across the three seeds of ADR-0013.
Run on both tracks, giving four panels in total and an independent replication of whatever the
inheritance pattern turns out to be.

## Considered Options

Adding perturbations that genuinely alter control flow — section injection, dead-code insertion
— would give a stronger result, but building PE rewrites that produce valid files is
substantial work with a high chance of silently corrupting samples. It is recorded as
out-of-scope rather than rejected on principle.

## Consequences

Perturbed samples must be re-preprocessed from scratch for every stage — a padded file has a
different length, so its image width band, its offset map and its spectrogram all change.
Serving any part of this from a clean cache invalidates the entire result.

Running on both tracks costs nothing extra in acquisition: Malimg supplies byte-recovered
binaries from its own held-out test split (ADR-0002) and BIG2015 supplies `.bytes` from its
(ADR-0003), and neither needs to be re-disassembled. The seed bands are cheap for the same
reason a curve is: perturbed preprocessing does not depend on model seed, so it is paid once and
the three trained models per stage simply forward-pass over it.

The graph branch, when it returns (`../paused/`), enters this figure as two additional lines on
axes that do not move. That is deliberate — the experiment was specified so a resumption widens
it rather than redesigns it.
