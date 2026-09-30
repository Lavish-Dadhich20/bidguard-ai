"""
Automated tests for the BidGuard AI compliance engine.

Run from the project root with either:
    python -m unittest discover -s tests -v
or, if pytest is installed:
    pytest tests/ -v
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.compliance_engine import evaluate_bidder, evaluate_all_bidders
from engine.requirement_checker import apply_operator, get_nested_value, FIELD_MISSING
from engine.cross_verification import normalize_name, compare_to_government
from engine.government_checker import is_blacklisted

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)


def req_status(result, requirement_id):
    for req in result["requirements"]:
        if req["requirement_id"] == requirement_id:
            return req["status"]
    raise AssertionError(f"Requirement {requirement_id} not found in result")


class TestOperators(unittest.TestCase):
    """Unit tests for the deterministic, rule-based comparison logic."""

    def test_equality_is_case_insensitive(self):
        self.assertTrue(apply_operator("==", "active", "ACTIVE"))
        self.assertFalse(apply_operator("==", "inactive", "ACTIVE"))

    def test_numeric_operators(self):
        self.assertTrue(apply_operator(">=", 50000000, 50000000))
        self.assertTrue(apply_operator(">=", 72000000, 50000000))
        self.assertFalse(apply_operator(">=", 32000000, 50000000))
        self.assertTrue(apply_operator("<", 2, 3))

    def test_boolean_operator(self):
        self.assertTrue(apply_operator("boolean", True, True))
        self.assertFalse(apply_operator("boolean", False, True))

    def test_contains_operator(self):
        self.assertTrue(apply_operator("contains", "Supply of Industrial Equipment", "industrial"))

    def test_get_nested_value_missing_path(self):
        self.assertIs(get_nested_value({"a": {"b": 1}}, "a.c"), FIELD_MISSING)
        self.assertEqual(get_nested_value({"a": {"b": 1}}, "a.b"), 1)

    def test_normalize_name_strips_punctuation_not_abbreviations(self):
        self.assertEqual(normalize_name("Deccan Metalworks Pvt. Ltd."), "DECCAN METALWORKS PVT LTD")
        self.assertNotEqual(normalize_name("XYZ Ltd"), normalize_name("XYZ Limited"))

    def test_compare_to_government_unavailable(self):
        self.assertEqual(compare_to_government("ACTIVE", FIELD_MISSING), "GOV_DATA_UNAVAILABLE")

    def test_is_blacklisted(self):
        gov = {"BLACKLIST": ["ABCDE1234F"]}
        self.assertTrue(is_blacklisted(gov, ["abcde1234f"]))
        self.assertFalse(is_blacklisted(gov, ["ZZZZZ9999Z"]))


class TestComplianceEngineScenarios(unittest.TestCase):
    """End-to-end tests, one per required test scenario, run against the
    project's own mock dataset in data/."""

    @classmethod
    def setUpClass(cls):
        cls.tender = load_json("tender_requirements.json")
        cls.bidders = {b["company_name"]: b for b in load_json("bidders.json")}
        cls.gov = load_json("government_records.json")
        cls.results = {
            name: evaluate_bidder(data, cls.tender, cls.gov)
            for name, data in cls.bidders.items()
        }

    # 1. Fully compliant bidder -> PASS on every mandatory requirement
    def test_fully_compliant_bidder(self):
        result = self.results["Alpha Engineering Works Pvt Ltd"]
        self.assertEqual(result["overall_status"], "COMPLIANT")
        self.assertFalse(result["mandatory_failure"])
        self.assertEqual(result["summary"]["fail"], 0)
        self.assertEqual(result["summary"]["missing"], 0)
        self.assertEqual(result["compliance_percentage"], 100.0)

    # 2. Turnover below threshold -> FAIL
    def test_turnover_below_threshold_fails(self):
        result = self.results["Bharat Precision Tools Ltd"]
        self.assertEqual(req_status(result, "REQ-004"), "FAIL")
        self.assertTrue(result["mandatory_failure"])
        self.assertEqual(result["overall_status"], "NON_COMPLIANT_MANDATORY_FAILURE")

    # 3. GST inactive -> FAIL
    def test_gst_inactive_fails(self):
        result = self.results["Chandra Fabrication Industries Pvt Ltd"]
        self.assertEqual(req_status(result, "REQ-001"), "FAIL")
        self.assertTrue(result["mandatory_failure"])

    # 4. Legal-name mismatch -> REVIEW (not an automatic fail)
    def test_legal_name_mismatch_review(self):
        result = self.results["Deccan Metal Works Pvt Ltd"]
        self.assertEqual(req_status(result, "REQ-013"), "REVIEW")
        # Udyam status itself is fine and verified -> still PASS
        self.assertEqual(req_status(result, "REQ-003"), "PASS")
        self.assertFalse(result["mandatory_failure"])
        self.assertEqual(result["overall_status"], "NEEDS_MANUAL_REVIEW")

    # 5. Missing required information -> MISSING
    def test_missing_oem_data(self):
        result = self.results["Everest Heavy Machinery Ltd"]
        self.assertEqual(req_status(result, "REQ-009"), "MISSING")
        self.assertTrue(result["mandatory_missing"])
        self.assertEqual(result["overall_status"], "INCOMPLETE_MANDATORY_DATA_MISSING")

    # 6. Local content below threshold -> FAIL
    def test_local_content_below_threshold_fails(self):
        result = self.results["Fortune Industrial Solutions Pvt Ltd"]
        self.assertEqual(req_status(result, "REQ-008"), "FAIL")
        self.assertTrue(result["mandatory_failure"])

    # 7. Blacklisted bidder -> FAIL, and must stay visible despite a high score
    def test_blacklisted_bidder_fails_regardless_of_score(self):
        result = self.results["Ganga Steel & Allied Industries Limited"]
        self.assertEqual(req_status(result, "REQ-010"), "FAIL")
        self.assertTrue(result["mandatory_failure"])
        self.assertGreaterEqual(result["compliance_percentage"], 90.0)  # high score
        self.assertEqual(result["overall_status"], "NON_COMPLIANT_MANDATORY_FAILURE")

    # 8. Government data mismatch / unavailable -> REVIEW
    def test_government_record_unavailable_triggers_review(self):
        result = self.results["Hind Auto Components Pvt Ltd"]
        self.assertEqual(req_status(result, "REQ-006"), "REVIEW")
        self.assertFalse(result["mandatory_failure"])
        self.assertEqual(result["overall_status"], "NEEDS_MANUAL_REVIEW")

    # 9. Multiple issues at once
    def test_multiple_inconsistencies(self):
        result = self.results["Indus Global Manufacturing Pvt Ltd"]
        self.assertEqual(req_status(result, "REQ-001"), "REVIEW")   # GST mismatch vs gov
        self.assertEqual(req_status(result, "REQ-004"), "REVIEW")   # turnover mismatch vs gov
        self.assertEqual(req_status(result, "REQ-007"), "MISSING")  # ESIC not provided
        self.assertEqual(req_status(result, "REQ-008"), "FAIL")     # local content too low
        self.assertEqual(req_status(result, "REQ-013"), "REVIEW")   # name mismatch
        self.assertTrue(result["mandatory_failure"])

    # 10. Compliant bidder with one non-critical review item
    def test_compliant_with_one_review_item(self):
        result = self.results["Jaipur Precision Castings Ltd"]
        self.assertFalse(result["mandatory_failure"])
        self.assertEqual(result["summary"]["fail"], 0)
        self.assertEqual(result["summary"]["missing"], 0)
        self.assertEqual(result["summary"]["review"], 1)
        self.assertEqual(req_status(result, "REQ-013"), "REVIEW")
        self.assertEqual(result["overall_status"], "NEEDS_MANUAL_REVIEW")

    def test_evaluate_all_bidders_returns_one_result_per_bidder(self):
        all_results = evaluate_all_bidders(list(self.bidders.values()), self.tender, self.gov)
        self.assertEqual(len(all_results), 10)
        self.assertEqual({r["tender_id"] for r in all_results}, {"TDR-DEMO-001"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
