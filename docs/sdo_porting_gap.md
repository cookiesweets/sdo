# SDO-to-Nighthawk Two-Level porting-gap audit

## Scope and conclusion

This document is a source audit, not a claim that either simulator currently
builds or passes a workload. It compares:

- SDO candidate port: `sdo` commit `40b4039be4ad` (`master`,
  `origin/master`);
- SDO reference: `upstream/master` commit `5d058fd4` and
  `origin/original` commit `45128d5e`;
- Nighthawk/STT target: `sparespec-stt` commit `8ff168d301`
  (`HPCA2027`).

Evidence is written as `REF:path:line-range`. Line numbers for SDO source are
from `git show REF:path`; therefore this audit does not depend on, or describe,
the dirty working-tree copies of `src/mem/packet.hh` and
`src/mem/ruby/system/Sequencer.cc`.

The primary conclusion is:

> `sdo/master` contains a substantial but only partially validated Two-Level
> port, begun in 2025 and accompanied by a `README_MICRO26` that calls it a
> Two-Level SDO configuration. Source inspection alone does not establish
> semantic equivalence to the upstream Three-Level SDO implementation or an
> apples-to-apples comparison with Nighthawk.

The upstream reference has a private L0, a private L1, and a shared L2. Its
location predictor and messages distinguish L0/L1/L2/memory. The candidate
Two-Level port has a private L1 and shared L2 and folds the old logical L2
prediction into the shared-L2 path. Nighthawk also uses
`X86_MESI_Two_Level`, but implements a different substrate: generation-owned
S-MSHRs and quarantined L1 entries, not SDO's predicted-depth, data-oblivious
cache traversal. Consequently:

1. an original `X86_MESI_Three_Level` SDO result is a separately labelled
   reproduction point, not the primary Nighthawk baseline;
2. `sdo/master` is a useful candidate port, not yet an exact port;
3. the fair target is SDO semantics on the same Two-Level topology, CPU/cache
   parameters, STT policy, checkpoints, and instruction budget used for
   Nighthawk;
4. full experiments must wait for the directed validation gates at the end of
   this document.

The row-by-row protocol mapping is in
[`sdo_three_to_two_mapping.csv`](sdo_three_to_two_mapping.csv).

## Repository and reference integrity

SDO identifies its base as early gem5 commit `38a1e23`, O3 CPU, and Ruby
(`40b4039:README:17-25`). Its published build instruction is
`X86_MESI_Three_Level` (`40b4039:README:29-35`). By contrast, the newer
experiment note explicitly calls the repository configuration Two-Level SDO
and selects `build/X86_MESI_Two_Level/gem5.opt`
(`40b4039:exp_script/README_MICRO26.md:1-7,47-52`).

The current SDO history contains a long sequence of 2025-11-12 commits touching
`MESI_Two_Level-L1cache.sm`, `MESI_Two_Level-L2cache.sm`,
`MESI_Two_Level-msg.sm`, `RubySlicc_Types.sm`, `packet.hh`, and
`Sequencer.cc`, followed by MICRO26 configuration work in 2026. This is direct
provenance for an attempted port, but the repository contains no checked-in
build manifest, directed-test result, binary hash, or equivalence report for
commit `40b4039`.

There is a subtle reference hazard. `MESI_Three_Level.slicc` includes the
Three-Level L0 and L1 controllers, but also includes the shared
`MESI_Two_Level-msg.sm`, `MESI_Two_Level-L2cache.sm`, directory, and DMA files
(`upstream/master:src/mem/protocol/MESI_Three_Level.slicc:1-9`). Those shared
files changed on `sdo/master`. Thus building `MESI_Three_Level` at current
`master` is not necessarily an upstream reproduction even though the
Three-Level-specific L0/L1 files themselves are unchanged. Use an isolated
checkout of `upstream/master` (or verify the exact `origin/original` blobs) for
the reference point.

`origin/original` has five side commits relative to the common upstream base.
For the protocol files examined here, it generally matches the upstream
Three-Level implementation; this does not make it the semantic source for the
new Two-Level port. Record the exact selected ref and every included SLICC blob
hash in a run manifest.

