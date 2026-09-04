# Multimodal Malware Family Classification

The vocabulary of this project. A glossary and nothing else — no implementation
detail, no specs, no decisions. Decisions live in [`adr/`](./adr/); the plan lives in
[`Development_Plan_Multimodal_Malware.md`](./Development_Plan_Multimodal_Malware.md).

When a term here conflicts with wording in an older document, this file wins.

---

## Corpus

**Track**:
An independent end-to-end experimental line bound to one source dataset, carrying
its own label space, splits, caches, checkpoints and result tables. The design runs
two — the Malimg track and the BIG2015 track — but Malimg is paused for lack of an
original-resolution distribution (ADR-0019); the delivered system reports BIG2015 alone.
_Avoid_: dataset, corpus, arm, pipeline

**Sample**:
One malware specimen within a track, addressed by a `sample_id` that is unique
across every track.
_Avoid_: file, binary, instance, specimen, datapoint

**Family**:
The named malware lineage a sample belongs to. The thing being predicted.
_Avoid_: class, label, variant, type, category

**Label space**:
The ordered set of families a single track classifies into. Never shared between
tracks, and never merged.
_Avoid_: classes, taxonomy, num_classes, label set

**Benign binary**:
An ordinary non-malicious Windows executable, used only to show that attribution
resolves to named PE sections. Measuring equipment, never training or evaluation data.
_Avoid_: clean file, goodware, negative sample, holdout

**Byte recovery**:
Reconstruction of a sample's original leading bytes by row-major flattening of a
Malimg image, exact except for a sub-kilobyte truncated tail.
_Avoid_: decoding, inversion, un-imaging, reverse-rendering

**Packed**:
Describes a sample whose code is compressed or encrypted at rest, so its bytes carry
little exploitable structure until unpacked.
_Avoid_: obfuscated, encrypted, protected, armoured

---

## Views

**Branch**:
One of the parallel per-view pipelines — image and audio — each with its own
preprocessing, model and checkpoint. A branch is a pipeline, not a representation.
_Avoid_: stream, arm, tower, view, channel

**Modality**:
The kind of representation a branch operates on. Used only in the general sense
("multimodal", "missing modality"); a specific pipeline is always a Branch.
_Avoid_: mode, sense, domain

**Entropy channel**:
The sliding-window Shannon entropy of a sample's byte stream, carried alongside the
raw byte channel in the image branch.
_Avoid_: randomness map, entropy image, complexity channel

**Offset map**:
The recorded correspondence between an image tensor's coordinates and byte offsets
in the source file. Part of a cached image tensor, not an optional extra.
_Avoid_: index, lookup table, coordinate map

---

## Models

**Stage**:
A numbered, independently trained and tagged model in the M0–M3 ladder. Stages are
per-track: `m1-image-malimg` and `m1-image-big2015` are different stages.
_Avoid_: checkpoint, milestone, model, step, version

**Checkpoint**:
The persisted artifact of a stage — weights, optimizer state and metadata.
_Avoid_: save, snapshot, model file, weights

**Embedding**:
A branch's or fusion model's penultimate representation. Fixed-width, and frozen once
its stage is tagged.
_Avoid_: features, vector, latent, encoding

**Fusion**:
A trained layer consuming embeddings and emitting family logits. Distinct from an
ensemble, which would combine predictions rather than representations.
_Avoid_: ensemble, combination, merge, aggregation

**Baseline**:
Stage M0 — the plain single-channel grayscale image model that every later delta on
its track is measured against.
_Avoid_: control, reference model, naive model

---

## Evaluation

**Delta**:
The macro-F1 difference between a stage and its named comparator, on the same track
and the same test split. A delta across tracks or splits is not a delta.
_Avoid_: improvement, gain, lift, boost

**Probe**:
An evaluation measuring a frozen embedding's quality on data from outside its track,
without training the trunk.
_Avoid_: transfer test, zero-shot eval, generalization test

**Padding strength**:
The size of appended junk bytes as a fraction of a sample's original file size.
_Avoid_: attack strength, noise level, epsilon, perturbation size

**Junk composition**:
What the appended padding bytes are — all zeros, or uniformly random. The axis
orthogonal to padding strength, which says only how much.
_Avoid_: noise type, fill, garbage, payload

**Attribution**:
A per-region importance score over a sample, expressed in source-file byte offsets.
A heatmap is the rendering of an attribution, not the attribution itself.
_Avoid_: explanation, saliency, heatmap, importance

---

## Paused

These terms belong to the paused graph branch (ADR-0017). They are kept here so
[`paused/`](./paused/) has one vocabulary rather than its own.

**Instrument set**:
The small curated collection of genuine PE binaries held for experiments that need an
intact executable. Measuring equipment, never training or evaluation data.
_Avoid_: holdout, extra dataset, real data, binary corpus

**CFG**:
A sample's basic blocks as nodes and its jumps and calls as edges. A call graph is a
coarser and distinct structure, named separately when used.
_Avoid_: flow graph, control graph, program graph

**Basic block**:
A maximal straight-line instruction sequence with one entry and one exit. The default
CFG node.
_Avoid_: block, node, segment

**Disassembly failure**:
A sample for which no usable CFG could be produced. A recorded outcome with a rate
that gets reported, not an error condition.
_Avoid_: crash, exception, bad sample, corrupt sample
