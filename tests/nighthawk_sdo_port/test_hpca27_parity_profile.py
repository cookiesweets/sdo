#!/usr/bin/env python

"""Regressions for the explicit HPCA27 sparespec-stt parity profile.

Keep this file compatible with Python 2.7 and Python 3.5.
"""

from __future__ import print_function

import os
import shutil
import sys
import tempfile
import unittest


TEST_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(TEST_DIR, "..", ".."))
CONFIGS_ROOT = os.path.join(REPO_ROOT, "configs")
sys.path.insert(0, CONFIGS_ROOT)

from common.SDOConfig import configure_hpca27_parity_cpu
from common.SDOConfig import configure_hpca27_parity_branch_predictor
from common.SDOConfig import HPCA27_BRANCH_PREDICTOR_PARITY
from common.SDOConfig import HPCA27_CPU_PARITY
from common.SDOConfig import HPCA27_INDIRECT_PREDICTOR_PARITY
from common.SDOConfig import HPCA27_FINAL_EVIDENCE_CLASS
from common.SDOConfig import HPCA27_OPTION_PARITY
from common.SDOConfig import HPCA27_SANITY_EVIDENCE_CLASS
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
    options.hpca27_evidence_class = HPCA27_FINAL_EVIDENCE_CLASS
    return options


def parity_cpu():
    cpu = Bag()
    cpu.branchPred = Bag()
    cpu.branchPred.type = "TournamentBP"
    cpu.branchPred.indirectBranchPred = Bag()
    cpu.branchPred.indirectBranchPred.type = "SimpleIndirectPredictor"
    return cpu


def runner_argv(
        max_insts="500000000",
        evidence_class=HPCA27_FINAL_EVIDENCE_CLASS):
    return [
        "--source-root", "/source",
        "--binary", "/binary",
        "--manifest", "/manifest",
        "--row-id", "SPEC2006:401.bzip2:bzip2",
        "--mode", "sdo-implicit",
        "--threat", "Futuristic",
        "--capability-profile", "current",
        "--pending-policy", "not_applicable",
        "--smshr", "0",
        "--l1d-size", "64kB",
        "--l1i-size", "32kB",
        "--l2-size", "2MB",
        "--l1d-assoc", "8",
        "--l1i-assoc", "4",
        "--l2-assoc", "16",
        "--llc-bank-contention", "0",
        "--llc-fake-getspec", "0",
        "--llc-data-banks", "1",
        "--llc-tag-banks", "1",
        "--llc-data-latency", "1",
        "--llc-tag-latency", "1",
        "--llc-data-issue-interval", "0",
        "--llc-tag-issue-interval", "0",
        "--output-dir", "/output",
        "--max-insts", max_insts,
        "--evidence-class", evidence_class,
        "--expected-source-sha", "0" * 40,
        "--expected-binary-sha256", "0" * 64,
        "--expected-manifest-sha256", "1" * 64,
    ]


def runner_args(
        max_insts="500000000",
        evidence_class=HPCA27_FINAL_EVIDENCE_CLASS):
    return RUNNER.parse_args(runner_argv(max_insts, evidence_class))


