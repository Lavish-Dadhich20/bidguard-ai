"""
scorer.py

Turns a list of per-requirement results into a transparent summary and
compliance percentage.

Important design rule from the project brief: the score is NEVER the
final eligibility decision by itself. A failed mandatory requirement
must stay clearly flagged (mandatory_failure = true) even when the
percentage looks high, and it is left to the tender's own rules /
a human reviewer to decide what to do with that.
"""

from typing import List, Dict


def score_results(requirement_results: List[Dict]) -> Dict:
    total = len(requirement_results)
    pass_count = sum(1 for r in requirement_results if r["status"] == "PASS")
    fail_count = sum(1 for r in requirement_results if r["status"] == "FAIL")
    review_count = sum(1 for r in requirement_results if r["status"] == "REVIEW")
    missing_count = sum(1 for r in requirement_results if r["status"] == "MISSING")

    compliance_percentage = round((pass_count / total) * 100, 2) if total else 0.0

    mandatory_failure = any(r["mandatory"] and r["status"] == "FAIL" for r in requirement_results)
    mandatory_missing = any(r["mandatory"] and r["status"] == "MISSING" for r in requirement_results)
    mandatory_review = any(r["mandatory"] and r["status"] == "REVIEW" for r in requirement_results)

    if mandatory_failure:
        overall_status = "NON_COMPLIANT_MANDATORY_FAILURE"
    elif mandatory_missing:
        overall_status = "INCOMPLETE_MANDATORY_DATA_MISSING"
    elif mandatory_review or review_count > 0:
        overall_status = "NEEDS_MANUAL_REVIEW"
    else:
        overall_status = "COMPLIANT"

    return {
        "compliance_percentage": compliance_percentage,
        "summary": {
            "pass": pass_count,
            "fail": fail_count,
            "review": review_count,
            "missing": missing_count,
            "total_requirements": total,
        },
        "mandatory_failure": mandatory_failure,
        "mandatory_missing": mandatory_missing,
        "overall_status": overall_status,
    }
