---
status: accepted
---

# Real PE binaries are acquired only as a small curated instrument set

Exactly three requirements need an intact executable: FR6's `pefile` section mapping, FR7's
junk-byte padding, and genuine `radare2` / `angr` disassembly. None of them need scale — a few
hundred to roughly 2,000 labelled PE samples supports an attribution panel and a disassembler
bake-off comfortably. We therefore acquire a small curated instrument set for those purposes,
and never train on it or report accuracy against it.

## Considered Options

Full BODMAS access was rejected because it places a third-party approval on the critical path
for a capability the project needs only at small scale. Abandoning raw binaries entirely was
rejected because it collapses three requirements at once, including the project's headline
robustness result.

## Consequences

The instrument set's family taxonomy will not match either track's label space, so it can carry
no accuracy claim. FR7 in particular cannot use it: a degradation curve needs samples that are
simultaneously inside a trained label space and re-disassemblable from a real file, which means
Malimg byte-recovered binaries instead (ADR-0015). The instrument set's roles are PE-section
attribution, disassembler selection, and characterising the disassembly failure rate on real
packed samples.
