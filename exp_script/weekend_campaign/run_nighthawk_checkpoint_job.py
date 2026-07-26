#!/usr/bin/env python

"""Run one parity-bound SDO checkpoint job from the canonical manifest.

The path and outer CLI intentionally match the HPCA27 Nighthawk campaign
runner contract.  The inner command selects SDO and the explicit
sparespec-stt non-mechanism parity profile.  This is preparation for the
artifact-bound parity gate; it does not by itself prove an exact SDO port.
"""

from __future__ import print_function

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys


MODE_OPTIONS = {
    "sdo-implicit": ("SDO", 1, 1),
}

HPCA27_MAX_INSTS = 500000000
HPCA27_FINAL_EVIDENCE_CLASS = "final-performance"
HPCA27_SANITY_EVIDENCE_CLASS = "sanity-slice-not-final-performance"
HPCA27_SANITY_MAX_INSTS = (10000000, 25000000)


def utc_now():
    if hasattr(datetime, "timezone"):
        return datetime.datetime.now(datetime.timezone.utc).replace(
            microsecond=0
        ).isoformat().replace("+00:00", "Z")
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def canonical_path(path, label, expected_kind=None):
    """Require an absolute, lexical and physical non-symlink path."""

    if not os.path.isabs(path):
        raise ValueError(label + " must be absolute: " + path)
    absolute = os.path.abspath(path)
    if path != absolute:
        raise ValueError(
            label + " must use its canonical lexical path: " + path
        )
    if os.path.islink(path) or os.path.realpath(path) != absolute:
        raise ValueError(
            label + " must use a canonical non-symlink path: " + path
        )
    if expected_kind == "file" and not os.path.isfile(path):
        raise ValueError("missing " + label + ": " + path)
    if expected_kind == "directory" and not os.path.isdir(path):
        raise ValueError("missing " + label + ": " + path)
    if expected_kind == "optional-directory" and os.path.exists(path) and \
            not os.path.isdir(path):
        raise ValueError(label + " is not a directory: " + path)
    return absolute


