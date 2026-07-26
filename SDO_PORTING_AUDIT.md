# SDO porting audit — final candidate disposition

Date: 2026-07-26

## Decision

The current implementation is an **SDO-style partial port**. Its performance
status is **HOLD**.

It is not an exact reproduction of Three-Level SDO on
`X86_MESI_Two_Level`, and it is not certified for an apples-to-apples
checkpoint slice or full sweep. This decision is fail-closed: successful
compilation, a normal hello exit, and a generated `stats.txt` establish that
the simulator ran, but do not resolve the remaining protocol semantics and
artifact-parity gates.

## Frozen identity

| Item | Frozen value |
|---|---|
| Source branch | `hpca27/sdo-candidate-v2-integrated` |
| Source commit | `426ed88a85300e75926b661594ec716d4a916342` |
| Parity/default parent | `98ee72283f9237a015a131f3d7fb84d2c45e1f7d` |
| Callback-audit parent | `c09e3a1616ebb5f08f092fd760ccd64eefca80c3` |
| Protocol | `X86_MESI_Two_Level` |
| Binary SHA-256 | `6df37ee8d537a16e861bfa38974ddc19d8228d8e8bfc1b149b07dd00ff7e006e` |
| Adapter-policy commit | `91370ace2a4383e98aa5d420ae986b08413dcf1d` |
| Adapter-policy SHA-256 | `8b33f10649cd769b3f2d229f7627a7b7b6c2ee406c0f8d158d13644f0eb36a40` |

The evaluated source and binary are isolated sidecar artifacts. They do not
reuse or write the protected Nighthawk source, binary, results, containers, or
checkpoint root.

## Evidence matrix

| Layer | Status | Evidence | Claim boundary |
|---|---|---|---|
| Clean isolated build | PASS | 52/52 source tests; binary hash above | Buildability only |
| Hello simulator execution | PASS | Raw simulator exit 0 and `m5out/stats.txt` | Simulator smoke only |
| MLDOM response ownership | PASS | CPU, RubySystem, L1, and Directory all enabled | Selected generated configuration only |
| Split-transaction callbacks | PASS | 1,345 unique transactions; 1,345 L0 and 1,345 L1 callbacks; no duplicate/missing/stuck transaction | Static-L1 20K hello trace only |
| Branch adapter policy | PASS | 89/89 fail-closed policy tests | Config representation only |
| Raw closed-world config | HOLD | 22 leaves differ | Not exact raw parity |
| Adapted closed-world config | HOLD | 20 representation leaves folded; two differences remain | No runtime predictor equivalence |
| Canonical artifact identity | FAIL | SPEC2017 candidate capture conflicts with available SPEC2006 reference identity and checkpoint paths | No checkpoint comparison |
| Directed semantic matrix | HOLD | Required target-depth, validation, squash/reuse, and transient tests incomplete | No protocol equivalence |
| Reuse-rich slice | NOT RUN | Prelaunch failed closed | No performance evidence |
| Near-neutral slice | NOT RUN | Prelaunch failed closed | No performance evidence |
| Full sweep | NOT AUTHORIZED | Required gates unresolved | Must remain out of main graph |

## Mechanism mapping

`Exact` below means the reviewed local behavior has a direct counterpart and
matching evidence. It does not mean whole-design equivalence.

