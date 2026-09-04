---
status: accepted
---

# Malimg is paused; BIG2015 is the project's sole delivered track

The project could not obtain an original-resolution Malimg distribution (ADR-0002) within the
time available — not because recovery was attempted and failed on a resized copy, but because no
original-resolution source was locatable within the effort budget available for it. The Milestone
0 plan already named this exact outcome and its contingency: demote Malimg, promote BIG2015 to
sole full track, and record the outcome as a new ADR rather than absorbing it silently. This is
that record. It is a pause, not a rejection — if an original-resolution distribution surfaces
later, Malimg slots back in without redesign, the same way the graph branch is preserved in
[`paused/`](../paused/) (ADR-0017).

## Considered Options

Continuing to search for a Malimg source before starting Milestone 1 was rejected: the dataset is
gated behind a request process at its origin (UCSB Vision Research Lab) with no guaranteed
turnaround, and every popular public mirror checked so far turned out to be pre-resized to a
fixed size — exactly what the byte-recovery gate exists to reject rather than silently accept.
Blocking Milestone 1 on an acquisition with no known timeline was judged worse than proceeding on
the track already in hand and resuming Malimg later if a source appears.

## Consequences

BIG2015 becomes the project's sole full track. `image_prep`, `audio_prep`, `FusionModel` and the
evaluation layer are all track-parametrized already (ADR-0001) and need no code change — they
simply run once instead of twice. What changes is scope:

- **FR6 loses its malware-specific attribution claim.** BIG2015's `.bytes` files ship with their
  PE header scrubbed by Microsoft and cannot be parsed by `pefile`; recovered Malimg files were
  the project's only source of parseable PE headers (ADR-0002). FR6 falls back to ADR-0018's
  benign-Windows-binary mechanism check: it can still show that a Grad-CAM heatmap resolves to a
  named PE section, but not that this holds *for malware*, and the report must say so plainly.
- **FR7's replication is halved, not withdrawn** (ADR-0015 already anticipated this): the
  robustness sweep runs on padded BIG2015 `.bytes` only.
- **FR5 has nothing to probe.** ADR-0014's cross-track embedding probe relies on two tracks
  probing each other at zero acquisition cost; with one track there is no "other track" to
  evaluate a frozen trunk against. Milestone 5 cannot proceed as designed unless BODMAS — until
  now optional per ADR-0014 — is acquired to stand in as the second track, or FR5 is descoped
  alongside Malimg. **This is deliberately left open**, tracked in `adr/README.md`'s open-question
  table, and must be settled before Milestone 5 starts, not during it.
- **ADR-0001's cross-track generalization argument has only one track to demonstrate across.**
  The project's headline result is a single-track finding until and unless a second track
  (Malimg's return, or BODMAS) is added.
- Every "per track" instruction already written into the Development Plan, Data Dictionary and
  Module Interface Spec continues to describe the schema correctly — `registry_malimg.csv`,
  `family_to_id_malimg.json` and `protocols/malimg_recovery.md` are simply never produced by the
  delivered system, the same way the paused graph branch's schemas were kept rather than deleted.

Nothing in `src/` changes as a result of this ADR. `Track = Literal["malimg", "big2015"]` and the
Malimg code paths (`_build_malimg_registry`, `recover_bytes`, the image-extension branch of
`load_raw_bytes`) stay in place, tested against synthetic data, ready to run the moment a real
distribution is obtained.
