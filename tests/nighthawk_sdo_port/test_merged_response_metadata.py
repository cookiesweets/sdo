#!/usr/bin/env python
#
# Source-contract tests for the MESI_Two_Level SDO merged-response path.
#
# Keep this file compatible with Python 2.7 and Python 3.5: standard library
# only, no annotations, no f-strings, and no newer unittest helpers.

from __future__ import print_function

import io
import os
import re
import unittest
from collections import Counter, namedtuple


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(TEST_DIR, os.pardir, os.pardir))

SEQUENCER_PATH = os.path.join(
    REPO_ROOT, "src", "mem", "ruby", "system", "Sequencer.cc")
PACKET_PATH = os.path.join(REPO_ROOT, "src", "mem", "packet.hh")
LOC_PRED_PATH = os.path.join(REPO_ROOT, "src", "cpu", "o3", "locPred.hh")
LSQ_UNIT_PATH = os.path.join(REPO_ROOT, "src", "cpu", "o3", "lsq_unit.hh")


Region = namedtuple(
    "Region", ["start", "open_brace", "end", "text", "code"])


class ContractExtractionError(AssertionError):
    pass


def read_source(path):
    try:
        with io.open(path, "r", encoding="utf-8") as source_file:
            return source_file.read()
    except IOError as error:
        raise ContractExtractionError(
            "cannot read required source {0}: {1}".format(path, error))


def mask_cpp_noncode(source):
    """Replace comments and literals with spaces while preserving offsets."""
    result = list(source)
    state = "code"
    index = 0

    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""

        if state == "code":
            if char == "/" and next_char == "/":
                result[index] = " "
                result[index + 1] = " "
                state = "line_comment"
                index += 2
                continue
            if char == "/" and next_char == "*":
                result[index] = " "
                result[index + 1] = " "
                state = "block_comment"
                index += 2
                continue
            if char == '"':
                result[index] = " "
                state = "string"
                index += 1
                continue
            if char == "'":
                result[index] = " "
                state = "char"
                index += 1
                continue
            index += 1
            continue

        if state == "line_comment":
            if char == "\n":
                state = "code"
            else:
                result[index] = " "
            index += 1
            continue

        if state == "block_comment":
            if char == "*" and next_char == "/":
                result[index] = " "
                result[index + 1] = " "
                state = "code"
                index += 2
                continue
            if char != "\n":
                result[index] = " "
            index += 1
            continue

        if state == "string" or state == "char":
            terminator = '"' if state == "string" else "'"
            if char == "\\":
                result[index] = " "
                if index + 1 < len(source):
                    if source[index + 1] != "\n":
                        result[index + 1] = " "
                    index += 2
                else:
                    index += 1
                continue
            if char == terminator:
                result[index] = " "
                state = "code"
                index += 1
                continue
            if char != "\n":
                result[index] = " "
            index += 1
            continue

    if state == "block_comment":
        raise ContractExtractionError("unterminated C-style block comment")
    if state == "string" or state == "char":
        raise ContractExtractionError(
            "unterminated C/C++ literal while extracting source")

    return "".join(result)


def matching_brace(masked_source, open_brace, label):
    if open_brace < 0 or masked_source[open_brace] != "{":
        raise ContractExtractionError(
            "{0}: extraction did not start at an opening brace".format(label))

    depth = 0
    for index in range(open_brace, len(masked_source)):
        char = masked_source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index

    raise ContractExtractionError(
        "{0}: opening brace has no matching closing brace".format(label))