| SDO mechanism | Original Three-Level hook/state/message | Two-Level replacement | Classification | Directed evidence | Residual semantic risk |
|---|---|---|---|---|---|
| First private-cache target | `GETSPEC_L0` at private L0 | `GETSPEC_L0` at physical private L1 | Adapted | Static-L1 hello callback conservation | Physical latency/capacity and controller boundary changed |
| Middle/shared-cache target | `GETSPEC_L1` passing private L0 to private L1 | legacy `GETSPEC_L2` passing private L1 to shared L2 | Adapted | Callback source contract tests | Private-to-shared contention and timing changed |
| Old physical L2 target | `GETSPEC_L2` at shared L2 | Folded into the shared-L2 target | Unsupported as a distinct target | Source-level fold contract test | No one-to-one physical target exists |
| Memory target | `GETSPEC_Mem` through L0/L1/L2 | `GETSPEC_Mem` through private L1/shared L2 | Adapted | Metadata propagation source tests | Same-line/transient memory paths not directed-tested |
| Private speculative-data channel | Dedicated L1→L0 message buffer | No corresponding private hop | Omitted | Topology source audit | Queueing and response ordering cannot be reproduced exactly |
| Hit-level compatibility fields | Four hit flags/data blocks | Four legacy fields retained | Adapted | Exclusive-hit flag reset test | Impossible physical levels can be misreported without normalization |
| Intermediate/final callback pair | Per-level callback then target confirmation | Split-aware L0/L1 pair | Adapted | 1,345/1,345 exact callback pairs | Hello uses one static target and does not cover every level/race |
| MLDOM response ownership | CPU and protocol response owners | CPU, RubySystem, L1, Directory | Exact for selected config | Four-component config audit PASS | Other configurations can still disable ownership |
| Candidate-data carry/copy | First hit carries data; target confirms | Retained packet fields and callback path | Adapted | Merge/copy source-contract tests | Data equality and forced validation failure not exercised |
| Visibility-gated forwarding | LSQ holds early data until expose-ready | Retained expose/validate path | Adapted | Source contract only | No dependent-wakeup response-first/visibility-first directed trace |
| Validation/re-execution | Expose/validate and data compare | Retained with physical-level remap | Adapted | Source contract only | Match/mismatch matrix at each physical level is missing |
| Squash and late response | LSQ removes load; later completion ignored | Retained without explicit owner generation | Adapted | Auditor negative fixtures only | Reused LQ index can alias a stale response |
| Same-line speculative merge | Sequencer speculative table | Retained table/collision path | Adapted | Merge nesting/source tests | Multi-request live protocol trace is missing |
| `spec_data_to_l1_latency` | Three-Level private response transport latency | Two-Level shared-to-private value `2` | Adapted, unresolved | Present in generated config | No approved mechanism allowlist or matched sensitivity evidence |
| Location-predictor distribution | Four distinct L0/L1/L2/memory outcomes | Folded outcomes can select the same shared L2 | Adapted, unresolved | Source fold test | Target probability distribution can change performance |
| Branch predictor | Inline TournamentBP indirect history | Nested `SimpleIndirectPredictor` with 13-bit speculative history | Adapted, unresolved | Fail-closed config adapter tests | Update/recovery algorithm is not runtime-equivalent by construction |
| Nighthawk S-MSHR/Stealth ownership | No counterpart | Deliberately absent from SDO | Not applicable | Source audit | Adding it would create a hybrid baseline |

## Configuration and artifact parity

The raw `config.ini` projection has 22 differences:

- 20 reviewed branch-predictor schema/representation leaves;
- `system.ruby.l2_cntrl0.spec_data_to_l1_latency=2`, which is mechanism
  specific and not approved for performance;
- the explicit 10M sanity budget instead of the 500M reference budget.

The branch adapter folds only the 20 reviewed representation leaves and emits
separate receipts for `config.ini` and `config.json`. After adaptation, the
mechanism latency and common sanity budget remain visible. This is correct
fail-closed behavior.

The actual prelaunch gate still fails because the captured candidate selected
SPEC2017 `507.cactuBSSN_r`, while the available canonical reference manifest
and primary config contract selected SPEC2006. Workload roots and checkpoint
selectors also resolve to different paths. No allowlist can repair an
artifact-identity mismatch, so no checkpoint gem5 run was started.

## Required work to leave HOLD

All items below are mandatory:

1. Select one workload generation and obtain a byte-identical reference
   workload, arguments, checkpoint metadata, and checkpoint-memory manifest.
2. Review and approve only the true mechanism field
   `spec_data_to_l1_latency`, without accepting any non-mechanism drift.
3. Decide whether the nested indirect predictor is part of the candidate
   mechanism or replace it with the reference implementation; numeric
   normalization alone is insufficient.
4. Run directed private-L1, shared-L2, and memory target tests, including
   response-first and visibility-first ordering.
5. Run validation match/mismatch, squash-before-response, late response with
   LQ-slot reuse, duplicate/orphan response, same-line merge, and transient
   coherence tests.
6. Require unique issue/callback/terminal conservation and zero outstanding
   occupancy for every directed case.
7. Pass one reuse-rich and one near-neutral common-budget checkpoint slice
   sequentially, with normal terminal cause, matching architecture output,
   and the same reference artifacts.

Only then may SDO be reconsidered for a full sweep. If the distinct old
physical-L2 target and private L0 hop remain impossible by construction, the
paper label must stay `SDO-style partial port`, even if the adapted Two-Level
candidate later becomes useful as a qualified comparison point.

## Immutable remote evidence

- Build:
  `/home/minwoo/hpca27_sidecar/runs/sdo-candidate-v2-integrated-build-426ed88-20260726T105133Z`
- Hello/callback:
  `/home/minwoo/hpca27_sidecar/runs/sdo-hello-l1-trace-426ed88-bin426ed88-20260726T105736Z`
- Prelaunch/parity:
  `/home/minwoo/hpca27_sidecar/runs/sdo-v2-prelaunch-cactuBSSN-10m-426ed88-20260726T110423Z`
- Adapter policy:
  `/home/minwoo/hpca27_sidecar/runs/sdo-branch-adapter-policy-tests-91370ac-20260726T1101Z`

These paths are evidence locations on `caslab-sim`, not protected campaign
artifacts.