class CpuParityProfileTest(unittest.TestCase):
    def test_explicit_profile_sets_every_reviewed_o3_control(self):
        cpu = parity_cpu()
        configure_hpca27_parity_cpu([cpu], parity_options())
        actual = dict(
            (name, getattr(cpu, name)) for name in HPCA27_CPU_PARITY
        )
        self.assertEqual(HPCA27_CPU_PARITY, actual)

    def test_profile_sets_nested_branch_predictor_reference_semantics(self):
        cpu = parity_cpu()
        configure_hpca27_parity_branch_predictor(
            [cpu], parity_options()
        )
        direct = dict(
            (name, getattr(cpu.branchPred, name))
            for name in HPCA27_BRANCH_PREDICTOR_PARITY
        )
        indirect = dict(
            (name, getattr(cpu.branchPred.indirectBranchPred, name))
            for name in HPCA27_INDIRECT_PREDICTOR_PARITY
        )
        self.assertEqual(HPCA27_BRANCH_PREDICTOR_PARITY, direct)
        self.assertEqual(HPCA27_INDIRECT_PREDICTOR_PARITY, indirect)

    def test_profile_rejects_wrong_branch_predictor_schema(self):
        cpu = parity_cpu()
        cpu.branchPred.type = "BiModeBP"
        with self.assertRaises(ValueError):
            configure_hpca27_parity_cpu([cpu], parity_options())

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

    def test_profile_accepts_only_explicit_sanity_budgets(self):
        for maxinsts in (10000000, 25000000):
            options = parity_options()
            options.hpca27_evidence_class = HPCA27_SANITY_EVIDENCE_CLASS
            options.maxinsts = maxinsts
            validate_hpca27_parity_options(options)

        for maxinsts in (9000000, 500000000):
            options = parity_options()
            options.hpca27_evidence_class = HPCA27_SANITY_EVIDENCE_CLASS
            options.maxinsts = maxinsts
            with self.assertRaises(ValueError):
                validate_hpca27_parity_options(options)

    def test_profile_rejects_short_roi_without_sanity_class(self):
        options = parity_options()
        options.maxinsts = 10000000
        with self.assertRaises(ValueError):
            validate_hpca27_parity_options(options)

    def test_profile_rejects_non_sdo_mechanism(self):
        options = parity_options()
        options.scheme = "DelayExecute"
        with self.assertRaises(ValueError):
            validate_hpca27_parity_options(options)


