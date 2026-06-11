#!/usr/bin/env bash

# Source this file before running the MICRO26 SDO experiment scripts, or let the
# scripts source it automatically for these defaults.

if [ -f /root/LOCAL_LIB/env_gcc_binutils.sh ]; then
    source /root/LOCAL_LIB/env_gcc_binutils.sh
fi
if [ -f /root/LOCAL_LIB/protobuf/env_protobuf.sh ]; then
    source /root/LOCAL_LIB/protobuf/env_protobuf.sh
fi
if [ -f /root/LOCAL_LIB/gperftools/env_gperftools.sh ]; then
    source /root/LOCAL_LIB/gperftools/env_gperftools.sh
fi
if [ -f /root/LOCAL_LIB/python/env_anaconda2.sh ]; then
    source /root/LOCAL_LIB/python/env_anaconda2.sh
fi

# Keep GEM5_PATH pointed at this SDO repository. If a sparespec-stt shell
# environment is already sourced, set SDO_GEM5_PATH or fall back to /root/sdo.
# The SPEC and checkpoint path variable names/defaults below follow
# sparespec-stt/exp_script/env.sh.
if [ -n "${SDO_GEM5_PATH:-}" ]; then
    export GEM5_PATH=$SDO_GEM5_PATH
elif [ -z "${GEM5_PATH:-}" ] || [ "$(basename "$GEM5_PATH")" = "sparespec-stt" ]; then
    export GEM5_PATH=/root/sdo
fi
export GEM5_BIN=${GEM5_BIN:-$GEM5_PATH/build/X86_MESI_Two_Level/gem5.opt}
export SPEC_PATH=${SPEC_PATH:-/root/Benchmark/SPEC2017}
export SPEC06_PATH=${SPEC06_PATH:-/root/Benchmark/SPEC2006}
export GAP_PATH=${GAP_PATH:-/root/Benchmark/gapbs}
export CKPT_PATH=${CKPT_PATH:-/root/Benchmark/spare_ckpt}
export CKPT_PATH_MESI=${CKPT_PATH_MESI:-/root/Benchmark/spare_ckpt}
export CKPT_PATH_MOESI=${CKPT_PATH_MOESI:-/root/Benchmark/spare_ckpt_moesi}
export CKPT_PATH_GAP=${CKPT_PATH_GAP:-/root/Benchmark/gap_ckpt}
export OUTPUT_ROOT=${OUTPUT_ROOT:-$GEM5_PATH/output/MICRO26}

export SPEC06_X86_SUFFIX=${SPEC06_X86_SUFFIX:-_base.Xeon-gcc4.3}
export SPEC17_X86_SUFFIX=${SPEC17_X86_SUFFIX:-_r_base.sparespec-m64}
export SPEC06_RUN_DIR_NAME=${SPEC06_RUN_DIR_NAME:-run_base_ref_Xeon-gcc4.3.0000}
export SPEC17_RUN_DIR_NAME=${SPEC17_RUN_DIR_NAME:-run_base_refrate_sparespec-m64.0000}
