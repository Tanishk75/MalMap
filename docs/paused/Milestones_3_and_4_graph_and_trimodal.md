# Paused milestones — Graph branch (M4) and Trimodal fusion (M5)

**Extracted verbatim from `../Development_Plan_Multimodal_Malware.md` v2.0 when the project was
scoped to V2 (ADR-0017). Gates, contingencies and descope levers are unchanged.**

Milestone numbering is preserved. The delivered plan keeps Milestones 5, 6 and 7 at their
original numbers, so these two slot back into place without renumbering anything.

Their governing ADRs live in [`./adr/`](./adr/): 0004 (instrument set), 0005 (malware handling),
0009 (`.asm` parsing), 0010 (nested fusion), 0012 (M3 fallback).

**Before resuming, note two things that changed underneath this plan.** BIG2015 now extracts
`.bytes` only, so Milestone 3's `.asm` parser has no input until a re-extraction runs. And the
instrument set was never acquired — Workstream A is paused with these milestones, so the
`radare2`-versus-`angr` bake-off has no substrate either.

---

## Workstream A — Instrument set *(parallel, started with Milestone 0)*

**Purpose.** Acquire the small curated collection of genuine PE binaries that FR6 and the
disassembler bake-off depend on (ADR-0004). It runs in parallel because its latency is external
— download queues, rate limits, possibly an access request — and blocking a milestone on someone
else's response time is avoidable.

**Work.** Choose a source and acquire a few hundred to roughly 2,000 labelled PE samples. Hash
every sample, record provenance and family label, and store the set archived and
password-protected inside the cloud environment only (ADR-0005). Produce
`protocols/instrument_set.md` recording source, date, label provenance and counts.

**Exit gate**

- [ ] Instrument set acquired, hashed, and labelled with recorded provenance.
- [ ] Storage conforms to ADR-0005, and ADR-0005 has been confirmed or overridden.
- [ ] At least one sample parses under `pefile` and disassembles under both candidate tools.

**Risk retired.** External-dependency latency, and confirmation that FR6 has a substrate at all.

**Descope lever.** Shrink the set. Two hundred samples still supports an attribution panel and a
failure-rate estimate; only the tightness of the estimate suffers.

*V2 note.* FR6 does not depend on this workstream any more. Attribution runs on Malimg
byte-recovered files, which retain their PE headers (ADR-0002), with ordinary Windows system
binaries as the mechanism fallback (ADR-0018).

---

## Milestone 3 — Graph branch: M4

**Purpose.** Build the branch that actually looks at what the code does, and characterise how
often that is impossible.

**Work.** Start with the BIG2015 `.asm` parser — the lower-risk of the two paths, since the
disassembly already exists (ADR-0009). Freeze the instruction-type bucket scheme and therefore
`node_feature_dim` before any graph is cached; this value can never change afterwards without
invalidating every cached graph and every tagged checkpoint downstream. Prototype `radare2`
against `angr` on the instrument set and pick one on measured speed and failure rate. Build the
Malimg-track graph path over byte-recovered files. Train the GNN with global pooling on the
samples that produced a usable CFG, logging and skipping the rest.

**Exit gate**

- [ ] `node_feature_dim` and its bucket scheme frozen and written into the Data Dictionary.
- [ ] M4 tagged on both tracks, or on one track with the other's absence explained in writing.
- [ ] Parse and disassembly failure rates reported per track as a percentage of attempted samples.
- [ ] Zero uncaught exceptions across a full preprocessing pass (PRD §3) — failures are logged
      outcomes, not crashes.
- [ ] A written statement on whether the `.asm`-derived and disassembler-derived node features
      are comparable, and what follows if they are not (ADR-0009).

**Risk retired.** The highest-variance step in the project.

**Descope levers, in order.** Coarsen from full CFG to call graph. Then run the graph branch on
BIG2015 only. Then reduce the node feature vector to instruction count and block size alone.

---

## Milestone 4 — Trimodal fusion: M5

**Purpose.** The centrepiece of the trimodal design. Does structure, added on top of appearance
and frequency, actually improve family classification?

**Work.** Freeze M3 and M4; train the second-stage fusion layer only (ADR-0010, ADR-0011).
Implement the inference-time fallback to M3 for samples with no CFG (ADR-0012). Assemble the
full per-track ladder table.

**Exit gate**

- [ ] M5 tagged on both tracks.
- [ ] Per-track ladder table: M0 through M5 macro-F1, with the M5-minus-best-predecessor delta.
- [ ] **The fraction of the evaluation set that actually took the M5 path is reported beside
      every M5 number** (ADR-0012). An M5 score computed over a set where a large share of
      samples silently ran M3 is not an M5 result.
- [ ] A written statement on whether the fusion delta replicates across both tracks.

**Risk retired.** The trimodal hypothesis, and the credibility of every earlier number once they
are placed in one table.

**Descope lever.** Skip optional end-to-end fine-tuning; keep frozen-branch fusion only.

---

## How these rejoin the delivered plan

Milestones 5, 6 and 7 were written to run on whatever branches exist, so resuming does not
rewrite them — it widens them:

- **Milestone 5 (probe)** adds the M5 trunk to the M0 / M1 / M3 trunks it probes (ADR-0014).
- **Milestone 6 (robustness)** adds M4 and M5 lines to a figure whose axes and panels are already
  fixed (ADR-0015). This is the cleanest rejoin: the experiment was deliberately specified so the
  graph branch slots in as two more lines rather than a redesign.
- **Milestone 7 (consolidation)** regains the disassembly-failure demo sample that ADR-0016
  originally prescribed and V2 dropped.