The relationship was checked with `git rev-list --left-right --count`:
`origin/original...40b4039` is `5 77`, while
`upstream/master...40b4039` is `0 77`; both merge bases are
`5d058fd4389c2e16818835fe023fc946d2150642`. The key-blob audit below makes
the comparison explicit (hashes are Git blob IDs):

| Path | `40b4039` | `origin/original` | `upstream/master` | Interpretation |
|---|---|---|---|---|
| `MESI_Three_Level-L0cache.sm` | `23c6a0d2` | `23c6a0d2` | `23c6a0d2` | Three-Level-specific L0 unchanged |
| `MESI_Three_Level-L1cache.sm` | `9625a35f` | `9625a35f` | `9625a35f` | Three-Level-specific L1 unchanged |
| `MESI_Three_Level-msg.sm` | `ac039353` | `ac039353` | `ac039353` | Private-hop message unchanged |
| `MESI_Two_Level-L1cache.sm` | `e4898a24` | `22621e5d` | `22621e5d` | candidate port changed CPU-facing L1 |
| `MESI_Two_Level-L2cache.sm` | `61416119` | `47b570a0` | `47b570a0` | candidate port changed shared L2 |
| `MESI_Two_Level-msg.sm` | `dda321a2` | `40c9f7e7` | `40c9f7e7` | candidate port changed network messages |
| `RubySlicc_Types.sm` | `9fe2cefd` | `20997529` | `20997529` | candidate port changed SLICC callbacks |
| `packet.hh` | `f4b35916` | `dd666422` | `dd666422` | candidate port changed packet metadata/API |
| `Sequencer.cc` | `1d6f01aa` | `e0937fbe` | `e0937fbe` | candidate port changed request association/callbacks |

Paths in this table are under `src/mem/protocol/` except `packet.hh`
(`src/mem/packet.hh`) and `Sequencer.cc`
(`src/mem/ruby/system/Sequencer.cc`). `origin/original` and
`upstream/master` are byte-identical for every listed blob. This supports
using upstream line-number evidence for this scoped reference audit, while the
five `origin/original` side commits still require independent review before
calling the entire trees identical.

## 1. gem5 and configuration API gap

### Common simulator family

Both trees are from the same legacy gem5 family and use the old Python
configuration style. This is not a modern-gem5 API migration. The important API
gaps are mechanism-local:

- packet metadata and request commands;
- O3/LSQ scheme selection and visibility callbacks;
- Ruby Sequencer outstanding-request bookkeeping;
- SLICC message fields, controller states, and callbacks;
- cache-entry metadata and replacement/admission hooks.

SDO exposes `scheme`, `mem_model`, `STT`, `impChannel`, location-predictor, and
TLB-defense options (`40b4039:configs/common/Options.py:374-458`). It wires
those options into the O3 CPU in
`40b4039:configs/common/CpuConfig.py:105-145,176-218` and declares their
parameters in `40b4039:src/cpu/o3/O3CPU.py:165-200`.

Nighthawk instead exposes `threat_model`, `needsTSO`, `simulateScheme`, and
`nighthawkSMSHRSize`-class controls
(`8ff168d3:configs/common/Options.py:300-320`,
`8ff168d3:configs/common/CpuConfig.py:89-132`,
`8ff168d3:src/cpu/o3/O3CPU.py:165-180`). Its CPU setup enforces the coupling
between protection, STT, and the `OnlyTainted` scheme
(`8ff168d3:src/cpu/o3/cpu.cc:451-497`).

These option sets are not name-compatible. A comparison launcher must emit a
normalized manifest and then translate it into each binary's native options.
At minimum the normalized fields must include ISA, CPU, clock, memory model,
threat model, taint/implicit-channel scope, visibility rule, cache topology and
latencies, checkpoint, warmup, and measured instruction count.

## 2. CPU, LSQ, STT, and visibility semantics

### SDO reference/candidate behavior

The SDO CPU defines three materially different modes:

- `UnsafeBaseline`: unsafe execution, loads execute normally;
- `DelayExecute`: safe mode, unsafe load execution is delayed;
- `SDO`: safe mode, loads may execute and `isInvisibleSpec` is enabled.

The assignments are explicit in
`40b4039:src/cpu/o3/cpu.cc:423-446`. SDO then constructs and configures a
location predictor (`40b4039:src/cpu/o3/cpu.cc:548-596`).

