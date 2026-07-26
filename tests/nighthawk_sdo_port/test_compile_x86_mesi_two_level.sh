#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd -P)
SOURCE_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd -P)
DRIVER=$SCRIPT_DIR/compile_x86_mesi_two_level.sh
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/sdo-compile-gate-test.XXXXXX")
TMP_ROOT=$(cd "$TMP_ROOT" && pwd -P)

cleanup() {
    rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
    printf 'test_compile_x86_mesi_two_level: %s\n' "$*" >&2
    exit 1
}

expect_fail() {
    local name=$1
    local expected=$2
    local output
    local status
    shift 2

    set +e
    output=$("$DRIVER" "$@" --allow-dirty 2>&1)
    status=$?
    set -e
    [[ "$status" -ne 0 ]] || fail "$name unexpectedly passed"
    case $output in
        *"$expected"*) ;;
        *) fail "$name did not report '$expected': $output" ;;
    esac
}

mkdir "$TMP_ROOT/real"
ln -s "$SOURCE_ROOT" "$TMP_ROOT/source-alias"
ln -s "$TMP_ROOT/real" "$TMP_ROOT/real-alias"

expect_fail "non-build basename" "must end in /build" \
    --build-root "$TMP_ROOT/wrong-root" \
    --run-dir "$TMP_ROOT/run-wrong-root"

expect_fail "source descendant build" "build root cannot be in source tree" \
    --build-root "$SOURCE_ROOT/.sdo-test-do-not-create/build" \
    --run-dir "$TMP_ROOT/run-source-build"

expect_fail "source descendant run" "run directory cannot be in source tree" \
    --build-root "$TMP_ROOT/source-run/build" \
    --run-dir "$SOURCE_ROOT/.sdo-test-do-not-create/run"

expect_fail "source symlink alias" "build root cannot be in source tree" \
    --build-root "$TMP_ROOT/source-alias/.sdo-test-do-not-create/build" \
    --run-dir "$TMP_ROOT/run-source-alias"

expect_fail "dot-dot overlap" "build root cannot be inside run directory" \
    --build-root "$TMP_ROOT/real/job/../job/build" \
    --run-dir "$TMP_ROOT/real/job"

expect_fail "symlink overlap" "build root cannot be inside run directory" \
    --build-root "$TMP_ROOT/real/alias-job/build" \
    --run-dir "$TMP_ROOT/real-alias/alias-job"

FAKE_SCONS=$TMP_ROOT/fake-scons
cat >"$FAKE_SCONS" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == --version ]]; then
    printf 'fake-scons 1\n'
    exit 0
fi
target=${!#}
case $target in
    */build/X86_MESI_Two_Level/gem5.opt) ;;
    *) printf 'unexpected target: %s\n' "$target" >&2; exit 9 ;;
esac
mkdir -p "$(dirname "$target")"
printf 'fake gem5.opt\n' >"$target"
EOF
chmod +x "$FAKE_SCONS"

VALID_BUILD_ROOT=$TMP_ROOT/valid-job/build
VALID_RUN_DIR=$TMP_ROOT/valid-run
"$DRIVER" \
    --build-root "$VALID_BUILD_ROOT" \
    --run-dir "$VALID_RUN_DIR" \
    --scons "$FAKE_SCONS" \
    --jobs 1 \
    --allow-dirty

[[ -f "$VALID_BUILD_ROOT/X86_MESI_Two_Level/gem5.opt" ]] ||
    fail "valid gate did not create the expected target"
grep -q '^final_status=PASS$' "$VALID_RUN_DIR/manifest.env" ||
    fail "valid gate did not record PASS"
grep -q "^build_root=$VALID_BUILD_ROOT$" "$VALID_RUN_DIR/manifest.env" ||
    fail "valid gate did not record the canonical build root"

printf 'test_compile_x86_mesi_two_level: PASS\n'
