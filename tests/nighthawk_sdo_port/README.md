# Nighthawk SDO-port merged-response source contract

This directory contains a lightweight source-contract regression for the
current `MESI_Two_Level` SDO port. It checks the metadata and control-flow
invariants around merged speculative requests without compiling gem5 or
running a benchmark.

## Run

From any directory:

```sh
python3 /path/to/sdo/tests/nighthawk_sdo_port/test_merged_response_metadata.py
```

From the repository root:

```sh
python3 tests/nighthawk_sdo_port/test_merged_response_metadata.py
```

The test uses only the Python standard library and is compatible with Python
3.5. It intentionally uses no f-strings, variable annotations, or third-party
packages.

## Contract covered

The regression reads, but never modifies:

- `src/mem/ruby/system/Sequencer.cc`;
- `src/mem/packet.hh`;
- `src/cpu/o3/locPred.hh`;
- `src/cpu/o3/lsq_unit.hh`.

It checks five bounded contracts:

1. `Sequencer::insertSpecldRequest` returns
   `RequestStatus_Merged` only inside the branch that found the requested
   older entry and attached the new packet to its `dependentRequests`.
2. If `aliased_reqIdx` does not identify an outstanding older entry, control
   reaches fresh `SequencerRequest` allocation, table insertion, outstanding
   accounting, and `RequestStatus_Ready`.
3. `Packet::clearMLDOMHitStatus` clears all four mutually exclusive SDO hit
   flags: speculative-buffer, logical L0, logical L1, and memory.
4. A normal-LD response derives the actual L0/L1/memory level from callback
   metadata, marks every dependent packet final, clears stale hit metadata,
   overwrites `fromLevel`, sets only the actual hit flag, and does so before
   expose/validate/spec dispatch and `ruby_hit_callback`.
5. The Two-Level fold remains consistent in both directions:
   legacy logical `Cache_L3` maps to the shared `Cache_L2` target before
   packet issue, physical-L2 callback hits fold into logical shared-cache
   hits, and the internal Ruby lower-level code `2` is exposed as SDO memory
   level `3`.

## Why this is not a whole-file text match

The test masks C/C++ comments and string/character literals before analysis.
This prevents commented legacy returns, debug strings, and brace characters
inside messages from satisfying the contract. It then locates semantic
function signatures and uses balanced-brace extraction to inspect only the
relevant function or nested control-flow body. Assertions look for ordered
identifiers and operations rather than formatting or an entire exact source
string.

Failures name the missing or misplaced semantic marker. This should make a
real regression distinguishable from harmless whitespace or debug-message
changes.

## Scope limitation

Passing this test proves only that the checked source structure expresses the
contract. It does not compile C++, exercise Ruby timing, prove absence of a
race, or establish exactly-once completion at runtime. Follow it with a
Two-Level build and directed runs for:

- older-request found and not-found merge cases;
- normal responses originating at private L1, shared L2, and memory;
- stale dependent packets carrying each prior hit flag;
- squash plus late response and LQ-index reuse;
- duplicate response and terminal-callback accounting.
