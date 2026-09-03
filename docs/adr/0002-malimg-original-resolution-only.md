---
status: accepted
---

# Only the original variable-resolution Malimg distribution is usable

Nataraj's construction reshapes a file's byte vector to a width chosen by file-size band and
discards only the `len mod width` remainder, so flattening an original-resolution Malimg image
row-major recovers the source file's leading bytes exactly, losing under a kilobyte of tail.
That recovery is what makes the entropy channel, the audio branch and `pefile` parsing possible
from a dataset that ships no binaries at all. The widely circulated resized copies — notably the
64x64 `malimg.npz` — destroy that byte stream irreversibly, so only a distribution whose images
retain their original dimensions is acceptable.

## Consequences

Byte-recoverability is a hard gate in Milestone 0, verified empirically per file-size band
rather than assumed from a filename or a dataset title.

With the instrument set deferred (ADR-0017), recovered Malimg files are the project's **only**
source of parseable PE headers and its only source of perturbable real binaries inside a trained
label space. This gate therefore got harder, not easier, when the project shrank: FR6 and the
Malimg half of FR7 both stand on it, where previously the instrument set backed one of them up.

If recovery fails, the Malimg track loses its audio branch and its attribution role at once, the
project falls back to BIG2015 as its sole full track, and FR7 continues on padded BIG2015
`.bytes` alone with its replication halved rather than withdrawn (ADR-0015). FR6's mechanism is
protected separately by the benign-PE fallback in ADR-0018 — that fallback validates that
heatmaps map to PE sections at all, but it cannot make the claim about malware, so this remains
the single highest-consequence gate in the project.
