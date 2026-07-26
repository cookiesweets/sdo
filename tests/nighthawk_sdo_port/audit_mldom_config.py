#!/usr/bin/env python3

"""Fail-closed audit of the SDO enable_MLDOM configuration copies."""

from __future__ import print_function

import argparse
import os
import re
import sys

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class AuditError(Exception):
    pass


GROUP_PATTERNS = (
    ("CPU", re.compile(r"^system\.cpu(?:\d+)?$")),
    ("RubySystem", re.compile(r"^system\.ruby$")),
    ("L1 controller", re.compile(r"^system\.ruby\.l1_cntrl\d+$")),
    ("Directory controller", re.compile(r"^system\.ruby\.dir_cntrl\d+$")),
)


def _read_bool(parser, section):
    if not parser.has_option(section, "enable_MLDOM"):
        raise AuditError("%s is missing enable_MLDOM" % section)
    raw_value = parser.get(section, "enable_MLDOM").strip().lower()
    if raw_value == "true":
        return True
    if raw_value == "false":
        return False
    raise AuditError(
        "%s has non-canonical enable_MLDOM=%r" % (section, raw_value))


def audit_config(path, expected_enabled):
    if not os.path.isfile(path):
        raise AuditError("config.ini is not a regular file: %s" % path)

    parser = configparser.RawConfigParser()
    try:
        with open(path, "r") as handle:
            parser.read_file(handle)
    except AttributeError:
        with open(path, "r") as handle:
            parser.readfp(handle)
    except (IOError, configparser.Error) as error:
        raise AuditError("could not parse %s: %s" % (path, error))

    checked = []
    sections = parser.sections()
    for group_name, pattern in GROUP_PATTERNS:
        matches = [section for section in sections if pattern.match(section)]
        if not matches:
            raise AuditError("missing %s section" % group_name)
        for section in sorted(matches):
            actual = _read_bool(parser, section)
            if actual != expected_enabled:
                raise AuditError(
                    "%s has enable_MLDOM=%s; expected %s" %
                    (section, str(actual).lower(),
                     str(expected_enabled).lower()))
            checked.append((group_name, section, actual))

    cpu_sections = [
        section for section in sections
        if GROUP_PATTERNS[0][1].match(section)
    ]
    for section in cpu_sections:
        if not parser.has_option(section, "scheme"):
            raise AuditError("%s is missing scheme" % section)
        scheme = parser.get(section, "scheme").strip()
        if expected_enabled and scheme != "SDO":
            raise AuditError(
                "%s has scheme=%r; expected SDO" % (section, scheme))
        if not expected_enabled and scheme == "SDO":
            raise AuditError(
                "%s has scheme=SDO while MLDOM is expected disabled" %
                section)

    return checked


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expect", required=True, choices=("enabled", "disabled"),
        help="required enable_MLDOM value in every audited component")
    parser.add_argument("config_ini", help="gem5 config.ini to audit")
    args = parser.parse_args(argv)

    expected_enabled = args.expect == "enabled"
    try:
        checked = audit_config(args.config_ini, expected_enabled)
    except AuditError as error:
        print("MLDOM_CONFIG_AUDIT FAIL: %s" % error, file=sys.stderr)
        return 1

    for group_name, section, actual in checked:
        print("MLDOM_CONFIG_AUDIT %s %s enable_MLDOM=%s" %
              (group_name, section, str(actual).lower()))
    print("MLDOM_CONFIG_AUDIT PASS expected=%s components=%d" %
          (args.expect, len(checked)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
