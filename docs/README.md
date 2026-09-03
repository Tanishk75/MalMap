# Documentation index

Read in this order. Everything below the first two is downstream of them.

**Scope.** The delivered system is the image + audio bimodal classifier (ADR-0017). The graph
branch and trimodal fusion are designed, preserved and paused in [`paused/`](./paused/). Active
documents describe a complete multimodal system on its own terms; they do not describe a
trimodal design with a branch missing.

| Document | What it is |
|---|---|
| [`CONTEXT.md`](./CONTEXT.md) | The glossary. Vocabulary only; it wins over wording anywhere else. |
| [`adr/`](./adr/) | Architecture Decision Records — one decision per file, plus an index and the list of decisions deliberately still open. |
| [`Development_Plan_Multimodal_Malware.md`](./Development_Plan_Multimodal_Malware.md) | The milestone ladder: exit gates, kill gates, contingencies, descope order. No dates. |
| [`PRD_Multimodal_Malware_Classification.md`](./PRD_Multimodal_Malware_Classification.md) | Problem, goals, functional requirements, success metrics, datasets, risks. |
| [`System_Architecture_Multimodal_Malware.md`](./System_Architecture_Multimodal_Malware.md) | Five-layer architecture, per-stage model designs, diagrams. |
| [`Data_Dictionary_Multimodal_Malware.md`](./Data_Dictionary_Multimodal_Malware.md) | Every schema passed between modules. The contract that lets branches be built independently. |
| [`Module_Interface_Spec_Multimodal_Malware.md`](./Module_Interface_Spec_Multimodal_Malware.md) | Function and class signatures per module. |
| [`Evaluation_Metrics_Spec_Multimodal_Malware.md`](./Evaluation_Metrics_Spec_Multimodal_Malware.md) | How every number in the project is computed and compared. |
| [`Checkpoint_Development_Plan_Multimodal_Malware.md`](./Checkpoint_Development_Plan_Multimodal_Malware.md) | Per-checkpoint build sheet: datasets, libraries, papers, exit criteria. |
| [`paused/`](./paused/) | The graph branch and trimodal fusion: ADRs, milestone plans, and what a resumption has to redo first. |
| [`diagrams/`](./diagrams/) | Architecture SVGs, embedded from the architecture document. |

Superseded, retained for history:

- [`Development_Roadmap_Multimodal_Malware.md`](./Development_Roadmap_Multimodal_Malware.md) — the week-numbered v1.0 roadmap.
- [`malware_classification_v1_v2_v3.md`](./malware_classification_v1_v2_v3.md) — the original V1/V2/V3 framing. Its motivation sections are still the clearest statement of *why*.
- `System_Architecture_Multimodal_Malware (1).md` — a duplicate. Safe to delete.

## Precedence

When two documents disagree: `CONTEXT.md` for vocabulary, then `adr/`, then everything else.
Every reconciled document carries a banner naming what changed and which ADR governs it.

Sections marked **PAUSED (V3)** inside an active document are not part of the delivered system.
They are correct designs kept in place so a resumption does not have to re-derive them; they were
left in the specs rather than extracted because pulling M4 and M5 out of five interlocking
documents would have broken all five. Only the ADRs and the milestone plans were physically
moved, into [`paused/`](./paused/).

## Known gaps

- **`SRS v1.0` and `Tech Stack v1.0` are referenced but absent.** The PRD, the roadmap and the
  checkpoint plan all cite section numbers in an SRS (`SRS §3.1`, `§8`) and a Tech Stack document
  that do not exist in this folder. Either they live elsewhere and should be added here, or those
  citations are dangling and should be removed. Unresolved.
- **Paused ADR-0005 is `proposed`, never accepted** — the assumption that raw malware never
  touches the Windows workstation. Moot for the delivered system, which acquires no live malware,
  but it must be settled before any instrument-set work if V3 resumes.
- **ADR numbers have gaps** — 0004, 0005, 0009, 0010 and 0012 live in `paused/adr/` and kept
  their numbers. That is deliberate; see [`adr/README.md`](./adr/README.md).
