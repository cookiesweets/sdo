#!/usr/bin/env python

"""Regressions for the explicit HPCA27 sparespec-stt parity profile."""

from __future__ import print_function

import os
import sys
import unittest


TEST_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(TEST_DIR, "..", ".."))
CONFIGS_ROOT = os.path.join(REPO_ROOT, "configs")
sys.path.insert(0, CONFIGS_ROOT)

from common.SDOConfig import configure_hpca27_parity_cpu
from common.SDOConfig import HPCA27_CPU_PARITY
from common.SDOConfig import HPCA27_OPTION_PARITY
from common.SDOConfig import validate_hpca27_parity_options


RUNNER_PATH = os.path.join(
    REPO_ROOT,
    "exp_script",
    "weekend_campaign",
    "run_nighthawk_checkpoint_job.py",
)
try:
    import importlib.util
    runner_spec = importlib.util.spec_from_file_location(
        "sdo_hpca27_runner", RUNNER_PATH
    )
    RUNNER = importlib.util.module_from_spec(runner_spec)
    runner_spec.loader.exec_module(RUNNER)
except (AttributeError, ImportError):
    import imp
    RUNNER = imp.load_source("sdo_hpca27_runner", RUNNER_PATH)


def read_source(relative_path):
    path = os.path.join(REPO_ROOT, relative_path)
    with open(path, "r") as handle:
        return handle.read()


class Bag(object):
    pass


def parity_options():
    options = Bag()
    for name, value in HPCA27_OPTION_PARITY.items():
        setattr(options, name, value)
    options.hpca27_performance_parity = True
    return options


def runner_args(max_insts="500000000"):
    return RUNNER.parse_args([
        "--source-root", "/source",
        "--binary", "/binary",
        "--manifest", "/manifest",
        "--row-id", "SPEC2006:401.bzip2:bzip2",
        "--mode", "sdo-implicit",
        "--threat", "Futuristic",
        "--capability-profile", "current",
        "--pending-policy", "not_applicable",
        "--smshr", "0",
        "--output-dir", "/output",
        "--max-insts", max_insts,
        "--expected-source-sha", "0" * 40,
        "--expected-binary-sha256", "0" * 64,
        "--expected-manifest-sha256", "1" * 64,
    ])


class CpuParityProfileTest(unittest.TestCase):
    def test_explicit_profile_sets_every_reviewed_o3_control(self):
        cpu = Bag()
        configure_hpca27_parity_cpu([cpu], parity_options())
        actual = dict(
            (name, getattr(cpu, name)) for name in HPCA27_CPU_PARITY
        )
        self.assertEqual(HPCA27_CPU_PARITY, actual)

    def test_profile_is_opt_in(self):
        options = parity_options()
        options.hpca27_performance_parity = False
        cpu = Bag()
        configure_hpca27_parity_cpu([cpu], options)
        for name in HPCA27_CPU_PARITY:
            self.assertFalse(hasattr(cpu, name), name)

    def test_profile_rejects_tso_and_short_roi(self):
        for name, value in (("mem_model", "TSO"), ("maxinsts", 100000000)):
            options = parity_options()
            setattr(options, name, value)
            with self.assertRaises(ValueError):
                validate_hpca27_parity_options(options)

    def test_profile_rejects_non_sdo_mechanism(self):
        options = parity_options()
        options.scheme = "DelayExecute"
        with self.assertRaises(ValueError):
            validate_hpca27_parity_options(options)


class RubyParityProfileTest(unittest.TestCase):
    def test_two_level_constructors_bind_stalls_and_hit_latency(self):
        source = " ".join(
            read_source("configs/ruby/MESI_Two_Level.py").split()
        )
        self.assertEqual(3, source.count(
            "resourceStalls = resource_stalls"
        ))
        self.assertIn(
            "icache_hit_latency = options.ruby_sequencer_hit_latency",
            source,
        )
        self.assertIn(
            "dcache_hit_latency = options.ruby_sequencer_hit_latency",
            source,
        )

    def test_ruby_validates_before_construction(self):
        source = read_source("configs/ruby/Ruby.py")
        validation = "validate_hpca27_parity_options(options)"
        self.assertIn(validation, source)
        self.assertLess(
            source.index(validation), source.index("system.ruby = RubySystem()")
        )

    def test_options_keep_historical_defaults_without_profile(self):
        source = " ".join(read_source("configs/common/Options.py").split())
        self.assertIn(
            'parser.add_option("--hpca27-performance-parity", '
            "default=False, action=\"store_true\"",
            source,
        )
        self.assertIn(
            'parser.add_option("--ruby-sequencer-hit-latency", default=2',
            source,
        )


class CanonicalRunnerContractTest(unittest.TestCase):
    def test_runner_builds_explicit_sdo_parity_command(self):
        args = runner_args()
        row = {
            "checkpoint_directory": "/checkpoint",
            "checkpoint_restore": 10000000000,
            "display_name": "bzip2",
            "post_restore_instruction_budget": 500000000,
        }
        RUNNER.validate_fixed_controls(args, row)
        command = RUNNER.build_command(
            args, "/binary", "/source/config.py", "/output", row
        )
        required = (
            "--scheme=SDO",
            "--mem_model=RC",
            "--maxinsts=500000000",
            "--threat_model=Futuristic",
            "--STT=1",
            "--impChannel=1",
            "--ruby_enable_resource_stall=0",
            "--ruby-sequencer-hit-latency=1",
            "--hpca27-performance-parity",
            "--pred_type=tournament_2way",
            "--subpred1_type=greedy",
            "--subpred2_type=loop",
            "--TLB_defense=SDO",
        )
        for option in required:
            self.assertIn(option, command)
        self.assertNotIn("--smshr-size=0", command)
        self.assertNotIn("--nighthawk-pending-policy=not_applicable", command)

    def test_runner_rejects_non_500m_roi(self):
        args = runner_args(max_insts="100000000")
        row = {"post_restore_instruction_budget": 500000000}
        with self.assertRaises(ValueError):
            RUNNER.validate_fixed_controls(args, row)

    def test_runner_rejects_non_500m_manifest_row(self):
        args = runner_args()
        row = {"post_restore_instruction_budget": 100000000}
        with self.assertRaises(ValueError):
            RUNNER.validate_fixed_controls(args, row)

    def test_runner_path_matches_outer_gate_contract(self):
        relative = os.path.relpath(RUNNER_PATH, REPO_ROOT)
        self.assertEqual(
            os.path.join(
                "exp_script",
                "weekend_campaign",
                "run_nighthawk_checkpoint_job.py",
            ),
            relative,
        )

    def test_parity_profile_leaves_process_cwd_unset(self):
        for relative in (
            "configs/example/spec06_config.py",
            "configs/example/spec17_config.py",
        ):
            source = read_source(relative)
            self.assertIn(
                "if not options.hpca27_performance_parity:", source
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