The LSQ tracks SDO loads through `OblS` lifecycle states including
`toBeSquash` (`40b4039:src/cpu/o3/lsq_unit.hh:679-702`). Before
`readyToExpose`, it can issue a speculative read
(`40b4039:src/cpu/o3/lsq_unit.hh:949-989`) and translates a predicted level
into `createReadSpecL0`, `createReadSpecL1`, or `createReadSpecMem`;
the old L2 creator is commented out
(`40b4039:src/cpu/o3/lsq_unit.hh:1015-1078`). Sender state carries the LQ
index/instruction, and the packet carries the instruction sequence number
(`40b4039:src/cpu/o3/lsq_unit.hh:1082-1088`).

Normal SDO deliberately does not use the speculative buffer. The alternate
unsafe-contention path does, and the source itself marks that path incorrect
(`40b4039:src/cpu/o3/lsq_unit.hh:1094-1121`). It must not be enabled for the
baseline unless separately repaired and labelled.

SDO's returned data is not simply made architecturally visible on first Ruby
response. The LSQ handles TLB miss and OblS miss with squash/reissue paths
(`40b4039:src/cpu/o3/lsq_unit_impl.hh:2196-2252`), distinguishes predicted
hit/validation behavior (`40b4039:src/cpu/o3/lsq_unit_impl.hh:2260-2285`),
and holds early-hit data until the visibility/expose path before writeback
(`40b4039:src/cpu/o3/lsq_unit_impl.hh:2295-2340`). It creates an expose or
validate packet where required
(`40b4039:src/cpu/o3/lsq_unit_impl.hh:2364-2385`). Validation compares the
speculative and ordinary data and requests re-execution on failure
(`40b4039:src/cpu/o3/lsq_unit_impl.hh:3123-3176`).

Squash removes the load-queue entry and predictor state
(`40b4039:src/cpu/o3/lsq_unit_impl.hh:2975-3027`); a response for a squashed
instruction is ignored by the later completion path
(`40b4039:src/cpu/o3/lsq_unit_impl.hh:3180-3255`). Commit refuses to retire an
MLDOM load before `readyToExpose`, and commits predictor state only after the
update protocol (`40b4039:src/cpu/o3/commit_impl.hh:1654-1656,1720-1734`).

The data-oblivious contract is more specific than “send a speculative load.”
A predicted-depth request continues to its selected target even if an upper
level already hit; each traversed level reports hit/miss metadata, the first
hit supplies the candidate value once, and the target-level callback is the
final confirmation. The upstream callbacks encode intermediate versus final
packets by requested target
(`upstream/master:src/mem/ruby/system/Sequencer.cc:1275-1493`) and copy data
only on the first hit
(`upstream/master:src/mem/ruby/system/Sequencer.cc:1495-1533`). This fixed
target-depth traversal is the local data-oblivious behavior that the candidate
Two-Level port must preserve after collapsing a cache level. Merely obtaining
the same value, or merely retaining `GETSPEC_*` enum names, is insufficient.

### Two-Level predictor collapse

In the candidate port, logical names no longer correspond one-to-one with the
upstream physical levels:

- `Cache_L1` means the old logical L0/private physical L1;
- `Cache_L2` means the old logical L1/shared physical L2;
- legacy `Cache_L3` is folded into `Cache_L2`.

This is recorded in
`40b4039:src/cpu/o3/locPred.hh:38-57,175-182` and reinforced in CPU setup
(`40b4039:src/cpu/o3/cpu.cc:568-576`). The random predictor still samples four
outcomes while two now lead to the shared L2
(`40b4039:src/cpu/o3/locPred.hh:115-128`). Therefore an unchanged random or
dynamic predictor can have a different level distribution after the fold.
Legacy L2 prediction/hit counters also remain in the CPU statistics
(`40b4039:src/cpu/o3/commit.hh:530-579`), so raw stat names cannot be compared
without a semantic remapping.

### Nighthawk behavior is not an SDO level-prediction path

