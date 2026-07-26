#!/usr/bin/env python3

"""Source and config.ini regressions for SDO enable_MLDOM wiring."""

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
sys.path.insert(0, TEST_DIR)

from common.SDOConfig import is_sdo_enabled
from audit_mldom_config import AuditError, audit_config


def read_source(relative_path):
    path = os.path.join(REPO_ROOT, relative_path)
    with open(path, "r") as handle:
        return handle.read()


class Options(object):
    pass


class MldomSourceContractTest(unittest.TestCase):
    def test_shared_predicate_is_exact_and_fail_closed(self):
        options = Options()
        self.assertFalse(is_sdo_enabled(options))
        for scheme in (None, "", "sdo", "SDO ", "UnsafeBaseline",
                       "DelayExecute"):
            options.scheme = scheme
            self.assertFalse(is_sdo_enabled(options), scheme)
        options.scheme = "SDO"
        self.assertTrue(is_sdo_enabled(options))

    def test_cpu_and_ruby_use_the_shared_predicate(self):
        cpu_source = read_source("configs/common/CpuConfig.py")
        ruby_source = read_source("configs/ruby/Ruby.py")
        self.assertIn(
            "sdo_enabled = is_sdo_enabled(options)", cpu_source)
        self.assertIn(
            "cpu.enable_MLDOM = sdo_enabled", cpu_source)
        ruby_assignment = "ruby.enable_MLDOM = is_sdo_enabled(options)"
        self.assertIn(ruby_assignment, ruby_source)
        self.assertLess(
            ruby_source.index(ruby_assignment),
            ruby_source.index("eval(\"%s.create_system"))

    def test_two_level_l1_and_memory_owner_copy_ruby_value(self):
        protocol_source = read_source("configs/ruby/MESI_Two_Level.py")
        ruby_source = read_source("configs/ruby/Ruby.py")
        normalized_protocol = " ".join(protocol_source.split())
        self.assertIn(
            "enable_MLDOM = ruby_system.enable_MLDOM",
            normalized_protocol)
        self.assertIn(
            "dir_cntrl.enable_MLDOM = ruby_system.enable_MLDOM",
            ruby_source)

    def test_controller_default_remains_fail_closed_and_cpp_consumes_it(self):
        controller_source = read_source(
            "src/mem/ruby/slicc_interface/Controller.py")
        abstract_source = read_source(
            "src/mem/ruby/slicc_interface/AbstractController.cc")
        self.assertIn(
            'enable_MLDOM = Param.Bool(False, "if enable MLDOM")',
            controller_source)
        self.assertIn("enable_MLDOM(p->enable_MLDOM)", abstract_source)
        self.assertIn("if (!enable_MLDOM)", abstract_source)

    def test_directory_is_the_two_level_memory_response_owner(self):
        directory_source = read_source(
            "src/mem/protocol/MESI_Two_Level-dir.sm")
        l1_source = read_source(
            "src/mem/protocol/MESI_Two_Level-L1cache.sm")
        self.assertIn("queueMemoryRead(", directory_source)
        self.assertNotIn("queueMemoryRead(", l1_source)


class MldomRuntimeConfigAuditTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="mldom-config-test-")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def write_config(self, cpu=True, ruby=True, l1=True, directory=True,
                     scheme="SDO", omit=None, invalid=None):
        sections = (
            ("system.cpu", cpu, (("scheme", scheme),)),
            ("system.ruby", ruby, ()),
            ("system.ruby.l1_cntrl0", l1, ()),
            ("system.ruby.dir_cntrl0", directory, ()),
        )
        path = os.path.join(self.temp_dir, "config.ini")
        with open(path, "w") as handle:
            for section, enabled, extra in sections:
                if omit == section:
                    continue
                handle.write("[%s]\n" % section)
                value = str(enabled).lower()
                if invalid == section:
                    value = "1"
                handle.write("enable_MLDOM=%s\n" % value)
                for key, item in extra:
                    handle.write("%s=%s\n" % (key, item))
                handle.write("\n")
            handle.write("[system.ruby.l1_cntrl0.L1Dcache]\n")
            handle.write("enable_MLDOM=false\n")
        return path

    def test_enabled_sdo_config_passes(self):
        checked = audit_config(self.write_config(), True)
        self.assertEqual(4, len(checked))

    def test_disabled_non_sdo_config_passes(self):
        path = self.write_config(
            cpu=False, ruby=False, l1=False, directory=False,
            scheme="DelayExecute")
        checked = audit_config(path, False)
        self.assertEqual(4, len(checked))

    def test_old_l1_default_gap_fails(self):
        with self.assertRaises(AuditError):
            audit_config(self.write_config(l1=False), True)

    def test_directory_default_gap_fails(self):
        with self.assertRaises(AuditError):
            audit_config(self.write_config(directory=False), True)

    def test_missing_component_fails_closed(self):
        with self.assertRaises(AuditError):
            audit_config(
                self.write_config(omit="system.ruby.l1_cntrl0"), True)

    def test_noncanonical_boolean_fails_closed(self):
        with self.assertRaises(AuditError):
            audit_config(
                self.write_config(invalid="system.ruby"), True)

    def test_sdo_scheme_with_disabled_expectation_fails(self):
        path = self.write_config(
            cpu=False, ruby=False, l1=False, directory=False, scheme="SDO")
        with self.assertRaises(AuditError):
            audit_config(path, False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
