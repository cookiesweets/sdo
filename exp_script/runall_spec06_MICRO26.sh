#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/env_MICRO26.sh"
source "$SCRIPT_DIR/common_MICRO26.sh"

MAX_JOBS=${MAX_JOBS:-4}
BENCHMARKS=${BENCHMARKS:-$(spec06_plotted_benchmarks)}
SCHEMES=${SCHEMES:-"UnsafeBaseline DelayExecute SDO"}
THREAT_MODELS=${THREAT_MODELS:-"Spectre Futuristic"}
STT_VALUES=${STT_VALUES:-"0 1"}
IMP_CHANNEL_VALUES=${IMP_CHANNEL_VALUES:-"0 1"}
FAIL_LOG=${FAIL_LOG:-$OUTPUT_ROOT/spec06_MICRO26_failures.log}

mkdir -p "$(dirname "$FAIL_LOG")"
: > "$FAIL_LOG"

for bench in $BENCHMARKS; do
    validate_plotted_spec06 "$bench"
done

throttle() {
    while [[ "$(jobs -pr | wc -l | tr -d ' ')" -ge "$MAX_JOBS" ]]; do
        sleep 2
    done
}

launch_one() {
    local bench=$1
    local scheme=$2
    local stt=$3
    local imp=$4
    local threat=$5

    (
        "$SCRIPT_DIR/spec06_MICRO26.sh" "$bench" "$scheme" "$stt" "$imp" "$threat" ||
        echo "FAILED spec06 bench=$bench scheme=$scheme stt=$stt imp=$imp threat=$threat" >> "$FAIL_LOG"
    ) &
}

echo "Starting SPEC2006 MICRO26 SDO runs with MAX_JOBS=$MAX_JOBS"

for bench in $BENCHMARKS; do
    for scheme in $SCHEMES; do
        if [[ "$scheme" == "UnsafeBaseline" ]]; then
            throttle
            launch_one "$bench" "$scheme" 0 0 Spectre
            continue
        fi
        for threat in $THREAT_MODELS; do
            for stt in $STT_VALUES; do
                for imp in $IMP_CHANNEL_VALUES; do
                    if [[ "$stt" == "0" && "$imp" == "1" ]]; then
                        continue
                    fi
                    throttle
                    launch_one "$bench" "$scheme" "$stt" "$imp" "$threat"
                done
            done
        done
    done
done

wait

if [[ -s "$FAIL_LOG" ]]; then
    echo "Some SPEC2006 runs failed:"
    cat "$FAIL_LOG"
    exit 1
fi

echo "All SPEC2006 MICRO26 SDO runs completed."
