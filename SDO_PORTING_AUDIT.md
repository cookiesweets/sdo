# SDO porting audit — HPCA 2027

Date: 2026-07-26  
Candidate disposition: **HOLD — SDO-style partial port**

This report separates executable/accounting evidence from semantic and
performance certification.  It does not call the current Two-Level candidate
an exact SDO reproduction.

## Frozen identities

| Artifact | Identity |
|---|---|
| SDO source | `hpca27/sdo-candidate-v2-integrated` at clean commit `426ed88a85300e75926b661594ec716d4a916342` |
| SDO binary | SHA-256 `6df37ee8d537a16e861bfa38974ddc19d8228d8e8bfc1b149b07dd00ff7e006e` |
| Protected Nighthawk reference source | `4dac93b1738bbf11408c61ccd2992d162c2c5804` |
| Protected Nighthawk reference binary | SHA-256 `dc0dd1f0632c978b178412f56903a88da24e3116c3f5f1a9dc4bc072146d52c5` |
| Evidence adapter | `hpca27/sdo-branch-evidence-adapter` at `91370ace2a4383e98aa5d420ae986b08413dcf1d` |

## Evidence matrix

| Layer | Result | Evidence and interpretation |
|---|---|---|
| Source tests | PASS | 52/52 at `/home/minwoo/hpca27_sidecar/runs/sdo-candidate-v2-integrated-build-426ed88-20260726T105133Z` |
| Clean build | PASS | Same directory; artifact manifest SHA-256 `fdaf6363b515bcbdb9bfc5fb4ff477fc21f1285d91bff12d8af562f6c335ae43` |
| Callback accounting | PASS | `/home/minwoo/hpca27_sidecar/runs/sdo-hello-l1-trace-426ed88-bin426ed88-20260726T105736Z`; 1,345 unique split-aware transactions, L0=1,345, L1=1,345, duplicate/missing/stuck=0; manifest SHA-256 `8a0ff6e3ab024a53a8c237a8a0efb50f18b83b7acadb1f8b38f2ca93953efcdb` |
| MLDOM response owners | PASS | CPU, RubySystem, L1, and Directory enablement observed in the hello bundle |
| Branch-config representation adapter | PASS | Fail-closed identity-bound adapter, 89/89 policy tests; `/home/minwoo/hpca27_sidecar/runs/sdo-branch-adapter-policy-tests-91370ac-20260726T1101Z` |
| Branch-predictor runtime semantics | HOLD | Nested predictor history/update/recovery has not been shown equivalent to the reference direct-field implementation |
| Closed-world raw config parity | HOLD | Final initialize-only capture has 22 raw differences; the reviewed adapter reduces these to two: the SDO mechanism latency and the common 10M sanity budget |
| Three-Level to Two-Level mapping | HOLD | 40 rows reviewed; 17 have no direct equivalent; folded target-depth and identity semantics remain adapted/unsupported rather than exact |
| Reuse-rich short slice | NOT RUN | Hard semantic/parity gates did not pass |
| Near-neutral short slice | NOT RUN | Hard semantic/parity gates did not pass |
| Full sweep | NOT AUTHORIZED | Candidate remains HOLD |

The final initialize-only capture is
`/home/minwoo/hpca27_sidecar/runs/sdo-v2-prelaunch-cactuBSSN-10m-426ed88-20260726T110423Z`.
Its final manifest SHA-256 is
`a23b7dde829b4e539a489305b8544fc924681c7cdfd10faddf5e222d20fa18d8`;
the preserved semantic-HOLD report SHA-256 is
`347c066dec75f2e0a98a59e6e04a4af82abc78cd387ddb5165ac0edf855d2f84`.
This directory is an initialize-only parity capture, not a performance run.

## Exact/adapted/omitted judgment

- Exact end-to-end SDO mechanisms certified on Two-Level: **none yet**.
- Rows not marked `no_direct_equivalent`: **23 of 40**.  They include adapted,
  retained, target-only, and source-bound categories; this count is not an
  exact-equivalence count.  Every row remains subject to its residual risk and
  required validation in `docs/sdo_three_to_two_mapping.csv`.
- No-direct-equivalent mappings: **17 of 40**.  These include the removed
  private cache level/channel, folded prediction target, legacy response
  fields, and topology-specific controller behavior.
- Omitted or unsupported required evidence: exact target-depth equivalence,
  predictor runtime update/recovery equivalence, generation-safe late-response
  ownership, and a reviewed mapping for the SDO-specific response latency.

## Paper-safe statement

The current code is a buildable, callback-accounted **SDO-style partial port**
to `X86_MESI_Two_Level`.  It is not an exact reproduction and supplies no
paper performance point.  The original Three-Level result, if reproduced,
must remain separately labelled and cannot be used as the apples-to-apples
bar against Two-Level Nighthawk.
