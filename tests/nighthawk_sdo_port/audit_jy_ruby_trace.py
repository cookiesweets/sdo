#!/usr/bin/env python
#
# Audit the two-stage callback accounting emitted by the JY_Ruby debug flag.
#
# Keep this script compatible with Python 2.7 and Python 3.5: the remote
# Ubuntu 16.04 gem5 environment still uses the legacy Python runtime.

from __future__ import print_function

import argparse
import re
import sys


CALLBACK_RE = re.compile(
    r"SPEC_LD_L1 commands callback readCallback_fromL([01]) "
    r"\(sn=([0-9]+),")


def audit_trace(path):
    callback_counts = {}
    failed_inserts = 0
    stuck_packets = 0

    with open(path, "r") as trace_file:
        for line in trace_file:
            match = CALLBACK_RE.search(line)
            if match:
                level = match.group(1)
                sequence_number = match.group(2)
                counts = callback_counts.setdefault(
                    sequence_number, {"0": 0, "1": 0})
                counts[level] += 1

            if ("fail to insert a request to Sequencer "
                    "SpecLDRequestTable" in line):
                failed_inserts += 1
            if "Stuck packet" in line:
                stuck_packets += 1

    totals = {
        "unique_seqnums": len(callback_counts),
        "l0_callbacks": 0,
        "l1_callbacks": 0,
        "seqnums_with_duplicate_l0": 0,
        "seqnums_with_duplicate_l1": 0,
        "seqnums_missing_l0": 0,
        "seqnums_missing_l1": 0,
        "seqnums_not_exactly_one_each": 0,
        "failed_insert_lines": failed_inserts,
        "stuck_packet_lines": stuck_packets,
    }

    for counts in callback_counts.values():
        l0_count = counts["0"]
        l1_count = counts["1"]
        totals["l0_callbacks"] += l0_count
        totals["l1_callbacks"] += l1_count
        if l0_count > 1:
            totals["seqnums_with_duplicate_l0"] += 1
        if l1_count > 1:
            totals["seqnums_with_duplicate_l1"] += 1
        if l0_count == 0:
            totals["seqnums_missing_l0"] += 1
        if l1_count == 0:
            totals["seqnums_missing_l1"] += 1
        if l0_count != 1 or l1_count != 1:
            totals["seqnums_not_exactly_one_each"] += 1

    totals["final_status"] = (
        "PASS"
        if totals["unique_seqnums"] > 0
        and totals["seqnums_not_exactly_one_each"] == 0
        and totals["stuck_packet_lines"] == 0
        else "FAIL"
    )
    return totals


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit exactly-once SDO L0/L1 callback trace pairs.")
    parser.add_argument("trace", help="JY_Ruby debug trace or stdout log")
    arguments = parser.parse_args(argv)

    try:
        totals = audit_trace(arguments.trace)
    except (IOError, OSError) as error:
        print("audit_jy_ruby_trace: {0}".format(error), file=sys.stderr)
        return 2

    output_order = [
        "unique_seqnums",
        "l0_callbacks",
        "l1_callbacks",
        "seqnums_with_duplicate_l0",
        "seqnums_with_duplicate_l1",
        "seqnums_missing_l0",
        "seqnums_missing_l1",
        "seqnums_not_exactly_one_each",
        "failed_insert_lines",
        "stuck_packet_lines",
        "final_status",
    ]
    print("schema_version=1")
    print("trace_path={0}".format(arguments.trace))
    for key in output_order:
        print("{0}={1}".format(key, totals[key]))

    return 0 if totals["final_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
