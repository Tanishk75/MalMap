---
status: accepted
---

# There is no serving layer; the demo is a curated notebook built around the entropy comparison

A live inference service is an explicit non-goal, and a viva needs a demonstration rather than a
deployment. The demo is a notebook centred on one comparison: a packed sample that M0 gets wrong
and M1 gets right, shown side by side — both predictions, both confidences, both Grad-CAM
overlays, and the PE-section attribution that says which file region the entropy channel keyed
on.

## Considered Options

A broader panel — an easy case, a hard case, an honest failure, a live padding demonstration —
was considered and cut to this single comparison. A panel spreads attention across samples that
each make a weaker point; the entropy comparison is the project's founding claim made visible in
one screen, and it is the thing an examiner can be walked through in under a minute. No sample
count is prescribed: one comparison, however many samples it takes to show it cleanly.

## Consequences

No API, no upload path, no model server, and no UI dependency that can fail live. The chosen
samples and their cached artifacts are committed to the repository so the demo runs with no
re-preprocessing and no network access, which also means the demo cannot show behaviour on an
arbitrary sample supplied by an examiner — that limit is worth stating up front rather than
discovering in the room.

Because the demo shows one thing well rather than several things partially, the questions it
invites are narrow and predictable. Prepare for them directly: why this sample, whether the
effect holds beyond it, and what the aggregate delta in the results table says.
