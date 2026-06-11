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

Useful overrides:

```bash
export GEM5_PATH=/root/sdo
export GEM5_BIN=$GEM5_PATH/build/X86_MESI_Two_Level/gem5.opt
export SPEC_PATH=/root/Benchmark/SPEC2017
export SPEC06_PATH=/root/Benchmark/SPEC2006
export CKPT_PATH=/root/Benchmark/spare_ckpt
export OUTPUT_ROOT=$GEM5_PATH/output/MICRO26

BENCHMARKS="mcf lbm xz" SCHEMES="UnsafeBaseline DelayExecute SDO" ./runall_spec17_MICRO26.sh
THREAT_MODELS="Spectre" STT_VALUES="1" IMP_CHANNEL_VALUES="1" ./runall_spec06_MICRO26.sh
PRED_TYPE=tournament_2way SUBPRED1_TYPE=greedy SUBPRED2_TYPE=loop PRED_OPTION=0 ./spec17_MICRO26.sh mcf SDO
GEM5_DEBUG_FLAGS=SpecBuffer,MemSpecBuffer,LSQUnit,LSQ ./spec17_MICRO26.sh mcf SDO
DRY_RUN=1 USE_CHECKPOINT=0 ./spec06_MICRO26.sh mcf SDO
```

Default scheme coverage:

- `UnsafeBaseline`: unprotected baseline, no `--threat_model` passed.
- `DelayExecute`: STT-style delayed execution with `--STT=1 --impChannel=1`.
- `SDO`: SDO with `tournament_2way(greedy, loop)`, `--pred_option=0`, and
  `--TLB_defense=SDO`.

The SPEC benchmark modules also honor:

- `SPEC06_RUN_DIR` / `SPEC17_RUN_DIR`: absolute run directory for executable
  lookup and process cwd.
- `SPEC06_EXEC_PREFIX` / `SPEC17_EXEC_PREFIX`: optional executable directory
  override.
- `SPEC06_X86_SUFFIX` / `SPEC17_X86_SUFFIX`: binary suffix override. The
  defaults match `sparespec-stt`: `_base.Xeon-gcc4.3` for SPEC2006 and
  `_r_base.sparespec-m64` for SPEC2017.
