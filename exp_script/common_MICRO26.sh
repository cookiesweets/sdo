#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "common_MICRO26.sh must be sourced by an experiment script" >&2
    exit 1
fi

die() {
    echo "error: $*" >&2
    exit 1
}

require_var() {
    local name=$1
    if [[ -z "${!name:-}" ]]; then
        die "$name is unset"
    fi
}

validate_bool() {
    local name=$1
    local value=$2
    case "$value" in
        0|1) ;;
        *) die "$name must be 0 or 1, got '$value'" ;;
    esac
}

validate_scheme() {
    case "$1" in
        UnsafeBaseline|DelayExecute|SDO) ;;
        *) die "scheme must be UnsafeBaseline, DelayExecute, or SDO, got '$1'" ;;
    esac
}

validate_threat() {
    case "$1" in
        Spectre|Futuristic) ;;
        *) die "threat_model must be Spectre or Futuristic, got '$1'" ;;
    esac
}

spec06_plotted_benchmarks() {
    echo "perlbench bzip2 gcc mcf milc namd gobmk povray libquantum h264ref omnetpp astar sphinx3"
}

spec17_plotted_benchmarks() {
    echo "cactuBSSN namd parest povray lbm x264 imagick leela nab xz"
}

is_word_in_list() {
    local needle=$1
    shift
    local item
    for item in "$@"; do
        if [[ "$item" == "$needle" ]]; then
            return 0
        fi
    done
    return 1
}

validate_plotted_spec06() {
    local benchmark=$1
    # shellcheck disable=SC2046
    if ! is_word_in_list "$benchmark" $(spec06_plotted_benchmarks); then
        die "SPEC2006 benchmark '$benchmark' is outside the plotted MICRO26 set"
    fi
}

validate_plotted_spec17() {
    local benchmark=$1
    # shellcheck disable=SC2046
    if ! is_word_in_list "$benchmark" $(spec17_plotted_benchmarks); then
        die "SPEC2017 benchmark '$benchmark' is outside the plotted MICRO26 set"
    fi
}

spec06_code() {
    case "$1" in
        perlbench) echo 400.perlbench ;;
        bzip2) echo 401.bzip2 ;;
        gcc) echo 403.gcc ;;
        bwaves) echo 410.bwaves ;;
        gamess) echo 416.gamess ;;
        mcf) echo 429.mcf ;;
        milc) echo 433.milc ;;
        zeusmp) echo 434.zeusmp ;;
        gromacs) echo 435.gromacs ;;
        cactusADM) echo 436.cactusADM ;;
        leslie3d) echo 437.leslie3d ;;
        namd) echo 444.namd ;;
        gobmk) echo 445.gobmk ;;
        dealII) echo 447.dealII ;;
        soplex) echo 450.soplex ;;
        povray) echo 453.povray ;;
        calculix) echo 454.calculix ;;
        hmmer) echo 456.hmmer ;;
        sjeng) echo 458.sjeng ;;
        GemsFDTD) echo 459.GemsFDTD ;;
        libquantum) echo 462.libquantum ;;
        h264ref) echo 464.h264ref ;;
        tonto) echo 465.tonto ;;
        lbm) echo 470.lbm ;;
        omnetpp) echo 471.omnetpp ;;
        astar) echo 473.astar ;;
        wrf) echo 481.wrf ;;
        sphinx3) echo 482.sphinx3 ;;
        xalancbmk) echo 483.xalancbmk ;;
        specrand_i) echo 998.specrand ;;
        specrand_f) echo 999.specrand ;;
        *) return 1 ;;
    esac
}