def stable_sha256(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def git_value(repo_root, arguments):
    process = subprocess.Popen(
        ["git"] + list(arguments),
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(stderr.decode("utf-8", "replace"))
    return stdout.decode("utf-8", "replace").strip()


def load_row(manifest_path, row_id):
    with open(manifest_path, "r") as handle:
        document = json.load(handle)
    matches = [
        row for row in document.get("workloads", [])
        if row.get("row_id") == row_id
    ]
    if len(matches) != 1:
        raise ValueError(
            "manifest row count for {} is {}".format(row_id, len(matches))
        )
    row = matches[0]
    if not row.get("valid"):
        raise ValueError(
            "manifest row is invalid: "
            + ";".join(row.get("validation_errors", []))
        )
    return document, row


def write_json(path, value):
    with open(path, "w") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--binary", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--row-id", required=True)
    parser.add_argument("--mode", choices=sorted(MODE_OPTIONS), required=True)
    parser.add_argument("--threat", choices=("Futuristic",), required=True)
    parser.add_argument(
        "--capability-profile", choices=("current",), required=True
    )
    parser.add_argument(
        "--pending-policy", choices=("not_applicable",), required=True
    )
    parser.add_argument("--smshr", type=int, required=True)
    parser.add_argument("--l1d-size", required=True)
    parser.add_argument("--l1i-size", required=True)
    parser.add_argument("--l2-size", required=True)
    parser.add_argument("--l1d-assoc", type=int, required=True)
    parser.add_argument("--l1i-assoc", type=int, required=True)
    parser.add_argument("--l2-assoc", type=int, required=True)
    parser.add_argument(
        "--llc-bank-contention", type=int, choices=(0, 1), required=True
    )
    parser.add_argument(
        "--llc-fake-getspec", type=int, choices=(0, 1), required=True
    )
    parser.add_argument("--llc-data-banks", type=int, required=True)
    parser.add_argument("--llc-tag-banks", type=int, required=True)
    parser.add_argument("--llc-data-latency", type=int, required=True)
    parser.add_argument("--llc-tag-latency", type=int, required=True)
    parser.add_argument(
        "--llc-data-issue-interval", type=int, required=True
    )
    parser.add_argument(
        "--llc-tag-issue-interval", type=int, required=True
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-insts", type=int, required=True)
    parser.add_argument(
        "--evidence-class",
        choices=(
            HPCA27_FINAL_EVIDENCE_CLASS,
            HPCA27_SANITY_EVIDENCE_CLASS,
        ),
        required=True,
    )
    parser.add_argument("--expected-source-sha", required=True)
    parser.add_argument("--expected-binary-sha256", required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--drain-at-end", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def validate_fixed_controls(args, row):
    expected = {
        "capability_profile": "current",
        "drain_at_end": False,
        "l1d_assoc": 8,
        "l1d_size": "64kB",
        "l1i_assoc": 4,
        "l1i_size": "32kB",
        "l2_assoc": 16,
        "l2_size": "2MB",
        "llc_bank_contention": 0,
        "llc_data_banks": 1,
        "llc_data_issue_interval": 0,
        "llc_data_latency": 1,
        "llc_fake_getspec": 0,
        "llc_tag_banks": 1,
        "llc_tag_issue_interval": 0,
        "llc_tag_latency": 1,
        "mode": "sdo-implicit",
        "pending_policy": "not_applicable",
        "smshr": 0,
        "threat": "Futuristic",
    }
    mismatches = []
    for name, wanted in expected.items():
        actual = getattr(args, name)
        if actual != wanted:
            mismatches.append(
                "{}={!r} (expected {!r})".format(name, actual, wanted)
            )
    if args.evidence_class == HPCA27_FINAL_EVIDENCE_CLASS:
        allowed_budgets = (HPCA27_MAX_INSTS,)
    elif args.evidence_class == HPCA27_SANITY_EVIDENCE_CLASS:
        allowed_budgets = HPCA27_SANITY_MAX_INSTS
    else:
        allowed_budgets = ()
    if args.max_insts not in allowed_budgets:
        mismatches.append(
            "max_insts={!r} (expected one of {!r} for {!r})".format(
                args.max_insts, allowed_budgets, args.evidence_class
            )
        )
    row_budget = int(row["post_restore_instruction_budget"])
    if row_budget != HPCA27_MAX_INSTS:
        mismatches.append(
            "post_restore_instruction_budget={!r} "
            "(expected canonical final-performance budget {!r})".format(
                row_budget, HPCA27_MAX_INSTS
            )
        )
    if args.evidence_class == HPCA27_SANITY_EVIDENCE_CLASS and \
            args.max_insts >= row_budget:
        mismatches.append(
            "sanity max_insts={!r} must be smaller than canonical "
            "budget {!r}".format(args.max_insts, row_budget)
        )
    if mismatches:
        raise ValueError(
            "HPCA27 outer-runner parity mismatch: "
            + ", ".join(sorted(mismatches))
        )


def validate_source_identity(source_root, expected_sha):
    source_sha = git_value(source_root, ["rev-parse", "HEAD"])
    if source_sha != expected_sha:
        raise ValueError(
            "source SHA mismatch: expected {} found {}".format(
                expected_sha, source_sha
            )
        )
    status = git_value(
        source_root, ["status", "--porcelain", "--untracked-files=all"]
    )
    if status:
        raise ValueError("source tree is not pristine")
    ignored = git_value(
        source_root,
        ["ls-files", "--others", "--ignored", "--exclude-standard"],
    )
    if ignored:
        raise ValueError("source tree contains ignored files")
    return source_sha


def build_command(args, binary, config, output_dir, row):
    """Build the exact inner command recorded in execution_identity.json."""

    command = [
        "/usr/bin/time",
        "-v",
        "-o",
        os.path.join(output_dir, "resource.time"),
        binary,
        "--outdir=" + output_dir,
        config,
        "--benchmark=" + row["display_name"],
        "--benchmark_stdout=" + os.path.join(
            output_dir, row["display_name"] + ".out"
        ),
        "--benchmark_stderr=" + os.path.join(
            output_dir, row["display_name"] + ".err"
        ),
        "--num-cpus=1",
        "--mem-size=8GB",
        "--mem-type=DDR3_1600_8x8",
        "--mem-channels=1",
        "--checkpoint-dir=" + row["checkpoint_directory"],
        "--checkpoint-restore=" + str(row["checkpoint_restore"]),
        "--at-instruction",
        "--l1d_size=" + args.l1d_size,
        "--l1i_size=" + args.l1i_size,
        "--l2_size=" + args.l2_size,
        "--l1d_assoc=" + str(args.l1d_assoc),
        "--l1i_assoc=" + str(args.l1i_assoc),
        "--l2_assoc=" + str(args.l2_assoc),
        "--cpu-type=DerivO3CPU",
        "--scheme=SDO",
        "--mem_model=RC",
        "--num-dirs=1",
        "--num-l2caches=1",
        "--ruby",
        "--ruby-clock=2GHz",
        "--ports=4",
        "--maxinsts=" + str(args.max_insts),
        "--hpca27-evidence-class=" + args.evidence_class,
        "--network=simple",
        "--topology=Mesh_XY",
        "--mesh-rows=1",
        "--MSHR_size=16",
        "--threat_model=Futuristic",
        "--STT=1",
        "--impChannel=1",
        "--ifPrintROB=0",
        "--moreTransTypes=0",
        "--ruby_enable_resource_stall=0",
        "--ruby-sequencer-hit-latency=1",
        "--llc-data-array-banks=" + str(args.llc_data_banks),
        "--llc-tag-array-banks=" + str(args.llc_tag_banks),
        "--llc-data-access-latency=" + str(args.llc_data_latency),
        "--llc-tag-access-latency=" + str(args.llc_tag_latency),
        "--llc-data-issue-interval="
        + str(args.llc_data_issue_interval),
        "--llc-tag-issue-interval="
        + str(args.llc_tag_issue_interval),
        "--pred_type=tournament_2way",
        "--subpred1_type=greedy",
        "--subpred2_type=loop",
        "--pred_option=0",
        "--TLB_defense=SDO",
        "--expose_only=0",
        "--disable_2ndld=0",
        "--enable_OblS_contention=0",
        "--hpca27-performance-parity",
    ]
    return command


def main(argv=None):
    args = parse_args(argv)
    source_root = canonical_path(
        args.source_root, "source directory", "directory"
    )
    binary = canonical_path(args.binary, "identity binary", "file")
    manifest_path = canonical_path(
        args.manifest, "canonical workload manifest", "file"
    )
    output_dir = canonical_path(
        args.output_dir, "output directory", "optional-directory"
    )

    source_sha = validate_source_identity(
        source_root, args.expected_source_sha
    )
    binary_hash = file_sha256(binary)
    if binary_hash != args.expected_binary_sha256:
        raise ValueError(
            "binary SHA-256 mismatch: expected {} found {}".format(
                args.expected_binary_sha256, binary_hash
            )
        )
    manifest_hash = file_sha256(manifest_path)
    if manifest_hash != args.expected_manifest_sha256:
        raise ValueError(
            "manifest SHA-256 mismatch: expected {} found {}".format(
                args.expected_manifest_sha256, manifest_hash
            )
        )

    document, row = load_row(manifest_path, args.row_id)
    validate_fixed_controls(args, row)

    config = os.path.join(
        source_root,
        "configs",
        "example",
        "spec{}_config.py".format(row["suite_code"]),
    )
    benchmark_config = os.path.join(source_root, row["config_source"])
    canonical_path(config, "SPEC selector config", "file")
    canonical_path(benchmark_config, "benchmark config", "file")
    canonical_path(
        row["working_directory"], "workload directory", "directory"
    )
    canonical_path(
        row["checkpoint_directory"], "checkpoint directory", "directory"
    )
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    command = build_command(args, binary, config, output_dir, row)
    environment = os.environ.copy()
    for name, value in row.get("environment", {}).items():
        environment[str(name)] = str(value)
    environment["OMP_NUM_THREADS"] = "1"
    environment["MKL_NUM_THREADS"] = "1"
    environment["OPENBLAS_NUM_THREADS"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    # Absolute executable prefixes alter the effective workload command.
    environment.pop("SPEC06_EXEC_PREFIX", None)
    environment.pop("SPEC06_RUN_DIR", None)
    environment.pop("SPEC17_EXEC_PREFIX", None)
    environment.pop("SPEC17_RUN_DIR", None)

    config_identity = {
        row["config_selection_source"]: file_sha256(config),
        row["config_source"]: file_sha256(benchmark_config),
    }
    identity = {
        "binary": binary,
        "binary_sha256": binary_hash,
        "canonical_nighthawk_source_sha": document.get(
            "nighthawk_git_sha"
        ),
        "capability_profile": args.capability_profile,
        "command": command,
        "command_sha256": stable_sha256(command),
        "config_files": config_identity,
        "config_hash": stable_sha256(config_identity),
        "evidence_class": args.evidence_class,
        "manifest": manifest_path,
        "manifest_sha256": manifest_hash,
        "max_insts": args.max_insts,
        "mode": args.mode,
        "pending_policy": args.pending_policy,
        "row_id": args.row_id,
        "runner_pid": os.getpid(),
        "design_scheme": "SDO",
        "drain_at_end": args.drain_at_end,
        "cache_constructor_scheme": "SDO",
        "legacy_cache_constructor_adapter": False,
        "smshr_size": args.smshr,
        "l1d_size": args.l1d_size,
        "l1i_size": args.l1i_size,
        "l2_size": args.l2_size,
        "l1d_assoc": args.l1d_assoc,
        "l1i_assoc": args.l1i_assoc,
        "l2_assoc": args.l2_assoc,
        "llc_bank_contention": args.llc_bank_contention,
        "llc_fake_getspec": args.llc_fake_getspec,
        "llc_data_banks": args.llc_data_banks,
        "llc_tag_banks": args.llc_tag_banks,
        "llc_data_latency": args.llc_data_latency,
        "llc_tag_latency": args.llc_tag_latency,
        "llc_data_issue_interval": args.llc_data_issue_interval,
        "llc_tag_issue_interval": args.llc_tag_issue_interval,
        "source_root": source_root,
        "source_sha": source_sha,
        "stt": 1,
        "implicit_channel": 1,
        "threat_model": args.threat,
        "working_directory": row["working_directory"],
    }
    write_json(os.path.join(output_dir, "execution_identity.json"), identity)
    write_json(os.path.join(output_dir, "canonical_workload_row.json"), row)
    with open(os.path.join(output_dir, "container_pid"), "w") as handle:
        handle.write(str(os.getpid()) + "\n")

    if args.dry_run:
        print(json.dumps(command))
        return 0

    started = utc_now()
    stdout_path = os.path.join(output_dir, "gem5.stdout")
    stderr_path = os.path.join(output_dir, "gem5.stderr")
    with open(stdout_path, "wb") as stdout_handle:
        with open(stderr_path, "wb") as stderr_handle:
            process = subprocess.Popen(
                command,
                cwd=row["working_directory"],
                env=environment,
                stdout=stdout_handle,
                stderr=stderr_handle,
            )
            with open(
                os.path.join(output_dir, "timed_command_pid"), "w"
            ) as handle:
                handle.write(str(process.pid) + "\n")
            exit_status = process.wait()

    write_json(
        os.path.join(output_dir, "execution_lifecycle.json"),
        {
            "started_utc": started,
            "finished_utc": utc_now(),
            "exit_status": exit_status,
        },
    )
    with open(os.path.join(output_dir, "exit_status"), "w") as handle:
        handle.write(str(exit_status) + "\n")
    return exit_status


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (IOError, OSError, RuntimeError, ValueError) as error:
        print("error: " + str(error), file=sys.stderr)
        raise SystemExit(2)
