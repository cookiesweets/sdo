#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/env_MICRO26.sh"
source "$SCRIPT_DIR/common_MICRO26.sh"

usage() {
    echo "Usage: $0 <benchmark> <scheme> [STT:0|1] [impChannel:0|1] [threat_model]"
    echo "Example: $0 mcf SDO 1 1 Spectre"
    echo "Example: USE_CHECKPOINT=0 DRY_RUN=1 $0 mcf DelayExecute 1 1 Futuristic"
}

if [[ "$#" -lt 2 ]]; then
    usage
    exit 1
fi

BENCHMARK=$1
SCHEME=$2
STT=${3:-1}
IMP_CHANNEL=${4:-1}
THREAT_MODEL=${5:-Spectre}

validate_scheme "$SCHEME"
validate_bool STT "$STT"
validate_bool impChannel "$IMP_CHANNEL"
if [[ "$STT" == "0" && "$IMP_CHANNEL" == "1" ]]; then
    die "STT0_Impl1 is invalid; use STT0_Impl0, STT1_Impl0, or STT1_Impl1"
fi
if [[ "$SCHEME" == "UnsafeBaseline" ]]; then
    STT=0
    IMP_CHANNEL=0
else
    validate_threat "$THREAT_MODEL"
fi

require_var GEM5_PATH
require_var GEM5_BIN
require_var SPEC_PATH
require_var OUTPUT_ROOT

BENCHMARK_CODE=$(spec17_code "$BENCHMARK") || die "unknown SPEC2017 benchmark '$BENCHMARK'"
BENCHSPEC_DIR=$(resolve_spec17_benchspec)
RUN_DIR=$BENCHSPEC_DIR/$BENCHMARK_CODE/run/${SPEC17_RUN_DIR_NAME:-run_base_refrate_sparespec-m64.0000}

if [[ ! -d "$RUN_DIR" ]]; then
    die "run directory not found: $RUN_DIR"
fi

MAX_INSTS=${MAX_INSTS:-100000000}
CHECKPOINT_CONFIG=${CHECKPOINT_CONFIG:-ooo_8Gmem_10Bn}
RUN_CONFIG=${RUN_CONFIG:-Ref}
NUM_CPUS=${NUM_CPUS:-1}
NUM_L2CACHES=${NUM_L2CACHES:-1}
NUM_DIRS=${NUM_DIRS:-1}
MESH_ROWS=${MESH_ROWS:-1}
MEM_SIZE=${MEM_SIZE:-8GB}
MSHR_SIZE=${MSHR_SIZE:-16}
CLEAN_OUTPUT=${CLEAN_OUTPUT:-1}

THREAT_DIR=$THREAT_MODEL
if [[ "$SCHEME" == "UnsafeBaseline" ]]; then
    THREAT_DIR=NoThreat
fi

PRED_DIR=NoPred
if [[ "$SCHEME" == "SDO" ]]; then
    PRED_DIR=${PRED_TYPE:-tournament_2way}_opt${PRED_OPTION:-0}_tlb${TLB_DEFENSE:-SDO}
fi

CKPT_OUT_DIR=${CKPT_PATH:-}/$CHECKPOINT_CONFIG/$BENCHMARK-1-ref-x86
OUTPUT_DIR=$OUTPUT_ROOT/spec17/$CHECKPOINT_CONFIG.MESI_Two_Level/$RUN_CONFIG/$SCHEME/$BENCHMARK/$THREAT_DIR/STT${STT}_Impl${IMP_CHANNEL}/$PRED_DIR
SCRIPT_OUT=$OUTPUT_DIR/runscript.log

if [[ "$CLEAN_OUTPUT" == "1" && -d "$OUTPUT_DIR" ]]; then
    rm -rf "$OUTPUT_DIR"
fi
mkdir -p "$OUTPUT_DIR"

export SPEC17_RUN_DIR=$RUN_DIR
export SPEC17_EXEC_PREFIX=${SPEC17_EXEC_PREFIX:-$RUN_DIR}
export SPEC17_X86_SUFFIX=${SPEC17_X86_SUFFIX:-_r_base.sparespec-m64}

{
    echo "Command line: $0 $*"
    echo "GEM5_PATH: $GEM5_PATH"
    echo "GEM5_BIN: $GEM5_BIN"
    echo "SPEC_PATH: $SPEC_PATH"
    echo "BENCHSPEC_DIR: $BENCHSPEC_DIR"
    echo "RUN_DIR: $RUN_DIR"
    echo "OUTPUT_DIR: $OUTPUT_DIR"
    echo "CKPT_OUT_DIR: $CKPT_OUT_DIR"
    echo "USE_CHECKPOINT: ${USE_CHECKPOINT:-1}"
    echo "BENCHMARK: $BENCHMARK"
    echo "SCHEME: $SCHEME"
    echo "THREAT_MODEL: $THREAT_DIR"
    echo "STT: $STT"
    echo "impChannel: $IMP_CHANNEL"
    echo "MAX_INSTS: $MAX_INSTS"
} | tee "$SCRIPT_OUT"

GEM5_CMD=("$GEM5_BIN")
if [[ -n "${GEM5_DEBUG_FLAGS:-}" ]]; then
    GEM5_CMD+=("--debug-flags=$GEM5_DEBUG_FLAGS")
fi

SIM_OPTS=(
    "--benchmark=$BENCHMARK"
    "--benchmark_stdout=$OUTPUT_DIR/$BENCHMARK.out"
    "--benchmark_stderr=$OUTPUT_DIR/$BENCHMARK.err"
    "--num-cpus=$NUM_CPUS"
    "--mem-size=$MEM_SIZE"
    "--num-l2caches=$NUM_L2CACHES"
    "--l1d_assoc=${L1D_ASSOC:-8}"
    "--l2_assoc=${L2_ASSOC:-16}"
    "--l1i_assoc=${L1I_ASSOC:-4}"
    "--cpu-type=DerivO3CPU"
    "--num-dirs=$NUM_DIRS"
    "--ruby"
    "--maxinsts=$MAX_INSTS"
    "--network=${NETWORK:-simple}"
    "--topology=${TOPOLOGY:-Mesh_XY}"
    "--mesh-rows=$MESH_ROWS"
    "--MSHR_size=$MSHR_SIZE"
)

while IFS= read -r opt; do
    SIM_OPTS+=("$opt")
done < <(emit_checkpoint_args "$CKPT_OUT_DIR")

while IFS= read -r opt; do
    SIM_OPTS+=("$opt")
done < <(emit_sdo_scheme_args "$SCHEME" "$STT" "$IMP_CHANNEL" "$THREAT_MODEL")

cd "$RUN_DIR"
run_or_print "${GEM5_CMD[@]}" --outdir="$OUTPUT_DIR" "$GEM5_PATH/configs/example/spec17_config.py" "${SIM_OPTS[@]}" 2>&1 | tee -a "$SCRIPT_OUT"