spec17_code() {
    case "$1" in
        perlbench) echo 500.perlbench_r ;;
        gcc) echo 502.gcc_r ;;
        bwaves) echo 503.bwaves_r ;;
        mcf) echo 505.mcf_r ;;
        cactuBSSN) echo 507.cactuBSSN_r ;;
        namd) echo 508.namd_r ;;
        parest) echo 510.parest_r ;;
        povray) echo 511.povray_r ;;
        lbm) echo 519.lbm_r ;;
        omnetpp) echo 520.omnetpp_r ;;
        wrf) echo 521.wrf_r ;;
        xalancbmk) echo 523.xalancbmk_r ;;
        x264) echo 525.x264_r ;;
        blender) echo 526.blender_r ;;
        cam4) echo 527.cam4_r ;;
        deepsjeng) echo 531.deepsjeng_r ;;
        imagick) echo 538.imagick_r ;;
        leela) echo 541.leela_r ;;
        nab) echo 544.nab_r ;;
        fotonik3d) echo 549.fotonik3d_r ;;
        roms) echo 554.roms_r ;;
        xz) echo 557.xz_r ;;
        *) return 1 ;;
    esac
}

resolve_spec06_benchspec() {
    local candidate
    for candidate in \
        "${SPEC06_BENCHSPEC_DIR:-}" \
        "${SPEC06_PATH:-}/benchmarks/SPECCPU_2006/benchspec/CPU2006" \
        "${SPEC06_PATH:-}/benchspec/CPU2006"
    do
        if [[ -n "$candidate" && -d "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done
    die "SPEC2006 benchspec directory not found; set SPEC06_BENCHSPEC_DIR or SPEC06_PATH"
}

resolve_spec17_benchspec() {
    local candidate
    for candidate in \
        "${SPEC17_BENCHSPEC_DIR:-}" \
        "${SPEC_PATH:-}/benchspec/CPU"
    do
        if [[ -n "$candidate" && -d "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done
    die "SPEC2017 benchspec directory not found; set SPEC17_BENCHSPEC_DIR or SPEC_PATH"
}

emit_checkpoint_args() {
    local ckpt_dir=$1
    if [[ "${USE_CHECKPOINT:-1}" == "1" ]]; then
        require_var CKPT_PATH
        echo "--checkpoint-dir=$ckpt_dir"
        echo "--checkpoint-restore=${INST_TAKE_CHECKPOINT:-10000000000}"
        echo "--at-instruction"
    fi
}

emit_sdo_scheme_args() {
    local scheme=$1
    local stt=$2
    local imp_channel=$3
    local threat_model=$4

    echo "--scheme=$scheme"
    echo "--mem_model=${MEM_MODEL:-TSO}"
    echo "--STT=$stt"
    echo "--impChannel=$imp_channel"
    echo "--ifPrintROB=${IF_PRINT_ROB:-0}"
    echo "--moreTransTypes=${MORE_TRANS_TYPES:-0}"
    echo "--ruby_enable_resource_stall=${RUBY_ENABLE_RESOURCE_STALL:-1}"

    if [[ "$scheme" != "UnsafeBaseline" ]]; then
        echo "--threat_model=$threat_model"
    fi

    if [[ "$scheme" == "SDO" ]]; then
        echo "--pred_type=${PRED_TYPE:-tournament_2way}"
        echo "--subpred1_type=${SUBPRED1_TYPE:-greedy}"
        echo "--subpred2_type=${SUBPRED2_TYPE:-loop}"
        if [[ -n "${SUBPRED3_TYPE:-}" ]]; then
            echo "--subpred3_type=$SUBPRED3_TYPE"
        fi
        echo "--pred_option=${PRED_OPTION:-0}"
        echo "--TLB_defense=${TLB_DEFENSE:-SDO}"
        echo "--expose_only=${EXPOSE_ONLY:-0}"
        echo "--disable_2ndld=${DISABLE_2NDLD:-0}"
        echo "--enable_OblS_contention=${ENABLE_OBLS_CONTENTION:-0}"
    else
        echo "--TLB_defense=No"
    fi
}

run_or_print() {
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        printf '%q ' "$@"
        printf '\n'
    else
        "$@"
    fi
}
