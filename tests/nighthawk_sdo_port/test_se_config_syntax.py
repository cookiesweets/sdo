#!/usr/bin/env python3

"""Syntax gate for the Python-2 runtime configuration used by SDO sanity."""

from __future__ import print_function

import os
import unittest


REPO_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", ".."))
SE_CONFIG = os.path.join(REPO_ROOT, "configs", "example", "se.py")


class SeConfigSyntaxTest(unittest.TestCase):
    def test_future_print_function_file_has_valid_function_syntax(self):
        with open(SE_CONFIG, "rb") as handle:
            source = handle.read()

        # This is deliberately compile-only: importing se.py requires the
        # generated gem5 m5 module. Python 3 provides the stricter parser for
        # catching Python-2 print statements made illegal by print_function.
        compile(source, SE_CONFIG, "exec")


if __name__ == "__main__":
    unittest.main(verbosity=2)
