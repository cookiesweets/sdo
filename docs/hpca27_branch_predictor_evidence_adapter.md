# HPCA27 branch-predictor evidence adapter

The HPCA27 Nighthawk reference and this SDO tree express the same reviewed
TournamentBP and indirect-predictor parameter intent through different gem5
schemas. The settings below close the numeric configuration gap; they do not,
by themselves, prove algorithmic runtime equivalence between the two gem5
branch-predictor implementations. This is not an SDO mechanism difference.

The reference stores `useIndirect` and the `indirect*` parameters directly in
the TournamentBP section. This tree stores the indirect parameters in a
`SimpleIndirectPredictor` child selected by `indirectBranchPred`; the presence
of that child is the equivalent of `useIndirect=true`. Rewriting the older
direct-field C++ interface into this tree would change branch-predictor object
construction and is outside the parity port.

The opt-in SDO parity profile explicitly binds the following values:

| Canonical reference field | SDO config field | Required value |
| --- | --- | --- |
| `type` | branch `type` | `TournamentBP` |
| `btb_entries` | branch `BTBEntries` | `4096` |
| `btb_tag_bits` | branch `BTBTagSize` | `16` |
| `ras_entries` | branch `RASSize` | `16` |
| `inst_shift` | branch `instShiftAmt` | `2` |
| `local_predictor_entries` | branch `localPredictorSize` | `2048` |
| `local_ctr_bits` | branch `localCtrBits` | `2` |
| `local_history_entries` | branch `localHistoryTableSize` | `2048` |
| `global_entries` | branch `globalPredictorSize` | `8192` |
| `global_ctr_bits` | branch `globalCtrBits` | `2` |
| `choice_entries` | branch `choicePredictorSize` | `8192` |
| `choice_ctr_bits` | branch `choiceCtrBits` | `2` |
| `use_indirect` | nested-child presence | `true` |
| indirect predictor type | child `type` | `SimpleIndirectPredictor` |
| `indirect_hash_ghr` | child `indirectHashGHR` | `true` |
| `indirect_hash_targets` | child `indirectHashTargets` | `true` |
| `indirect_sets` | child `indirectSets` | `256` |
| `indirect_ways` | child `indirectWays` | `2` |
| `indirect_tag_bits` | child `indirectTagSize` | `16` |
| `indirect_path_length` | child `indirectPathLength` | `3` |
| nested schema guard | child `indirectGHRBits` | `13` |
| nested schema guard | child `instShiftAmt` | `2` |

## Proposed evidence normalization

The artifact checker should apply a versioned adapter only when the candidate
declares the SDO source identity and all of these structural checks pass:

1. The adapter names an exact reviewed candidate source commit, simulator
   binary hash, build-provenance hash, config-projection version, and adapter
   policy hash. An unreviewed source or binary must not select the adapter by
   merely declaring `kind=SDO`.
2. There is exactly one measured `DerivO3CPU`, with exactly one branch
   predictor of type `TournamentBP`.
3. The branch section has all eleven direct fields in the table with the
   required types and values.
4. The branch section has exactly one `indirectBranchPred` child reference,
   and that reference resolves to a distinct, present
   `SimpleIndirectPredictor` section.
5. The child has all eight nested fields in the table with the required types
   and values. `numThreads` must resolve to `1`.
6. The direct branch section must not also contain any of `useIndirect`,
   `indirectHashGHR`, `indirectHashTargets`, `indirectSets`, `indirectWays`,
   `indirectTagSize`, or `indirectPathLength`. A mixed schema is ambiguous and
   must fail.
7. The child section may contain normal SimObject identity and event fields,
   but no additional behavior-selecting predictor parameter may be silently
   discarded. Unknown scalar or child parameters must fail until reviewed.

After those checks, the adapter may project the nested values onto the
canonical reference names, synthesize `use_indirect=true`, and omit only the
now-redundant child section and branch-to-child reference from the exhaustive
non-mechanism projection. It must then run the ordinary exact field comparison
and exhaustive projection comparison. A missing child, null reference, type
change, value change, extra predictor child, unknown behavior parameter, or
mixed direct/nested schema remains a parity failure.

This proposal does not itself admit an artifact. The external parity checker
must implement and test the adapter, and the two predictor implementations
still require a bounded semantic review, before an SDO run can pass the
artifact-bound gate.
