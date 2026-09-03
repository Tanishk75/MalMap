---
status: accepted
---

# If Malimg byte recovery fails, FR6's mechanism is validated on benign Windows binaries

FR6 — Grad-CAM attributions resolved to named PE sections — needs at least one corpus of files
that parse under `pefile`. With the instrument set deferred (ADR-0017), Malimg byte-recovered
files are the only such corpus in the project (ADR-0002), so a failure of that gate would
otherwise leave FR6 with no substrate at all. If it fails, the offset-map-to-PE-section mapping
is instead demonstrated on ordinary Windows system binaries, and the report states plainly that
attribution on malware samples was not possible.

## Considered Options

Acquiring the instrument set purely to protect FR6 was rejected: it reintroduces an
externally-gated dependency and the malware-handling question (paused ADR-0005) for a
contingency, not for the main path. Dropping FR6 outright on gate failure was rejected because
the mapping machinery — offset map, byte-range resolution, section lookup — is most of the work
and is worth showing to be correct even when it cannot be pointed at malware.

## Consequences

This fallback protects the **mechanism**, not the claim. A heatmap landing on `.text` in a
benign binary demonstrates that attribution resolves to file structure; it says nothing about
what the model learned from malware. The report must not blur those, and the distinction is
stated where the result appears rather than in a footnote.

Benign binaries are unlabelled with respect to family, so no accuracy number attaches to them
under any circumstance. They are measuring equipment, on exactly the terms the instrument set
was (paused ADR-0004).
