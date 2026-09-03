---
status: accepted
---

# The graph branch parses BIG2015's shipped `.asm`; disassemblers run only where a real file exists

BIG2015 ships IDA Pro disassembly listings and no runnable executables, so `radare2` and `angr`
have nothing to operate on for that track's samples. Parsing the shipped `.asm` into basic
blocks and control-flow edges is both the only available route and a substantially cheaper one.
Live disassembly is therefore confined to the instrument set and to Malimg byte-recovered
files, where an actual PE exists.

## Consequences

The PRD's open question of `radare2` versus `angr` narrows to a decision about the instrument
set and the Malimg track; it does not apply to the BIG2015 track at all. Two CFG construction
paths now exist, and their node features must be made comparable by construction — an IDA
listing and a `radare2` analysis will not agree on basic-block boundaries or instruction
categories by default. Reconciling them is the graph branch's principal correctness risk, and
if they cannot be reconciled the per-track M4 numbers are not comparable to each other and must
be reported as such.