def regions_for_pattern(source, pattern, label):
    """Extract every balanced definition/block beginning with pattern."""
    masked_source = mask_cpp_noncode(source)
    matches = list(re.finditer(pattern, masked_source, re.MULTILINE | re.DOTALL))
    if not matches:
        raise ContractExtractionError(
            "{0}: semantic anchor was not found: {1}".format(label, pattern))

    regions = []
    for match in matches:
        open_brace = masked_source.find("{", match.end())
        if open_brace < 0:
            raise ContractExtractionError(
                "{0}: anchor has no following body".format(label))

        # A declaration ending before the next brace is not a definition.
        semicolon = masked_source.find(";", match.end(), open_brace)
        if semicolon >= 0:
            continue

        close_brace = matching_brace(masked_source, open_brace, label)
        regions.append(Region(
            match.start(),
            open_brace,
            close_brace + 1,
            source[match.start():close_brace + 1],
            masked_source[match.start():close_brace + 1]))

    if not regions:
        raise ContractExtractionError(
            "{0}: anchors were declarations rather than definitions".format(
                label))
    return regions


def one_region(source, pattern, label):
    regions = regions_for_pattern(source, pattern, label)
    if len(regions) != 1:
        raise ContractExtractionError(
            "{0}: expected one bounded region, found {1}".format(
                label, len(regions)))
    return regions[0]


def nested_region(region, pattern, label):
    return one_region(region.text, pattern, label)


def require_pattern(test_case, code, pattern, message):
    match = re.search(pattern, code, re.MULTILINE | re.DOTALL)
    test_case.assertIsNotNone(match, message)
    return match


def require_order(test_case, code, labelled_patterns, context):
    cursor = 0
    positions = []
    for label, pattern in labelled_patterns:
        match = re.search(
            pattern, code[cursor:], re.MULTILINE | re.DOTALL)
        test_case.assertIsNotNone(
            match,
            "{0}: missing or out-of-order semantic marker '{1}'".format(
                context, label))
        absolute_position = cursor + match.start()
        positions.append(absolute_position)
        cursor += match.end()
    return positions


class MergedResponseMetadataContractTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sequencer = read_source(SEQUENCER_PATH)
        cls.packet = read_source(PACKET_PATH)
        cls.loc_pred = read_source(LOC_PRED_PATH)
        cls.lsq_unit = read_source(LSQ_UNIT_PATH)

        cls.insert_specld = one_region(
            cls.sequencer,
            r"\bSequencer::insertSpecldRequest\s*\(",
            "Sequencer::insertSpecldRequest")
        cls.alias_block = nested_region(
            cls.insert_specld,
            r"\bif\s*\(\s*pkt->aliased_reqIdx\s*>\s*0\s*\)",
            "aliased_reqIdx merge block")
        cls.alias_match_block = nested_region(
            cls.alias_block,
            r"\bif\s*\(\s*specld_key\.second\s*==\s*aliased_ld_idx\s*\)",
            "matching older speculative request")

        cls.normal_read_callback = one_region(
            cls.sequencer,
            r"\bSequencer::readCallback\s*\(\s*"
            r"Addr\s+address\s*,\s*DataBlock&\s+data\s*,\s*"
            r"bool\s+externalHit\s*,\s*const\s+bool\s+hitAtL0\s*,\s*"
            r"const\s+bool\s+hitAtL1\s*,\s*"
            r"const\s+bool\s+hitAtMem\s*,",
            "normal-load response readCallback")

    def test_merge_return_is_nested_in_matching_older_request(self):
        require_pattern(
            self,
            self.alias_block.code,
            r"\baliased_ld_idx\s*=\s*pkt->aliased_reqIdx\s*\*\s*2\s*;",
            "aliased_reqIdx must be converted to the outstanding split-load "
            "index before searching")

        require_order(
            self,
            self.alias_match_block.code,
            [
                ("attach dependent packet",
                 r"\bspecld_req->dependentRequests\.push_back\s*\(\s*pkt\s*\)"
                 r"\s*;"),
                ("return merged status",
                 r"\breturn\s+RequestStatus_Merged\s*;"),
            ],
            "matching older speculative request")

        active_returns = re.findall(
            r"\breturn\s+RequestStatus_Merged\s*;",
            self.alias_block.code)
        self.assertEqual(
            len(active_returns),
            1,
            "aliased_reqIdx block must have exactly one active Merged return, "
            "nested in the actual key-match branch; commented legacy returns "
            "must not count")
        self.assertEqual(
            len(re.findall(
                r"\breturn\s+RequestStatus_Merged\s*;",
                self.alias_match_block.code)),
            1,
            "the sole active Merged return must remain inside the branch that "
            "found and attached to an older request")

    def test_merge_miss_falls_through_to_fresh_allocation(self):
        tail = self.insert_specld.code[self.alias_block.end:]
        allocation = require_pattern(
            self,
            tail,
            r"\bSequencerRequest\s*\*\s*new_seq_req\s*=\s*"
            r"new\s+SequencerRequest\s*\(",
            "a missed aliased_reqIdx lookup must reach fresh request "
            "allocation")

        before_allocation = tail[:allocation.start()]
        self.assertIsNone(
            re.search(
                r"\breturn\s+RequestStatus_(?:Merged|Aliased)\s*;",
                before_allocation),
            "after the aliased_reqIdx search misses, no unconditional "
            "Merged/Aliased return may prevent fresh allocation")

        require_order(
            self,
            tail,
            [
                ("allocate SequencerRequest",
                 r"\bnew_seq_req\s*=\s*new\s+SequencerRequest\s*\("),
                ("insert into speculative request table",
                 r"\bm_specldRequestTable\.insert\s*\("),
                ("increment outstanding count",
                 r"\bm_outstanding_count\s*\+\+\s*;"),
                ("report ready",
                 r"\breturn\s+RequestStatus_Ready\s*;"),
            ],
            "fresh speculative request path")

    def test_packet_clearer_resets_every_exclusive_hit_flag(self):
        clear_method = one_region(
            self.packet,
            r"\bvoid\s+clearMLDOMHitStatus\s*\(\s*\)",
            "Packet::clearMLDOMHitStatus")

        assignments = re.findall(
            r"\b(isSBHit|isL0Hit|isL1Hit|isMemHit)\s*=\s*(true|false)\s*;",
            clear_method.code)
        self.assertEqual(
            Counter(assignments),
            Counter([
                ("isSBHit", "false"),
                ("isL0Hit", "false"),
                ("isL1Hit", "false"),
                ("isMemHit", "false"),
            ]),
            "clearMLDOMHitStatus must clear each mutually-exclusive SDO hit "
            "flag exactly once and must not set any hit flag")

    def test_normal_ld_callback_replaces_dependent_response_metadata(self):
        callback_level = one_region(
            self.sequencer,
            r"\bint\s+callbackSDOHitLevel\s*\(",
            "callbackSDOHitLevel")
        require_order(
            self,
            callback_level.code,
            [
                ("L0 response maps to level 0",
                 r"\bif\s*\(\s*hitAtL0\s*\)\s*return\s+0\s*;"),
                ("L1 response maps to level 1",
                 r"\bif\s*\(\s*hitAtL1\s*\)\s*return\s+1\s*;"),
                ("memory response maps to level 3",
                 r"\bif\s*\(\s*hitAtMem\s*\)\s*return\s+3\s*;"),
            ],
            "actual callback hit-level priority")

        overwrite = one_region(
            self.sequencer,
            r"\bvoid\s+overwriteSDOHitLevel\s*\(",
            "overwriteSDOHitLevel")
        require_order(
            self,
            overwrite.code,
            [
                ("clear stale mutually-exclusive flags",
                 r"\bpkt->clearMLDOMHitStatus\s*\(\s*\)\s*;"),
                ("overwrite visible fromLevel",
                 r"\bpkt->fromLevel\s*=\s*"
                 r"visibleSDOLevel\s*\(\s*rubyLevel\s*\)\s*;"),
                ("set exactly the actual response hit level",
                 r"\bmarkSDOHitLevel\s*\(\s*pkt\s*,\s*rubyLevel\s*\)\s*;"),
            ],
            "dependent response metadata overwrite helper")

        mark_level = one_region(
            self.sequencer,
            r"\bvoid\s+markSDOHitLevel\s*\(",
            "markSDOHitLevel")
        for level, setter in (("0", "setL0_Hit"),
                              ("1", "setL1_Hit"),
                              ("3", "setMem_Hit")):
            require_pattern(
                self,
                mark_level.code,
                r"\bcase\s+{0}\s*:\s*pkt->{1}\s*\(\s*\)\s*;\s*"
                r"break\s*;".format(level, setter),
                "markSDOHitLevel must map visible level {0} only through "
                "{1}".format(level, setter))

        require_order(
            self,
            self.normal_read_callback.code,
            [
                ("derive level from actual callback booleans",
                 r"\bconst\s+int\s+responseLevel\s*=\s*"
                 r"callbackSDOHitLevel\s*\(\s*hitAtL0\s*,\s*"
                 r"hitAtL1\s*,\s*hitAtMem\s*\)\s*;"),
                ("enter normal-LD merged-response path",
                 r"\bif\s*\(\s*RubySystem::getMLDOMEnabled\s*\(\s*\)\s*"
                 r"&&\s*request->m_type\s*==\s*RubyRequestType_LD\s*\)"),
            ],
            "normal read callback")

        normal_ld_block = nested_region(
            self.normal_read_callback,
            r"\bif\s*\(\s*RubySystem::getMLDOMEnabled\s*\(\s*\)\s*"
            r"&&\s*request->m_type\s*==\s*RubyRequestType_LD\s*\)",
            "MLDOM normal-LD dependent callback block")
        dependent_loop = nested_region(
            normal_ld_block,
            r"\bfor\s*\(\s*auto&\s+dependentPkt\s*:\s*"
            r"request->dependentRequests\s*\)",
            "normal-LD dependent packet loop")

        positions = require_order(
            self,
            dependent_loop.code,
            [
                ("force final callback",
                 r"\bdependentPkt->isFinalPacket\s*=\s*true\s*;"),
                ("replace stale metadata",
                 r"\boverwriteSDOHitLevel\s*\(\s*dependentPkt\s*,\s*"
                 r"responseLevel\s*\)\s*;"),
                ("dispatch dependent packet",
                 r"\bruby_hit_callback\s*\(\s*dependentPkt\s*\)\s*;"),
            ],
            "normal-LD dependent packet callback")
        type_branch = require_pattern(
            self,
            dependent_loop.code,
            r"\bif\s*\(\s*dependentPkt->isExpose\s*\(\s*\)\s*\)",
            "metadata replacement must apply before dependent packet type "
            "dispatch")
        self.assertLess(
            positions[1],
            type_branch.start(),
            "all dependent packet kinds must receive replaced response "
            "metadata before expose/validate/spec dispatch")

    def test_logical_and_physical_two_level_fold_contract(self):
        enum_fold = one_region(
            self.loc_pred,
            r"\binline\s+CacheLevel_t\s+"
            r"foldCacheLevelForTwoLevelSDO\s*\(\s*CacheLevel_t\s+level\s*\)",
            "typed Two-Level predictor fold")
        int_fold = one_region(
            self.loc_pred,
            r"\binline\s+int\s+"
            r"foldCacheLevelForTwoLevelSDO\s*\(\s*int\s+level\s*\)",
            "integer Two-Level predictor fold")

        fold_pattern = (
            r"\breturn\s+level\s*==\s*Cache_L3\s*\?\s*"
            r"Cache_L2\s*:\s*level\s*;")
        require_pattern(
            self, enum_fold.code, fold_pattern,
            "typed predictor fold must map legacy logical L2 Cache_L3 to "
            "the shared-cache Cache_L2 target and preserve all other levels")
        require_pattern(
            self, int_fold.code, fold_pattern,
            "integer predictor fold must match the typed fold rule")

        lsq_read = one_region(
            self.lsq_unit,
            r"\bLSQUnit<Impl>::read\s*\(",
            "LSQUnit::read")
        predictor_blocks = regions_for_pattern(
            lsq_read.text,
            r"\bif\s*\(\s*cpu->enableMLDOM\s*\)",
            "MLDOM blocks in LSQUnit::read")
        predictor_blocks = [
            block for block in predictor_blocks
            if re.search(r"\blocationPredictor->predict\s*\(", block.code)
        ]
        self.assertEqual(
            len(predictor_blocks),
            1,
            "LSQUnit::read must have one bounded MLDOM prediction block")
        predictor_block = predictor_blocks[0]
        require_order(
            self,
            predictor_block.code,
            [
                ("obtain prediction",
                 r"\bload_inst->pred_level\s*=\s*"
                 r"cpu->locationPredictor->predict\s*\("),
                ("fold before packet issue",
                 r"\bfolded_pred_level\s*=\s*"
                 r"foldCacheLevelForTwoLevelSDO\s*\(\s*"
                 r"load_inst->pred_level\s*\)\s*;"),
                ("store folded prediction",
                 r"\bload_inst->pred_level\s*=\s*folded_pred_level\s*;"),
            ],
            "LSQ predictor-to-packet fold")

        issue_switches = regions_for_pattern(
            lsq_read.text,
            r"\bswitch\s*\(\s*load_inst->pred_level\s*\)",
            "SDO packet target switch")
        self.assertEqual(
            len(issue_switches),
            2,
            "LSQUnit::read must apply the same target fold to aligned and "
            "split-load packet creation")
        for issue_switch in issue_switches:
            require_pattern(
                self,
                issue_switch.code,
                r"\bcase\s+Cache_L1\s*:[^{}]*"
                r"Packet::createReadSpecL0\s*\(",
                "logical L0 must issue to the private physical L1 target")
            require_pattern(
                self,
                issue_switch.code,
                r"\bcase\s+Cache_L2\s*:[^{}]*"
                r"Packet::createReadSpecL1\s*\(",
                "folded logical L1/L2 must issue to the shared physical L2 "
                "target")
            self.assertIsNone(
                re.search(r"\bcase\s+Cache_L3\s*:", issue_switch.code),
                "the active Two-Level packet switch must not expose a "
                "separate legacy logical-L2 target after folding")

        l2_wrappers = regions_for_pattern(
            self.sequencer,
            r"\bSequencer::readCallback\s*\(\s*"
            r"Addr\s+address\s*,\s*DataBlock&\s+data\s*,\s*"
            r"const\s+bool\s+externalHit\s*,\s*"
            r"const\s+bool\s+hitAtL0\s*,\s*"
            r"const\s+bool\s+hitAtL1\s*,\s*"
            r"const\s+bool\s+hitAtL2\s*,",
            "physical-L2 readCallback wrappers")
        self.assertEqual(
            len(l2_wrappers),
            3,
            "all three hit-metadata readCallback overloads must expose the "
            "same physical-L2 fold")
        for wrapper in l2_wrappers:
            require_pattern(
                self,
                wrapper.code,
                r"\breadCallback\s*\([^;{}]*"
                r"hitAtL1\s*\|\|\s*hitAtL2\s*,",
                "a physical L2 hit must be folded into the logical shared "
                "cache hit before the main callback")

        visible_level = one_region(
            self.sequencer,
            r"\bint\s+visibleSDOLevel\s*\(",
            "visibleSDOLevel")
        require_pattern(
            self,
            visible_level.code,
            r"\breturn\s+rubyLevel\s*==\s*2\s*\?\s*3\s*:\s*"
            r"rubyLevel\s*;",
            "the internal lower-level Ruby response code 2 must be exposed "
            "as SDO memory level 3, leaving visible levels 0/1/3")


if __name__ == "__main__":
    unittest.main(verbosity=2)
