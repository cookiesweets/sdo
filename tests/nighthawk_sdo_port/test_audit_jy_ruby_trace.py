#!/usr/bin/env python3

from __future__ import print_function

import os
import subprocess
import sys
import tempfile
import unittest


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
AUDITOR = os.path.join(TEST_DIR, "audit_jy_ruby_trace.py")


def run_auditor(lines):
    trace_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
    try:
        trace_file.writelines(lines)
        trace_file.close()
        process = subprocess.Popen(
            [sys.executable, AUDITOR, trace_file.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True)
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    finally:
        try:
            os.unlink(trace_file.name)
        except OSError:
            pass


class JyRubyTraceAuditTest(unittest.TestCase):
    def test_exactly_one_two_stage_callback_pair_passes(self):
        status, stdout, stderr = run_auditor([
            "10 SPEC_LD_L1 commands callback readCallback_fromL0 "
            "(sn=7, idx=1-0, addr=[0x4, line 0x0])\n",
            "12 SPEC_LD_L1 commands callback readCallback_fromL1 "
            "(sn=7, idx=1-0, addr=[0x4, line 0x0]) "
            "--> last readCallback\n",
            "13 fail to insert a request to Sequencer "
            "SpecLDRequestTable with (addr=0x0, ld_idx=2, sn=9)\n",
        ])
        self.assertEqual(status, 0, stderr)
        self.assertIn("unique_seqnums=1\n", stdout)
        self.assertIn("failed_insert_lines=1\n", stdout)
        self.assertIn("final_status=PASS\n", stdout)

    def test_duplicate_final_callback_fails(self):
        status, stdout, unused_stderr = run_auditor([
            "10 SPEC_LD_L1 commands callback readCallback_fromL0 "
            "(sn=8, idx=1-0, addr=[0x4, line 0x0])\n",
            "12 SPEC_LD_L1 commands callback readCallback_fromL1 "
            "(sn=8, idx=1-0, addr=[0x4, line 0x0])\n",
            "14 SPEC_LD_L1 commands callback readCallback_fromL1 "
            "(sn=8, idx=1-0, addr=[0x4, line 0x0])\n",
        ])
        self.assertEqual(status, 1)
        self.assertIn("seqnums_with_duplicate_l1=1\n", stdout)
        self.assertIn("seqnums_not_exactly_one_each=1\n", stdout)
        self.assertIn("final_status=FAIL\n", stdout)

    def test_missing_second_stage_callback_fails(self):
        status, stdout, unused_stderr = run_auditor([
            "10 SPEC_LD_L1 commands callback readCallback_fromL0 "
            "(sn=9, idx=1-0, addr=[0x4, line 0x0])\n",
        ])
        self.assertEqual(status, 1)
        self.assertIn("seqnums_missing_l1=1\n", stdout)
        self.assertIn("final_status=FAIL\n", stdout)

    def test_stuck_packet_fails_even_with_balanced_callbacks(self):
        status, stdout, unused_stderr = run_auditor([
            "10 SPEC_LD_L1 commands callback readCallback_fromL0 "
            "(sn=10, idx=1-0, addr=[0x4, line 0x0])\n",
            "12 SPEC_LD_L1 commands callback readCallback_fromL1 "
            "(sn=10, idx=1-0, addr=[0x4, line 0x0])\n",
            "20 Stuck packet: sn:10, isSpec=1\n",
        ])
        self.assertEqual(status, 1)
        self.assertIn("stuck_packet_lines=1\n", stdout)
        self.assertIn("final_status=FAIL\n", stdout)

    def test_empty_trace_fails_closed(self):
        status, stdout, unused_stderr = run_auditor([])
        self.assertEqual(status, 1)
        self.assertIn("unique_seqnums=0\n", stdout)
        self.assertIn("final_status=FAIL\n", stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
