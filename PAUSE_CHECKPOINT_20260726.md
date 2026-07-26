# HPCA 2027 Nighthawk pause checkpoint

Paused safely at 2026-07-26 21:33 KST (12:33 UTC) at the user's request.
This file is the cross-lane restart index.  Per-lane resume notes remain the
authoritative detailed instructions.

## Verified quiescent state

- `caslab-sim` (`165.132.146.134`): no `gem5.opt` or sidecar build process;
  the persistent lock file exists but `lslocks` reports no owner.
- RTL host (`192.168.0.71`): no SBY, solver, Yosys, Icarus, Verilator,
  OpenROAD, or Nighthawk user scope remains.
- Baseline host at pause: `MemAvailable=1,044,392,360 kB`, memory PSI zero.
- RTL host at pause: `MemAvailable=62,915,540 kB`, memory PSI zero.
- No protected source, binary, result, checkpoint, container, or campaign
  process was changed or stopped.
- All future RTL-host commands, including manifest/hash post-processing, must
  run within CPU set `{1,2,7,13}`.  Logical CPUs `{0,4,6,8,12,14}` are
  forbidden.

## Baseline lane

### AuxBuffer+STT

- Branch: `hpca27/auxbuffer-exact-budget-calibration`
- Pause/resume tip: `e17bdddec5fcb7f6ffec88a05be7079b16678c9d`
- Calibration tooling: `547e5d52b9f39f53fe59add0f6306db7b5364da0`
- Detailed note:
  `/private/tmp/nighthawk-baseline-aux-budget-calibration/docs/AUXBUFFER_EXACT_BUDGET_RESUME_20260726.md`
- Preserved original gate failure: requested 10,000,000 but reference
  committed 10,000,001.
- First exact reachable reference point PASS:
  requested = committed = 10,000,001.
- PASS run:
  `/home/minwoo/hpca27_sidecar/runs/aux-budget-calibration-i1-reference-cactu-10000001/20260726T122436Z_nighthawk-reference_p2018586`
- Audit SHA-256:
  `e5063ad64a1968c150692fae9a2ef4576d879e920f957ffb733e31044083b148`
- Manifest SHA-256:
  `0c9788a88d8e3d1ce9cbb800c90e12ff08da077f61a21c95de067bae83785c9c`
- Candidate cactu slice, libquantum calibration/slices, and full sweep were
  not launched.  Resume with the candidate exact-budget cactu point only
  after a fresh guard and lock check.

### Nighthawk-NoEarly

- Branch/commit:
  `hpca27/noearly-owner-accounting-integration` at
  `23a935647278837601ad3f561a2f0f2cabe21062`
- Binary SHA-256:
  `afde87369dc0708b0577cf0414115e2612ec37ee84347f0321337d82fe6d5d8b`
- Directed 8/8 and hello 1/1 PASS; every run ended with one terminal marker,
  zero negative markers, and zero final owner/fragment/TBE/S-MSHR occupancy.
- Suite:
  `/home/minwoo/hpca27_sidecar/runs/noearly-directed/noearly-directed-suite-23a93564-20260726T120920Z`
- Archive:
  `/home/minwoo/hpca27_sidecar/archives/noearly-directed-23a93564-20260726T120920Z.tar.gz`
- Archive SHA-256:
  `da1f19ad3fe772658361b38169d782cdc94699ae4e498cd22bd8600fbaa6d1e3`
- Performance parity bundle and the two checkpoint slices remain HOLD.

### SDO

- Mechanism binary source commit:
  `426ed88a85300e75926b661594ec716d4a916342`
- Documentation tip: `4801d97`
- Binary SHA-256:
  `6df37ee8d537a16e861bfa38974ddc19d8228d8e8bfc1b149b07dd00ff7e006e`
- Status remains `SDO-style partial port` / HOLD.  Compile, source tests,
  hello, and callback accounting passed, but required Three-Level to
  Two-Level semantics remain unresolved.  No checkpoint slice or full sweep
  was launched.

## RTL lane

### Full-cache production top

- Branch: `hpca27/rtl-full-cache-top`
- Pause/resume tip:
  `1872a51b90ac3b807f8f8d69e6d9bc93c6b8dde4`
- Functional RTL:
  `e2e0440125a0c250468acf345cb6dece77d344e9`
- Detailed note:
  `/private/tmp/nighthawk-rtl-full-cache-top/RESUME_RTL_FULL_CACHE_TOP_20260726.md`
- Implemented global 10-bit `{set,way}` ownership, one global eight-entry
  S-MSHR manager, a serialized tag/metadata snapshot interface, matched STT
  shell, and a deterministic same-way cross-set test for sets 5 and 9.