Nighthawk's `OnlyTainted` mode enables the Nighthawk-specific path
(`8ff168d3:src/cpu/o3/lsq_unit_impl.hh:230-265`). The LSQ tracks STT
taint/visibility (`8ff168d3:src/cpu/o3/lsq_unit_impl.hh:1238-1268`), and a
visibility retry is marked resolved while preserving request history and
assigning a generation from the dynamic instruction sequence number
(`8ff168d3:src/cpu/o3/lsq_unit.hh:1119-1143`). Squash emits a
generation-tagged control request before removing the LQ entry
(`8ff168d3:src/cpu/o3/lsq_unit_impl.hh:1955-2004`).

The packet carries taint, resolved/squash, and request-generation metadata
(`8ff168d3:src/mem/packet.hh:386-400,814-833`). The Sequencer rejects a
tainted CPU callback before visibility
(`8ff168d3:src/mem/ruby/system/Sequencer.cc:502-552`) and performs
generation-aware cleanup only for the matching original request
(`8ff168d3:src/mem/ruby/system/Sequencer.cc:1441-1499`).

There is no sound one-line substitution from SDO's prediction depth to
Nighthawk's quarantine generation. The fair common policy boundary is the STT
visibility decision; the mechanisms on the unsafe side of that boundary must
remain distinct.

## 3. Ruby topology and cache-level assumptions

### Upstream Three-Level SDO

The Ruby configuration creates separate L0, L1, and L2 cache classes
(`upstream/master:configs/ruby/MESI_Three_Level.py:39-45`). Per core it creates
private L0I/L0D and a private L1, connects an extra speculative-data channel
between L1 and L0, and then creates shared/clustered L2 controllers
(`upstream/master:configs/ruby/MESI_Three_Level.py:85-180,196-229`).
The protocol composition is L0 controller, L1 controller, shared L2
controller, directory, and DMA
(`upstream/master:src/mem/protocol/MESI_Three_Level.slicc:1-9`).

The L0 accepts `SpecLoad_L0/L1/L2/Mem` and perfect variants
(`upstream/master:src/mem/protocol/MESI_Three_Level-L0cache.sm:100-142`).
It either returns a hit at the requested stopping level or forwards a
`CoherenceMsg` toward L1
(`upstream/master:src/mem/protocol/MESI_Three_Level-L0cache.sm:627-710,
851-903,1089-1194`).

The private L1 separately accepts `GETSPEC_L1`, `GETSPEC_L2`, and
`GETSPEC_Mem` (`upstream/master:src/mem/protocol/MESI_Three_Level-L1cache.sm:
270-290`). A logical-L2 request passes through L1 even on a hit, whereas a
logical-L1 request can stop there
(`upstream/master:src/mem/protocol/MESI_Three_Level-L1cache.sm:485-535,
1013-1100`). The shared L2 then distinguishes logical L2, memory, and perfect
paths and reports `hitAtL2`/`DataBlk_L2`
(`upstream/master:src/mem/protocol/MESI_Two_Level-L2cache.sm:646-803,
1228-1298`).

### Candidate Two-Level SDO

The active Two-Level composition has only the L1 controller, L2 controller,
directory, and DMA
(`40b4039:src/mem/protocol/MESI_Two_Level.slicc:1-7`). Its L1 states are the
ordinary MESI stable/transient states; there is no SDO quarantine state
(`40b4039:src/mem/protocol/MESI_Two_Level-L1cache.sm:80-104`).

The CPU-facing request translation is:

- predicted logical L0 -> `GETSPEC_L0`, stop at private physical L1;
- predicted logical L1 -> legacy command `GETSPEC_L2`, continue to shared
  physical L2;
- predicted memory/perfect -> forward accordingly;
- the old direct logical-L2 case is absent.

See `40b4039:src/mem/protocol/MESI_Two_Level-L1cache.sm:296-320,650-739,
1151-1201,1428-1484`. The shared L2 maps the legacy `GETSPEC_L2` command to
its speculative shared-L2 event, preserves origin/index on lower-level
forwarding, and reports shared-L2 or memory data
(`40b4039:src/mem/protocol/MESI_Two_Level-L2cache.sm:290-326,489-515,
646-803,1238-1308`).

The directory handles speculative memory/perfect requests and returns
`DATA_SPEC_FROM_MEM` with origin/index
(`40b4039:src/mem/protocol/MESI_Two_Level-dir.sm:205-221,356-375,406-475,
590-638`).

