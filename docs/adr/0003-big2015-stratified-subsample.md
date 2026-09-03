---
status: accepted
---

# BIG2015 is used as a stratified per-family subsample of `.bytes` only

BIG2015 extracts to roughly 200GB for the labelled training set alone, against about 20GB of
free-tier working disk, so the full corpus cannot be materialised on the available compute. We
extract a fixed, seeded, family-stratified subsample from `train.7z` — the `.bytes` files only,
not the accompanying `.asm` listings — and treat that as the track's corpus for every stage.

## Considered Options

Streaming extract-preprocess-discard over all 10,868 samples was rejected as a longer-running,
more failure-prone job for a corpus this project does not need in full. Third-party
pre-extracted re-uploads were rejected on unverifiable provenance, which is a poor thing to
defend in a viva.

Extracting the `.asm` listings alongside the `.bytes` would keep the shipped disassembly that
makes the graph branch cheap on this track (paused ADR-0009), at roughly an order of magnitude
more extracted bytes and a correspondingly longer job. With the graph branch out of scope
(ADR-0017) nothing in the delivered project reads an `.asm` file, so paying that cost now would
be buying an option against a resumption that has no trigger set. If V3 resumes, this track is
re-extracted from `train.7z` in full — a known, bounded, accepted cost, recorded here so the
re-extraction is not read later as an oversight.

## Consequences

The sampling protocol — per-family count, seed and selection rule — is itself a reportable
artifact, and is frozen in a file before extraction runs, since every number on this track is
conditional on it. Smaller per-family support widens confidence intervals, which raises rather
than lowers the importance of the seed discipline in ADR-0013.

`.bytes` files carry a scrubbed PE header, so this track can be padded for FR7 but can never
supply PE-section attribution. That role belongs to the Malimg track alone (ADR-0002).
