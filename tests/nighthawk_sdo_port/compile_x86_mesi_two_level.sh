#!/usr/bin/env bash
#
# Compile-only provenance gate for the candidate Two-Level SDO port.
# This script deliberately accepts no workload or checkpoint arguments.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd -P)
SOURCE_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd -P)

usage() {
    cat <<'EOF'
Usage:
  compile_x86_mesi_two_level.sh --build-root NEW_ABSOLUTE_DIR \
    --run-dir NEW_ABSOLUTE_DIR [OPTIONS]

Required:
  --build-root DIR   New, canonical SCons root whose basename is "build".
  --run-dir DIR      New, absolute directory for the compile manifest/log.

Options:
  --scons COMMAND    SCons executable (default: $SCONS or scons).
  --jobs N           Compile jobs (default: $SCONS_JOBS or 16; maximum 32).
  --allow-dirty      Permit and record a dirty source tree.
  -h, --help

The only build target is:
  BUILD_ROOT/X86_MESI_Two_Level/gem5.opt

Run this script through the baseline-host resource guard. It never launches a
workload, accepts no checkpoint argument, and refuses existing, aliased,
overlapping, or source-tree build/run paths.
EOF
}

die() {
    printf 'compile_x86_mesi_two_level: %s\n' "$*" >&2
    exit 2
}

sha256_file() {
    local path=$1
    if [[ "$SHA256_TOOL" == sha256sum ]]; then
        sha256sum "$path" | awk '{print $1}'
    else
        shasum -a 256 "$path" | awk '{print $1}'
    fi
}

is_uint() {
    case ${1:-} in
        ''|*[!0-9]*) return 1 ;;
        *) return 0 ;;
    esac
}

normalize_absolute_path() {
    local input=$1
    local component
    local normalized=
    local index=0
    local -a input_components
    local -a output_components

    IFS=/ read -r -a input_components <<<"$input"
    for component in "${input_components[@]}"; do
        case $component in
            ''|.)
                ;;
            ..)
                if (( index > 0 )); then
                    index=$((index - 1))
                    unset 'output_components[index]'
                fi
                ;;
            *)
                output_components[index]=$component
                index=$((index + 1))
                ;;
        esac
    done

    for ((index = 0; index < ${#output_components[@]}; index++)); do
        normalized=$normalized/${output_components[index]}
    done
    printf '%s\n' "${normalized:-/}"
}

# Resolve every existing ancestor with pwd -P, while retaining a normalized
# suffix that does not exist yet. This provides realpath -m semantics without
# depending on GNU-only realpath options.
canonicalize_missing_path() {
    local requested=$1
    local normalized
    local probe
    local suffix=
    local component
    local resolved

    normalized=$(normalize_absolute_path "$requested") || return 1
    probe=$normalized
    while [[ ! -e "$probe" ]]; do
        # A dangling symlink is not a new path and must not be followed.
        [[ ! -L "$probe" ]] || return 1
        [[ "$probe" != / ]] || return 1
        component=${probe##*/}
        suffix=/$component$suffix
        probe=${probe%/*}
        [[ -n "$probe" ]] || probe=/
    done
    [[ -d "$probe" ]] || return 1
    resolved=$(cd "$probe" && pwd -P) || return 1
    if [[ "$resolved" == / ]]; then
        printf '/%s\n' "${suffix#/}"
    else
        printf '%s%s\n' "$resolved" "$suffix"
    fi
}

shell_join() {
    local arg
    local output=
    for arg in "$@"; do
        printf -v arg '%q' "$arg"
        output="${output}${output:+ }${arg}"
    done
    printf '%s\n' "$output"
}

BUILD_ROOT=
RUN_DIR=
SCONS_COMMAND=${SCONS:-scons}
JOBS=${SCONS_JOBS:-16}
ALLOW_DIRTY=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --build-root)
            [[ $# -ge 2 ]] || die "--build-root requires a value"
            BUILD_ROOT=$2
            shift 2
            ;;
        --run-dir)
            [[ $# -ge 2 ]] || die "--run-dir requires a value"
            RUN_DIR=$2
            shift 2
            ;;
        --scons)
            [[ $# -ge 2 ]] || die "--scons requires a value"
            SCONS_COMMAND=$2
            shift 2
            ;;
        --jobs)
            [[ $# -ge 2 ]] || die "--jobs requires a value"
            JOBS=$2
            shift 2
            ;;
        --allow-dirty)
            ALLOW_DIRTY=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "unknown option: $1"
            ;;
    esac
done

[[ -n "$BUILD_ROOT" ]] || die "--build-root is required"
[[ -n "$RUN_DIR" ]] || die "--run-dir is required"
[[ "$BUILD_ROOT" == /* ]] || die "--build-root must be absolute"
[[ "$RUN_DIR" == /* ]] || die "--run-dir must be absolute"
case $BUILD_ROOT$RUN_DIR in
    *$'\n'*|*$'\r'*) die "build/run paths cannot contain newlines" ;;
esac
BUILD_ROOT=$(canonicalize_missing_path "$BUILD_ROOT") ||
    die "cannot canonicalize --build-root safely"
RUN_DIR=$(canonicalize_missing_path "$RUN_DIR") ||
    die "cannot canonicalize --run-dir safely"
[[ ! -e "$BUILD_ROOT" ]] || die "build root already exists: $BUILD_ROOT"
[[ ! -e "$RUN_DIR" ]] || die "run directory already exists: $RUN_DIR"
[[ "${BUILD_ROOT##*/}" == build ]] ||
    die "--build-root must end in /build for this SConstruct"
case "$BUILD_ROOT/" in
    "$SOURCE_ROOT/"*) die "build root cannot be in source tree" ;;
esac
case "$RUN_DIR/" in
    "$SOURCE_ROOT/"*) die "run directory cannot be in source tree" ;;
esac
[[ "$BUILD_ROOT" != "$RUN_DIR" ]] || die "build root and run directory must differ"
case "$RUN_DIR/" in
    "$BUILD_ROOT/"*) die "run directory cannot be inside build root" ;;
esac
case "$BUILD_ROOT/" in
    "$RUN_DIR/"*) die "build root cannot be inside run directory" ;;