The command names retain compatibility residue. Current messages still declare
L0/L1/L2/Mem variants and four hit/data fields
(`40b4039:src/mem/protocol/MESI_Two_Level-msg.sm:31-50,73-95,113-133`),
and SLICC callback types still expose L0/L1/L2/Mem callbacks
(`40b4039:src/mem/protocol/RubySlicc_Types.sm:102-121`). The presence of these
names does not prove that four physical levels still exist.

### Nighthawk Two-Level cache semantics

Nighthawk adds component state absent from SDO:

- `IS_Tainted`, `IS_Tainted_Visible`, `S_Tainted`, `E_Tainted`, and
  squash/spare states
  (`8ff168d3:src/mem/protocol/MESI_Two_Level-L1cache.sm:75-118`);
- S-MSHR full, tainted-visible retry, owner mismatch, unsafe preemption,
  no-slot rejection, and generation-squash events
  (`8ff168d3:src/mem/protocol/MESI_Two_Level-L1cache.sm:120-183`);
- TBE fields for S-MSHR tracking, epoch, visibility, waiter, and owner
  generation
  (`8ff168d3:src/mem/protocol/MESI_Two_Level-L1cache.sm:195-209`).

Unsafe admission chooses an invalid entry or an eligible younger Stealth entry;
otherwise it rejects, rather than evicting ordinary visible data to manufacture
quarantine capacity
(`8ff168d3:src/mem/protocol/MESI_Two_Level-L1cache.sm:1353-1387`).
Response-first installs Stealth state while retaining ownership, and
visibility-first or promotion paths validate the live owner/generation
(`8ff168d3:src/mem/protocol/MESI_Two_Level-L1cache.sm:3435-3539`).

At the cache implementation level, Stealth and owner generation are explicit
entry metadata (`8ff168d3:src/mem/ruby/slicc_interface/AbstractCacheEntry.hh:
83-86`). Admission selects invalid first and permits older unsafe work to
preempt only eligible Stealth state
(`8ff168d3:src/mem/ruby/structures/CacheMemory.cc:747-831`). Safe replacement
can reclaim Stealth (`8ff168d3:src/mem/ruby/structures/CacheMemory.cc:
834-897`), a single authoritative copy is enforced
(`8ff168d3:src/mem/ruby/structures/CacheMemory.cc:1008-1025`), and the
quarantine-capable slot is restored after promotion/safe fill
(`8ff168d3:src/mem/ruby/structures/CacheMemory.cc:1035-1152`).

None of these has a direct Three-Level SDO counterpart. Adding them to SDO
would turn the baseline into a Nighthawk-derived hybrid.

## 4. Messages, virtual networks, TBE fields, and Sequencer hooks

### Messages and virtual networks

The Three-Level private L0/L1 hop uses `CoherenceClass` values for
`GETSPEC_L0/L1/L2/Mem/Perfect` and speculative data responses, carrying an LQ
index plus four hit flags/data blocks
(`upstream/master:src/mem/protocol/MESI_Three_Level-msg.sm:29-82`).
The L1/shared-L2 network uses the shared Two-Level request/response messages.
The L1 controller's request, response, and unblock channels use virtual
networks 0, 1, and 2 respectively
(`upstream/master:src/mem/protocol/MESI_Three_Level-L1cache.sm:50-64`).

The candidate Two-Level port removes the private L0/L1 channel but retains
request/response origin and index across the Ruby network. It does not add an
owner generation to these messages
(`40b4039:src/mem/protocol/MESI_Two_Level-msg.sm:73-95,113-133`).

Nighthawk uses `GETSPEC`, `GETSPEC_FAKE`, squash, and expose-style commands
rather than predicted-depth commands, and has a tainted response class
(`8ff168d3:src/mem/protocol/MESI_Two_Level-msg.sm:31-67`). Generation is
kept in Packet/TBE/cache-entry state rather than added to this network message.

### TBEs

The Three-Level L0 and L1 TBEs contain ordinary transient state/data fields,
not a live load generation
(`upstream/master:src/mem/protocol/MESI_Three_Level-L0cache.sm:169-177`,
`upstream/master:src/mem/protocol/MESI_Three_Level-L1cache.sm:165-179`).
The upstream shared-L2 path carries origin/index in messages but similarly
lacks a Nighthawk owner-generation lifecycle.