class RubyParityProfileTest(unittest.TestCase):
    def test_reference_functional_unit_pool_is_explicit(self):
        pool = " ".join(read_source("src/cpu/o3/FUPool.py").split())
        self.assertIn(
            "FUList = [ IntALU(), IntMultDiv(), FP_ALU(), "
            "FP_MultDiv(), ReadPort(), SIMD_Unit(), WritePort(), "
            "RdWrPort(), IprPort() ]",
            pool,
        )

        units = " ".join(
            read_source("src/cpu/o3/FuncUnitConfig.py").split()
        )
        for contract in (
            "class IntALU(FUDesc): opList = "
            "[ OpDesc(opClass='IntAlu') ] count = 6",
            "class IntMultDiv(FUDesc):",
            "class FP_MultDiv(FUDesc):",
            "class ReadPort(FUDesc): opList =",
            "class WritePort(FUDesc): opList =",
            "class RdWrPort(FUDesc): opList =",
        ):
            self.assertIn(contract, units)
        self.assertNotIn("class IntMult(FUDesc):", units)
        self.assertNotIn("class IntDiv(FUDesc):", units)
        self.assertNotIn("class FP_Mult(FUDesc):", units)
        self.assertNotIn("class FP_Div(FUDesc):", units)

    def test_reference_ruby_prefetcher_defaults_are_explicit(self):
        source = " ".join(
            read_source(
                "src/mem/ruby/structures/RubyPrefetcher.py"
            ).split()
        )
        for contract in (
            'pf_per_stream = Param.UInt32(1,',
            'train_misses = Param.UInt32(4,',
            'num_startup_pfs = Param.UInt32(1,',
            'cross_page = Param.Bool(False,',
        ):
            self.assertIn(contract, source)
        self.assertNotIn("num_extra_pfs = Param.UInt32(", source)

        implementation = read_source(
            "src/mem/ruby/structures/Prefetcher.cc"
        )
        header = read_source(
            "src/mem/ruby/structures/Prefetcher.hh"
        )
        self.assertNotIn("p->num_extra_pfs", implementation)
        self.assertNotIn("m_num_extra_pfs", implementation)
        self.assertNotIn("m_num_extra_pfs", header)
        for allocation in (
            "delete[] m_unit_filter_hit;",
            "delete[] m_negative_filter_hit;",
            "delete[] m_nonunit_stride;",
            "delete[] m_nonunit_hit;",
        ):
            self.assertIn(allocation, implementation)

    def test_reference_spare_field_representation_is_retained(self):
        source = " ".join(
            read_source("src/mem/ruby/structures/RubyCache.py").split()
        )
        self.assertIn("is_l1ispare = Param.Bool(False,", source)
        self.assertIn("is_l1dspare = Param.Bool(False,", source)

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

    def test_cache_contract_fields_are_effective_and_explicit(self):
        ruby_cache = read_source(
            "src/mem/ruby/structures/RubyCache.py"
        )
        self.assertIn("dataIssueInterval = Param.Cycles(", ruby_cache)
        self.assertIn("tagIssueInterval = Param.Cycles(", ruby_cache)
        self.assertIn("is_stt = Param.Bool(False", ruby_cache)

        banked_array = " ".join(
            read_source(
                "src/mem/ruby/structures/BankedArray.cc"
            ).split()
        )
        self.assertIn(
            "issueInterval == 0 ? accessLatency : issueInterval",
            banked_array,
        )
        self.assertIn(
            "(issueInterval-1) * m_ruby_system->clockPeriod()",
            banked_array,
        )

        two_level = " ".join(
            read_source("configs/ruby/MESI_Two_Level.py").split()
        )
        for binding in (
            "dataArrayBanks = 1",
            "tagArrayBanks = 1",
            "dataAccessLatency = 1",
            "tagAccessLatency = 1",
            "dataIssueInterval = 0",
            "tagIssueInterval = 0",
        ):
            self.assertEqual(2, two_level.count(binding), binding)
        self.assertEqual(2, two_level.count("is_stt = stt"))
        self.assertEqual(1, two_level.count("is_stt = False"))
        for option in (
            "llc_data_array_banks",
            "llc_tag_array_banks",
            "llc_data_access_latency",
            "llc_tag_access_latency",
            "llc_data_issue_interval",
            "llc_tag_issue_interval",
        ):
            self.assertIn("options." + option, two_level)

    def test_reference_static_dram_pipeline_latency(self):
        source = read_source("src/mem/DRAMCtrl.py")
        self.assertEqual(
            1,
            source.count(
                'static_frontend_latency = Param.Latency("10ns"'
            ),
        )
        self.assertEqual(
            1,
            source.count(
                'static_backend_latency = Param.Latency("10ns"'
            ),
        )
        self.assertNotIn(
            'static_frontend_latency = Param.Latency("50ns"', source
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
            "--hpca27-evidence-class=final-performance",
            "--threat_model=Futuristic",
            "--STT=1",
            "--impChannel=1",
            "--ruby_enable_resource_stall=0",
            "--ruby-sequencer-hit-latency=1",
            "--llc-data-array-banks=1",
            "--llc-tag-array-banks=1",
            "--llc-data-access-latency=1",
            "--llc-tag-access-latency=1",
            "--llc-data-issue-interval=0",
            "--llc-tag-issue-interval=0",
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

    def test_runner_requires_every_cache_selector(self):
        cache_options = (
            "--l1d-size",
            "--l1i-size",
            "--l2-size",
            "--l1d-assoc",
            "--l1i-assoc",
            "--l2-assoc",
            "--llc-bank-contention",
            "--llc-fake-getspec",
            "--llc-data-banks",
            "--llc-tag-banks",
            "--llc-data-latency",
            "--llc-tag-latency",
            "--llc-data-issue-interval",
            "--llc-tag-issue-interval",
        )
        original_stderr = sys.stderr
        captured_stderr = open(os.devnull, "w")
        sys.stderr = captured_stderr
        try:
            for option in cache_options:
                argv = runner_argv()
                index = argv.index(option)
                del argv[index:index + 2]
                with self.assertRaises(SystemExit):
                    RUNNER.parse_args(argv)
        finally:
            sys.stderr = original_stderr
            captured_stderr.close()

    def test_runner_rejects_noncanonical_identity_paths(self):
        root = os.path.realpath(tempfile.mkdtemp(prefix="sdo-parity-"))
        try:
            identity_file = os.path.join(root, "identity")
            with open(identity_file, "w") as handle:
                handle.write("identity\n")
            self.assertEqual(
                identity_file,
                RUNNER.canonical_path(
                    identity_file, "identity input", "file"
                ),
            )
            with self.assertRaises(ValueError):
                RUNNER.canonical_path(
                    "relative/identity", "identity input", "file"
                )
            noncanonical = os.path.join(
                root, "unused", "..", "identity"
            )
            with self.assertRaises(ValueError):
                RUNNER.canonical_path(
                    noncanonical, "identity input", "file"
                )

            symlink = os.path.join(root, "identity-link")
            os.symlink(identity_file, symlink)
            with self.assertRaises(ValueError):
                RUNNER.canonical_path(
                    symlink, "identity input", "file"
                )

            real_directory = os.path.join(root, "real-directory")
            os.mkdir(real_directory)
            nested_file = os.path.join(real_directory, "nested")
            with open(nested_file, "w") as handle:
                handle.write("nested\n")
            directory_link = os.path.join(root, "directory-link")
            os.symlink(real_directory, directory_link)
            with self.assertRaises(ValueError):
                RUNNER.canonical_path(
                    os.path.join(directory_link, "nested"),
                    "identity input",
                    "file",
                )
        finally:
            shutil.rmtree(root)

    def test_runner_rejects_non_500m_roi(self):
        args = runner_args(max_insts="100000000")
        row = {"post_restore_instruction_budget": 500000000}
        with self.assertRaises(ValueError):
            RUNNER.validate_fixed_controls(args, row)

    def test_runner_accepts_only_explicit_sanity_budgets(self):
        for budget in (10000000, 25000000):
            args = runner_args(
                max_insts=str(budget),
                evidence_class=HPCA27_SANITY_EVIDENCE_CLASS,
            )
            row = {
                "display_name": "bzip2",
                "checkpoint_directory": "/checkpoint",
                "checkpoint_restore": 10000000000,
                "post_restore_instruction_budget": 500000000,
            }
            RUNNER.validate_fixed_controls(args, row)
            command = RUNNER.build_command(
                args, "/binary", "/source/config.py", "/output", row
            )
            self.assertIn(
                "--hpca27-evidence-class="
                + HPCA27_SANITY_EVIDENCE_CLASS,
                command,
            )
            self.assertIn("--maxinsts=" + str(budget), command)

        for budget in (9000000, 500000000):
            args = runner_args(
                max_insts=str(budget),
                evidence_class=HPCA27_SANITY_EVIDENCE_CLASS,
            )
            row = {"post_restore_instruction_budget": 500000000}
            with self.assertRaises(ValueError):
                RUNNER.validate_fixed_controls(args, row)

    def test_runner_rejects_budget_manifest_mismatch(self):
        args = runner_args(
            max_insts="10000000",
            evidence_class=HPCA27_SANITY_EVIDENCE_CLASS,
        )
        row = {"post_restore_instruction_budget": 25000000}
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

    def test_runner_identity_binds_evidence_class_flags(self):
        source = read_source(
            "exp_script/weekend_campaign/"
            "run_nighthawk_checkpoint_job.py"
        )
        self.assertIn('"evidence_class": args.evidence_class', source)
        self.assertIn(
            '"sanity_slice": (\n'
            "            args.evidence_class == "
            "HPCA27_SANITY_EVIDENCE_CLASS",
            source,
        )
        self.assertIn(
            '"final_performance_candidate": (\n'
            "            args.evidence_class == "
            "HPCA27_FINAL_EVIDENCE_CLASS",
            source,
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

    def test_branch_adapter_is_reapplied_after_checkpoint_cpu_setup(self):
        cpu_config = read_source("configs/common/CpuConfig.py")
        source = read_source("configs/common/Simulation.py")
        replacement = "branchPred.indirectBranchPred ="
        adapter = "configure_hpca27_parity_branch_predictor("
        self.assertIn(
            "import configure_hpca27_parity_branch_predictor",
            cpu_config,
        )
        self.assertIn(replacement, source)
        self.assertIn(adapter, source)
        self.assertLess(source.index(replacement), source.index(adapter))

    def test_branch_representation_gap_remains_explicitly_partial(self):
        source = read_source(
            "docs/hpca27_branch_predictor_evidence_adapter.md"
        )
        self.assertIn("versioned adapter", source)
        self.assertIn("mixed schema is ambiguous and", source)
        self.assertIn("does not itself admit an artifact", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
