#!/bin/bash

BENCHMARKS=(perlbench bzip2 gcc bwaves gamess mcf milc zeusmp gromacs cactusADM leslie3d namd gobmk dealII soplex povray calculix hmmer sjeng GemsFDTD libquantum h264ref tonto lbm omnetpp astar wrf sphinx3 xalancbmk specrand_i specrand_f)
STT_VALUES=(1)
IMPLICIT_CHANNEL_VALUES=(0 1)
THREAT_MODELS=(Spectre Futuristic)

MAX_JOBS=$1
if [ -z "MAX_JOBS" ]; then
    MAX_JOBS=16
fi

run_benchmark() {
    local bench=$1
    local stt=$2
    local implicit_channel=$3
    local threat_model=$4

    ./runsdo06.sh "$bench" "$stt" "$implicit_channel" "$threat_model" &
    local pid=$!
    echo "Started $bench | threat=$threat_model | STT=$stt | implicit=$implicit_channel | PID=$pid"
    wait $pid
    if [ $? -ne 0 ]; then
        echo "Error: $bench | threat=$threat_model | STT=$stt | implicit=$implicit_channel"
    fi
}

echo "Starting all benchmarks across THREAT_MODELS x STT x implicit_channel (max $MAX_JOBS jobs in parallel)."

running_jobs=0
task_queue=()

# Populate task queue
for bench in "${BENCHMARKS[@]}"; do
  for threat in "${THREAT_MODELS[@]}"; do
    for stt in "${STT_VALUES[@]}"; do
      for implicit in "${IMPLICIT_CHANNEL_VALUES[@]}"; do
        task_queue+=("$bench $stt $implicit $threat")
      done
    done
  done
done

# Launch with job control
for task in "${task_queue[@]}"; do
    while [ "$running_jobs" -ge "$MAX_JOBS" ]; do
        wait -n
        ((running_jobs--))
    done

    IFS=' ' read -r bench stt implicit threat <<< "$task"
    run_benchmark "$bench" "$stt" "$implicit" "$threat" &
    ((running_jobs++))
done

wait
echo "All benchmark runs completed."