The current SDO Two-Level L1 TBE contains address, transient state, data,
dirty/prefetch, and pending acknowledgements
(`40b4039:src/mem/protocol/MESI_Two_Level-L1cache.sm:173-181`). Its L2 TBE
adds coherence requestors but no LQ owner generation
(`40b4039:src/mem/protocol/MESI_Two_Level-L2cache.sm:166-178`).

Nighthawk's TBE tracks S-MSHR epoch and owner generation and uses
epoch-sensitive deallocation
(`8ff168d3:src/mem/protocol/MESI_Two_Level-L1cache.sm:195-209,2049-2125`).
That is a deliberate Nighthawk property, not a missing field that can be copied
into an exact SDO reproduction without changing the mechanism.

### Sequencer

At SDO `40b4039`, speculative requests are tracked in
`m_specldRequestTable` using a line address and an LQ-derived index; accepted
commands are L0, logical-L1, memory, and perfect variants, while the old L2
case is commented
(`40b4039:src/mem/ruby/system/Sequencer.cc:376-420`). Same-line interaction
and collision/merge logic are in
`40b4039:src/mem/ruby/system/Sequencer.cc:422-480`.

The callbacks separately implement private-L1, shared-L2, and memory targets
(`40b4039:src/mem/ruby/system/Sequencer.cc:931-1150`). Multiple matching
packets can receive an oblivious-hit callback
(`40b4039:src/mem/ruby/system/Sequencer.cc:1283-1329`), and target-specific
early/final callbacks run at
`40b4039:src/mem/ruby/system/Sequencer.cc:1329-1502`. The first hit copies
data once, marks it carried, and sends an intermediate or final packet
(`40b4039:src/mem/ruby/system/Sequencer.cc:1514-1546`). Empty-state checking
includes the speculative table
(`40b4039:src/mem/ruby/system/Sequencer.cc:1550-1554`).

This bookkeeping has no explicit generation field, live-owner predicate, or
exactly-one terminal-action counter. That is a validation risk, not proof of a
bug. Directed tests must exercise LQ-index reuse, squash plus late response,
duplicate responses, merged same-line requests, and a response concurrent with
visibility.

## 5. Storage, forwarding, validation, and squash

SDO and Nighthawk must not be described as storing speculative data in the
same way:

- SDO transports hit-level metadata and candidate data through Ruby callbacks
  and packet state; the LSQ gates writeback and may validate/re-execute.
- Normal SDO explicitly avoids the speculative buffer
  (`40b4039:src/cpu/o3/lsq_unit.hh:1094-1121`).
- Nighthawk can install a returned line in an L1 entry marked Stealth, where it
  remains quarantined until a valid promotion or is reclaimed/deprecated.

For SDO, expose/validate requests are translated by the Sequencer
(`40b4039:src/mem/ruby/system/Sequencer.cc:1719-1740`) and the LSQ compares
validation data before allowing completion
(`40b4039:src/cpu/o3/lsq_unit_impl.hh:3123-3176`). For Nighthawk, promotion
requires the live matching owner/generation and a non-deprecated entry;
owner-loss paths terminate/drop rather than forwarding stale state
(`8ff168d3:src/mem/protocol/MESI_Two_Level-L1cache.sm:2384-2468,
2518-2529`).

The current SDO packet has sequence number, hit-level, final/carry/copy, and
confirmation fields but no Nighthawk request generation or live-owner token
(`40b4039:src/mem/packet.hh:443-456,882-956,1060-1086`). Its squash behavior
is chiefly LSQ/predictor cleanup. Nighthawk additionally sends a
generation-tagged Ruby control operation, so a late response can be rejected
against the precise lifetime. These are different correctness contracts.

## 6. Statistics gap

SDO provides detailed prediction and actual-hit-level statistics, including
exact/inexact/incorrect prediction, predicted L0/L1/L2/memory, speculative
load target-versus-hit matrices, expose/validate hit level, stalls, and
validation failure
(`40b4039:src/cpu/o3/commit.hh:530-600`,
`40b4039:src/cpu/o3/commit_impl.hh:214-303`).