- Icarus unit 10/10 PASS; Verilator unit 10/10 PASS.
- Random/reference: Icarus 18/18 and Verilator 18/18 PASS, 30,384 operations
  each.
- HOLD before freeze/PPA: update production contract and metadata ledger,
  resolve canonical co-located-tag versus external installed metadata,
  preserve stale-owner safety, and rerun lint/unit/random from the final
  functional commit.

### Formal

- Branch/report tip:
  `hpca27/rtl-formal-expanded` at
  `772502213e1c8ca9919ca84075d2943bb7477c6d`
- Formal design/evidence source:
  `6885d0e451c20abf1644eb56e2f4fdd65eee2fe9`
- Valid end-to-end pinned bounded run:
  `/home/minwoo/hdd/hpca27_sidecar/nighthawk-rtl/runs/20260726T124000Z_formal-final-e2e-pinned-6885d0e`
- Bounded result: 14/14 PASS and 35/35 covers, 917 affinity samples with
  zero violations.
- Valid induction attempt:
  `/home/minwoo/hdd/hpca27_sidecar/nighthawk-rtl/runs/20260726T125500Z_formal-induction-e2e-pinned-6885d0e`
- Induction classification: base depth 16 PASS, induction UNPROVEN; do not
  claim an unbounded proof.
- An earlier manifest/hash post-process briefly used forbidden CPU 8.  Those
  artifacts are excluded and classified `AFFINITY_FAIL` under:
  `/home/minwoo/hdd/hpca27_sidecar/nighthawk-rtl/runs/20260726T123000Z_formal-affinity-fail-classification-6885d0e`
- Any change to the production RTL requires the whole pinned formal suite to
  be regenerated.

### PPA and power infrastructure

- Branch: `hpca27/rtl-production-contract-v2`
- Tip: `ed21973c96c0f2288986f73d45de37bc41c3e14b`
- Added matched W8 Nighthawk/STT ORFS configs, 2/3/4 ns and seed 1/2/3
  controls, strict source/tool pin checks, endpoint/timing/DRC acceptance
  audit, and routed VCD power-report Tcl.
- Final PPA/power was not launched.
- ORFS-pinned Yosys build attempts are preserved:
  submodule, readline header, FFI header, and FFI link failures were fixed
  incrementally.  The final clean v5 attempt included the rootless Tcl and
  FFI development bundle paths but was deliberately terminated for this
  pause.
- Paused Yosys v5 run:
  `/home/minwoo/hdd/hpca27_sidecar/nighthawk-rtl/runs/20260726T122410Z_yosys-pin-aaa534749-v5_8dd9e6fe386c_p1265275`
- It ended with exit 143 after exact scope-only `TERM`; peak RSS was
  1,394,236 KiB and no emergency threshold fired.
- On resume, use new `-v6` source/install directories rather than overwriting
  v5, with:
  - Tcl include:
    `/home/minwoo/hdd/hpca27_sidecar/nighthawk-rtl/tools/deps-noble-tcl8.6-dev-8.6.14/root/usr/include/tcl8.6`
  - FFI include:
    `/home/minwoo/hdd/hpca27_sidecar/nighthawk-rtl/tools/deps-noble-libffi-dev-3.4.6/root/usr/include/x86_64-linux-gnu`
  - FFI library:
    `/home/minwoo/hdd/hpca27_sidecar/nighthawk-rtl/tools/deps-noble-libffi-dev-3.4.6/root/usr/lib/x86_64-linux-gnu`

## Resume order

1. Re-run protected-state, lock, memory/swap/PSI/OOM, and CPU-affinity
   preflight.  Do not reuse or overwrite any listed result directory.
2. Resume AuxBuffer at its exact-budget candidate cactu slice, then calibrate
   and run the near-neutral libquantum pair.  Keep gem5 concurrency at one.
3. Complete NoEarly closed-world parity and the same two exact-budget slices.
4. Merge the full-cache top, production contract/PPA infrastructure, and
   formal changes on a new integration branch.  Resolve metadata ownership
   before freezing one clean commit.
5. Build the ORFS-pinned Yosys tool in new v6 directories, then rerun lint,
   Icarus, Verilator, random/reference, trace replay, activity, formal, Yosys,
   and OpenROAD from the one frozen commit.
6. Launch no full sweep until the candidate-specific hard gates pass.  SDO
   remains HOLD until its mapping audit has no unresolved required semantic
   item.

At pause, no performance candidate was certified for a full sweep and no
final RTL PPA or workload-power claim was available.