esac
is_uint "$JOBS" || die "--jobs must be an integer"
(( JOBS >= 1 && JOBS <= 32 )) || die "--jobs must be between 1 and 32"

if command -v sha256sum >/dev/null 2>&1; then
    SHA256_TOOL=sha256sum
elif command -v shasum >/dev/null 2>&1; then
    SHA256_TOOL=shasum
else
    die "sha256sum or shasum is required"
fi

git -C "$SOURCE_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
    die "source root is not a git worktree"
SOURCE_COMMIT=$(git -C "$SOURCE_ROOT" rev-parse HEAD)
SOURCE_BRANCH=$(git -C "$SOURCE_ROOT" symbolic-ref --quiet --short HEAD ||
    printf 'DETACHED')
if [[ -n "$(git -C "$SOURCE_ROOT" status --porcelain)" ]]; then
    SOURCE_DIRTY=true
else
    SOURCE_DIRTY=false
fi
if [[ "$SOURCE_DIRTY" == true && "$ALLOW_DIRTY" -ne 1 ]]; then
    die "source tree is dirty; commit it or pass --allow-dirty explicitly"
fi

if [[ "$SCONS_COMMAND" == */* ]]; then
    [[ -x "$SCONS_COMMAND" ]] || die "SCons executable is not runnable"
    SCONS_EXE=$SCONS_COMMAND
else
    SCONS_EXE=$(command -v "$SCONS_COMMAND" 2>/dev/null || true)
    [[ -n "$SCONS_EXE" ]] || die "SCons executable not found: $SCONS_COMMAND"
fi

TARGET=$BUILD_ROOT/X86_MESI_Two_Level/gem5.opt
COMMAND=("$SCONS_EXE" -j "$JOBS" "$TARGET")
COMMAND_SHELL=$(shell_join "${COMMAND[@]}")
START_UTC=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
MEM_AVAILABLE_KIB=UNAVAILABLE
if [[ -r /proc/meminfo ]]; then
    MEM_AVAILABLE_KIB=$(awk '/^MemAvailable:/ {print $2; exit}' /proc/meminfo)
    [[ -n "$MEM_AVAILABLE_KIB" ]] || MEM_AVAILABLE_KIB=UNAVAILABLE
fi

mkdir -p "$(dirname "$BUILD_ROOT")" "$(dirname "$RUN_DIR")"
mkdir "$BUILD_ROOT"
mkdir "$RUN_DIR"

git -C "$SOURCE_ROOT" status --porcelain=v1 >"$RUN_DIR/git_status.txt"
git -C "$SOURCE_ROOT" submodule status --recursive \
    >"$RUN_DIR/submodules.txt" 2>&1 || true

{
    printf 'schema_version=1\n'
    printf 'phase=compile_only\n'
    printf 'protocol=X86_MESI_Two_Level\n'
    printf 'source_root=%s\n' "$SOURCE_ROOT"
    printf 'source_commit=%s\n' "$SOURCE_COMMIT"
    printf 'source_branch=%s\n' "$SOURCE_BRANCH"
    printf 'source_dirty=%s\n' "$SOURCE_DIRTY"
    printf 'build_root=%s\n' "$BUILD_ROOT"
    printf 'binary_path=%s\n' "$TARGET"
    printf 'run_dir=%s\n' "$RUN_DIR"
    printf 'jobs=%s\n' "$JOBS"
    printf 'scons_executable=%s\n' "$SCONS_EXE"
    printf 'command_shell=%s\n' "$COMMAND_SHELL"
    printf 'hostname=%s\n' "$(hostname)"
    printf 'kernel=%s\n' "$(uname -srmo)"
    printf 'mem_available_before_kib=%s\n' "$MEM_AVAILABLE_KIB"
    printf 'start_utc=%s\n' "$START_UTC"
} >"$RUN_DIR/manifest.env"

{
    "$SCONS_EXE" --version 2>&1 || true
    printf '\nCC=%s\n' "${CC:-cc}"
    "${CC:-cc}" --version 2>&1 | head -n 1 || true
    printf 'CXX=%s\n' "${CXX:-c++}"
    "${CXX:-c++}" --version 2>&1 | head -n 1 || true
    python --version 2>&1 || true
} >"$RUN_DIR/toolchain.txt"
printf '%s\n' "$COMMAND_SHELL" >"$RUN_DIR/command.txt"

printf 'source_commit=%s\n' "$SOURCE_COMMIT"
printf 'source_dirty=%s\n' "$SOURCE_DIRTY"
printf 'mem_available_before_kib=%s\n' "$MEM_AVAILABLE_KIB"
printf 'binary_target=%s\n' "$TARGET"
printf 'command_shell=%s\n' "$COMMAND_SHELL"

set +e
(
    cd "$SOURCE_ROOT"
    "${COMMAND[@]}"
) >"$RUN_DIR/compile.log" 2>&1
EXIT_STATUS=$?
set -e

FINAL_STATUS=FAIL
BINARY_SHA256=UNAVAILABLE
if [[ "$EXIT_STATUS" -eq 0 ]]; then
    if [[ -f "$TARGET" ]]; then
        BINARY_SHA256=$(sha256_file "$TARGET")
        FINAL_STATUS=PASS
    else
        EXIT_STATUS=3
        printf '%s\n' \
            "SCons exited zero but did not create the expected binary: $TARGET" \
            >>"$RUN_DIR/compile.log"
    fi
fi
END_UTC=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

{
    printf 'end_utc=%s\n' "$END_UTC"
    printf 'exit_status=%s\n' "$EXIT_STATUS"
    printf 'final_status=%s\n' "$FINAL_STATUS"
    printf 'binary_sha256=%s\n' "$BINARY_SHA256"
} >>"$RUN_DIR/manifest.env"

printf 'final_status=%s\n' "$FINAL_STATUS"
printf 'manifest=%s\n' "$RUN_DIR/manifest.env"
printf 'binary=%s\n' "$TARGET"
exit "$EXIT_STATUS"