The Two-Level fold leaves legacy L2 names in this schema. Before using these
statistics:

1. define whether each name is a logical prediction level or physical cache;
2. verify that all increments follow the same definition;
3. add a manifest field for the mapping version;
4. compare total issued, responses, validation/expose, re-execution, squash,
   and terminal completions for conservation.

Nighthawk exposes CPU-side tainted issue, visibility, resolved request,
generation-tagged squash, and related counts
(`8ff168d3:src/cpu/o3/lsq_unit.hh:586-626`) and controller/cache lifecycle
statistics. These are not directly comparable to SDO predictor accuracy.
The common comparison should report performance plus normalized request
lifecycle totals; mechanism-specific statistics should remain separately
labelled.

## 7. Run scripts, checkpoints, and ISA compatibility

Both intended experiments are x86 Ruby DerivO3CPU runs, so ISA is not the
largest blocker. Compatibility still must be demonstrated with the exact
checkpoint and syscall-emulation setup, not inferred from an `X86` build name.

The SDO MICRO26 scripts:

- select the Two-Level binary and external checkpoint roots
  (`40b4039:exp_script/env_MICRO26.sh:19-36`);
- expose max-instruction, checkpoint, and unique output controls
  (`40b4039:exp_script/spec17_MICRO26.sh:52-75`);
- use DerivO3CPU/Ruby common arguments
  (`40b4039:exp_script/spec17_MICRO26.sh:109-135`);
- translate scheme, memory-model, STT, implicit-channel, predictor, and TLB
  settings (`40b4039:exp_script/common_MICRO26.sh:183-215`);
- copy the executable naming convention from `sparespec-stt`
  (`40b4039:exp_script/README_MICRO26.md:71-79`).

These are encouraging integration points, but compatible filename suffixes do
not prove checkpoint compatibility. A manifest must compare:

- checkpoint provenance and workload binary SHA-256;
- gem5 checkpoint version/serialized object compatibility;
- CPU count, Ruby protocol, cache sizes/latencies, memory size and ranges;
- x86 workload ABI and run directory;
- restore/warmup/measurement instruction counts;
- stdout and committed-instruction agreement.

Do not reuse a checkpoint generated with protocol-specific in-flight Ruby
state unless restoration is shown to occur before Ruby state is materialized
or the exact protocol compatibility has been verified.

## 8. Items with no direct equivalent

The following are intentionally marked `no_direct_equivalent=true` in the CSV:

- Three-Level private L0 controller and L0↔L1 speculative-data channel;
- a distinct physical target for every L0/L1/L2/memory prediction;
- Nighthawk S-MSHR capacity, epoch, and owner-generation lifecycle;
- Nighthawk Stealth cache state, safe-priority reclaim, and slot restoration;
- Nighthawk generation-tagged squash/late-response association;
- SDO predictor training, hit-depth matrix, validation/re-execution contract;
- SDO perfect/perfect-unsafe traversal modes.

These gaps require either a documented semantic adaptation or a
mechanism-specific metric. They must not be hidden by renaming states.

## 9. Minimum safe port and validation sequence

### Stage A: freeze provenance

1. Record all three source commits and submodule hashes.
2. Hash every SLICC file included by each protocol.
3. Build `upstream/master` Three-Level and `40b4039` Two-Level in isolated
   trees with unique binary names.
4. Record compiler, SCons command, binary SHA-256, and dirty status.

### Stage B: compile and boot gates

1. Compile-only the candidate `X86_MESI_Two_Level`.
2. Run one hello/smoke workload under UnsafeBaseline, DelayExecute, and SDO.
3. Require identical architectural output and expected committed instruction
   count.
4. Treat any assertion, deadlock, lost response, or unexpected Ruby table
   residue as a failure.

### Stage C: directed semantic gates

Use one test at a time and log all request identifiers:

1. each candidate prediction target: private L1, shared L2, memory;
2. predicted shallower than actual and predicted deeper than actual;
3. response before visibility and visibility before response;
4. validation success and forced validation failure/re-execution;
5. squash before response, late response, and LQ-index reuse;
6. two same-block speculative loads plus a normal safe load;
7. transient/coherence conflict at private L1 and shared L2;
8. duplicate response/duplicate final callback rejection;
9. TLB miss under each TLB-defense mode;
10. random predictor distribution after the level fold.

