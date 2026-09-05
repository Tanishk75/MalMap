---
status: accepted
---

# MOTIF replaces Malimg as the project's second track

ADR-0019 promoted BIG2015 to sole full track after no original-resolution Malimg distribution
could be located. That state was reconsidered rather than kept: too much of the project's design
depends on having two independent tracks to probe against each other (ADR-0001, ADR-0014) to
settle for one without first checking whether a substitute exists. [MOTIF](https://github.com/boozallen/MOTIF)
(Joyce et al., AAAI-22 AICS workshop) does: 3,095 disarmed real PE malware samples across 454
families, with ground-truth family labels drawn from vetted threat-intelligence reports, publicly
cloneable with no request gate. It is adopted as Malimg's replacement in the two-track design.
This does not reverse ADR-0019 — Malimg is still unavailable for the reason recorded there — it
answers the question ADR-0019 left open, of what fills the second-track role instead.

## Considered Options

**BODMAS** (57,293 samples, 581 families, also disarmed) was the other candidate raised. It was
not chosen for *now*: its raw binaries require emailing the maintainers to request access, with
no known turnaround — the same kind of open-ended wait that just cost the project a Malimg
acquisition cycle. MOTIF's zero-friction access made it available to verify and adopt in one
session; BODMAS remains a reasonable target if MOTIF's family sizes prove too small in practice,
or as the dataset FR5's "should we acquire a third view" question (already in the plan, Milestone
5) considers.

**Using all 454 MOTIF families** was rejected: the median family has only a handful of samples,
far short of what a stratified 70/15/15 split needs (at least 3/family, and realistically more to
be a meaningful class). **Keeping each of the top families at its natural count** (142 down to a
handful) was also rejected in favor of an even cut — see below — so the adopted track is balanced
by construction rather than replicating BIG2015's own long tail (Simda at 42 versus everyone
else's 100).

## Decision

The top 30 families by sample count are kept, each capped to 21 samples — the count of the
30th-ranked family — for an even 630-sample set. Frozen in
[`protocols/motif_sampling.md`](../../protocols/motif_sampling.md) per the same discipline as
`protocols/big2015_sampling.md`: published counts read from the dataset's own metadata (not
memory), a deterministic tie-break (`(-count, family_name)`), and a single seeded
`RandomState` stream for sub-selecting families above the cap (`MOTIF_SAMPLE_SEED = 2022`,
`src/config.py`).

## Consequences

**Three of ADR-0019's four consequences are reversed, not just softened:**

- **FR7's replication is restored**, not halved — the robustness sweep runs on both BIG2015 and
  MOTIF again (ADR-0015).
- **FR5 has a second track to probe against again** — Milestone 5 is unblocked without needing
  BODMAS; BODMAS returns to being a genuinely optional third view, as ADR-0014 originally framed
  it.
- **ADR-0001's cross-track generalization argument has two tracks to demonstrate across again.**

**FR6 gets a real chance to improve, but conditionally.** MOTIF's disarming only zeroes
`OPTIONAL_HEADER.Subsystem` and `FILE_HEADER.Machine` — unlike BIG2015's more thoroughly scrubbed
`.bytes` format, the rest of the PE structure, including the section table, is the original
malware's. This means `pefile` may well parse MOTIF samples and let FR6 demonstrate attribution
on real malware, not just benign binaries (ADR-0018). This is **not assumed** — Milestone 0's
exit gate adds an explicit check that at least one extracted MOTIF sample parses under `pefile`,
following the same "verify empirically, never trust a dataset's description" discipline ADR-0002
established for Malimg. If the parse rate turns out too low to trust, FR6 falls back to
ADR-0018's benign-binary mechanism check exactly as ADR-0019 anticipated.

**New consequence ADR-0019 didn't have to consider: MOTIF's files are still malware, even
disarmed.** They cannot execute (ADR-0018's disarming trick), but they carry known-malware MD5
hashes and sit as real files under `data/raw/motif/`. Real-time antivirus scanning may quarantine
or delete them after extraction — noted in `protocols/motif_sampling.md` so this isn't mistaken
for an extraction bug later. This is a smaller version of the concern paused ADR-0005 raised for
the (deferred) instrument set, not the same thing: MOTIF's files cannot run, where the instrument
set's would have needed to.

This was not hypothetical: a first local extraction attempt lost files in real time to a managed
corporate antivirus (Trend Micro Apex One, confirmed active in place of Windows Defender via
`Get-CimInstance`), which offered no local exclusion the way Defender's `Add-MpPreference` does.
The adopted fix extracts on Kaggle instead — where there is no local AV to react to — and
re-packages the result as a password-protected 7z (`notebooks/motif_subsample.ipynb`) before it
ever reaches an AV-managed machine, rather than relying on an exclusion that may not be grantable
at all on a given machine. See `protocols/motif_sampling.md`'s Extraction section for the full
account.

Code impact: `Track` gains a third literal value (`"motif"`), alongside `"malimg"` (still valid,
still unused) and `"big2015"`. `src/data/registry.py` gains `_build_motif_registry`, following
the same per-track-registry pattern as `_build_big2015_registry` (ADR-0001) — no change to
`image_prep`, `audio_prep`, `FusionModel`, or the evaluation layer, since all of them were already
track-parametrized rather than hardcoded to two named tracks.
