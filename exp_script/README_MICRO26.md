# MICRO26 SDO Experiment Scripts

These scripts run the two-level `MESI_Two_Level` SDO configuration in this
repository. They borrow the SPEC checkpoint/run-directory flow used by
`sparespec-stt` and `stt-invisibase`, but use this repo's SDO options:
`--scheme`, `--mem_model`, `--STT`, `--impChannel`, predictor options, and
`--TLB_defense`.

Typical setup:

```bash
cd /root/sdo/exp_script
source ./env_MICRO26.sh
```

Run one benchmark:

```bash
./spec17_MICRO26.sh mcf SDO 1 1 Spectre
./spec06_MICRO26.sh mcf DelayExecute 1 1 Futuristic
USE_CHECKPOINT=0 ./spec17_MICRO26.sh mcf UnsafeBaseline
```

Run the default MICRO sweep:

```bash
MAX_JOBS=4 ./runall_spec17_MICRO26.sh
MAX_JOBS=4 ./runall_spec06_MICRO26.sh
```

By default, the runall scripts are limited to the plotted MICRO26 benchmark set.
SPEC2006 runs:

```text
perlbench bzip2 gcc mcf milc namd gobmk povray libquantum h264ref omnetpp astar sphinx3
```

SPEC2017 runs:

```text
cactuBSSN namd parest povray lbm x264 imagick leela nab xz
```

Useful overrides:

```bash
export GEM5_PATH=/root/sdo
export GEM5_BIN=$GEM5_PATH/build/X86_MESI_Two_Level/gem5.opt
export SPEC_PATH=/root/Benchmark/SPEC2017
export SPEC06_PATH=/root/Benchmark/SPEC2006
export CKPT_PATH=/root/Benchmark/spare_ckpt
export OUTPUT_ROOT=$GEM5_PATH/output/MICRO26

BENCHMARKS="mcf lbm xz" SCHEMES="UnsafeBaseline DelayExecute SDO" ./runall_spec17_MICRO26.sh
THREAT_MODELS="Spectre" STT_VALUES="0 1" IMP_CHANNEL_VALUES="0 1" ./runall_spec06_MICRO26.sh
PRED_TYPE=tournament_2way SUBPRED1_TYPE=greedy SUBPRED2_TYPE=loop PRED_OPTION=0 ./spec17_MICRO26.sh mcf SDO
GEM5_DEBUG_FLAGS=SpecBuffer,MemSpecBuffer,LSQUnit,LSQ ./spec17_MICRO26.sh mcf SDO
DRY_RUN=1 USE_CHECKPOINT=0 ./spec06_MICRO26.sh mcf SDO
```

Default scheme coverage:

- `UnsafeBaseline`: unprotected baseline, no `--threat_model` passed.
- `DelayExecute`: STT-style delayed execution for `STT0_Impl0`,
  `STT1_Impl0`, and `STT1_Impl1`.
- `SDO`: SDO for `STT0_Impl0`, `STT1_Impl0`, and `STT1_Impl1`, using
  `tournament_2way(greedy, loop)`, `--pred_option=0`, and
  `--TLB_defense=SDO`.
- `STT0_Impl1` is skipped because it is an invalid configuration.

The SPEC benchmark modules also honor:

- `SPEC06_RUN_DIR` / `SPEC17_RUN_DIR`: absolute run directory for executable
  lookup and process cwd.
- `SPEC06_EXEC_PREFIX` / `SPEC17_EXEC_PREFIX`: optional executable directory
  override.
- `SPEC06_X86_SUFFIX` / `SPEC17_X86_SUFFIX`: binary suffix override. The
  defaults match `sparespec-stt`: `_base.Xeon-gcc4.3` for SPEC2006 and
  `_r_base.sparespec-m64` for SPEC2017.

## HPCA27 performance-parity runner

The MICRO26 scripts above retain their historical/reference defaults and are
not performance-parity evidence. In particular, they may select TSO, a 100M
instruction budget, and Ruby resource stalls.

Final checkpoint candidates must instead use the tracked canonical outer
runner path:

```text
exp_script/weekend_campaign/run_nighthawk_checkpoint_job.py
```

Its outer CLI matches the Nighthawk campaign evidence contract and accepts
only `sdo-implicit`, `Futuristic`, `current`, `not_applicable` pending policy,
zero Nighthawk S-MSHRs, and the 500M post-restore ROI. The emitted gem5 command
selects the explicit `--hpca27-performance-parity` profile. That profile fails
closed unless the non-mechanism CPU/cache/Ruby/memory controls match the
reviewed `sparespec-stt` reference, including RC (`needsTSO=false`), the O3
width/queue/register/port values, disabled Ruby cache resource stalls, and
one-cycle sequencer hit latency. All L1/L2 size and associativity selectors and
all LLC bank/latency/issue selectors must be supplied explicitly; none is
accepted by omission.

The runner also binds the source commit, binary and manifest hashes, workload
row, checkpoint selector, exact inner command, and thread environment. It
rejects relative, symlink-resolved, or lexically non-canonical identity paths
before launch. It writes `execution_identity.json` and
`canonical_workload_row.json` before launch. A successful run is still only a
candidate: the immutable artifact bundle must pass the separate
`nighthawk-baseline` v2 parity gate. In particular, the nested branch-predictor
representation still needs the fail-closed evidence adapter proposed in
`docs/hpca27_branch_predictor_evidence_adapter.md`, and the Two-Level SDO
semantic gaps documented in `docs/sdo_porting_gap.md` remain.