For every test, assert conservation:

`issued = rejected_before_issue + exactly_one_terminal_completion`

and separately reconcile intermediate callbacks, final callbacks,
validations, re-executions, squashes, and outstanding-table occupancy.

### Stage D: apples-to-apples sanity

Only after Stage C passes, run a short slice from one reuse-rich and one
near-neutral workload using the same Nighthawk checkpoint, CPU/cache/memory
parameters, STT visibility policy, taint scope, warmup, and instruction cap.
Keep the original Three-Level SDO result separate. Do not launch a full sweep
until the Two-Level semantic review and short-run accounting are clean.

## 10. HPCA27 non-mechanism parity-profile update

The source-only parity work based on SDO commit `2fa3ce45` closes several
configuration-representation gaps against the reviewed Nighthawk artifact
whose binary source commit is `4dac93b1738bbf11408c61ccd2992d162c2c5804`.
It does not close the mechanism or runtime-validation gaps above.

The following items are now bound in source:

- `RubyCache` exposes data/tag issue intervals and per-cache `is_stt`.
  A raw interval of zero resolves to the existing access latency, so the
  reviewed `1`-cycle access/`0`-cycle raw-interval point retains the prior
  bank-occupancy behavior. Both private L1 caches explicitly use one data
  bank, one tag bank, one-cycle accesses, zero raw intervals, and STT
  visibility; the shared L2 explicitly uses the six reviewed LLC selector
  values and has STT visibility false
  (`src/mem/ruby/structures/RubyCache.py`,
  `src/mem/ruby/structures/BankedArray.cc`,
  `configs/ruby/MESI_Two_Level.py`).
- The base DRAM controller's static frontend and backend pipeline latencies
  are each `10ns`, matching the reference source. This is a non-mechanism
  timing correction and still requires emitted-config comparison
  (`src/mem/DRAMCtrl.py`).
- Every outer L1/L2 size and associativity selector and every LLC selector is
  required. The runner rejects relative, lexically non-canonical, or
  symlink-resolved source, binary, manifest, output, workload, checkpoint,
  and config paths before launch. The six LLC timing selectors are passed to
  the inner Ruby configuration
  (`exp_script/weekend_campaign/run_nighthawk_checkpoint_job.py`).
- The parity profile binds the target tree's `TournamentBP` and nested
  `SimpleIndirectPredictor` values to the reviewed numeric and boolean
  semantics, including the post-checkpoint switch CPU
  (`configs/common/SDOConfig.py`, `configs/common/Simulation.py`).

The branch predictor remains **partial** at the evidence layer. The reference
schema stores `useIndirect` and indirect parameters directly on
`TournamentBP`; this tree stores them in an `indirectBranchPred` child.
[`hpca27_branch_predictor_evidence_adapter.md`](hpca27_branch_predictor_evidence_adapter.md)
specifies the exact fail-closed structural checks and normalization that an
external parity checker would need. That adapter is proposed, not implemented
in the external checker, so an exhaustive config projection must continue to
report the representation mismatch.

These changes have Python-compatible source regressions but no fresh gem5
binary, emitted `config.ini`/`config.json`, checkpoint run, architectural
result, or artifact-bound parity verdict. Their status is therefore
**source-bound / runtime-unvalidated**, not exact parity.

## Status

This audit establishes the source-level gap and a validation plan. It does not
establish:

- that `40b4039` builds;
- that current Two-Level SDO is functionally correct;
- that it is semantically equivalent to upstream Three-Level SDO;
- that checkpoints restore across both binaries;
- any performance, security, area, power, or timing result.

Until those gates pass, label the implementation
**“candidate Two-Level SDO port”**, not **“exact SDO reproduction.”**

The repository now includes the fail-closed compile-only driver
`tests/nighthawk_sdo_port/compile_x86_mesi_two_level.sh`. It preserves a unique
manifest and binary hash when run, but the Stage-B compile gate remains
**NOT RUN**: no binary, boot, workload, or checkpoint result is claimed by this
source-only addition.
