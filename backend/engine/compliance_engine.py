"""
compliance_engine.py

The orchestrator. This is the ONLY function other systems (a FastAPI
backend, a CLI, a test suite) need to call:

    result = evaluate_bidder(bidder_data, tender_requirements, government_records)

`bidder_data` is expected to look like whatever the (separately built)
document extractor produces -- a flat-ish nested dict such as:
    {"company_name": ..., "pan": {...}, "gst": {...}, ...}

`tender_requirements` may be either:
  - the full tender dict, e.g. {"tender_id": ..., "requirements": [...]}
  - or just the list of requirement dicts (tender_id will then be taken
    from bidder_data if present, else left as "UNKNOWN").

`government_records` is the mock/real government reference dataset.

Swapping the mock `bidders.json` for the real extractor's output later
requires no changes here, as long as the extractor's output uses the
same field names (documented in data/bidders.json).
"""

from typing import Any, Dict, List, Union

from engine.requirement_checker import (
    FIELD_MISSING,
    check_field_requirement,
    get_nested_value,
)
from engine.government_checker import get_gov_record, get_gov_value, is_blacklisted
from engine.cross_verification import compare_to_government, check_identity_consistency
from engine.scorer import score_results


def _clean(value: Any) -> Any:
    """Turn internal sentinels into JSON-friendly None."""
    return None if value is FIELD_MISSING else value


def _evaluate_blacklist_requirement(requirement: dict, bidder_data: dict, government_records: dict) -> dict:
    identifier_field = requirement.get("gov_identifier_field")
    pan_identifier = get_nested_value(bidder_data, identifier_field) if identifier_field else FIELD_MISSING
    company_name = bidder_data.get("company_name")

    candidate_identifiers = [pan_identifier, company_name]
    blacklisted = is_blacklisted(government_records, candidate_identifiers)

    status = "FAIL" if blacklisted else "PASS"
    reason = (
        "Bidder identifier matches an entry on the government blacklist/debarment list."
        if blacklisted
        else "Bidder does not appear on the government blacklist/debarment list."
    )

    return {
        "status": status,
        "extracted_value": {"pan": _clean(pan_identifier), "company_name": company_name},
        "government_value": "ON_BLACKLIST" if blacklisted else "NOT_ON_BLACKLIST",
        "reason": reason,
    }


def _evaluate_standard_requirement(requirement: dict, bidder_data: dict, government_records: dict) -> dict:
    base = check_field_requirement(requirement, bidder_data)
    source = requirement.get("verification_source")

    # No government source configured for this requirement (e.g. experience
    # years) -- it is purely self-declared and stays as computed.
    if not source:
        return {
            "status": base["status"],
            "extracted_value": _clean(base["extracted_value"]),
            "government_value": None,
            "reason": base["reason"] + " (No independent government verification source configured for this requirement.)"
            if base["status"] != "MISSING"
            else base["reason"],
        }

    # If the bidder's own data is missing, there is nothing to cross-verify.
    if base["status"] == "MISSING":
        return {
            "status": "MISSING",
            "extracted_value": None,
            "government_value": None,
            "reason": base["reason"],
        }

    identifier_field = requirement.get("gov_identifier_field")
    identifier = get_nested_value(bidder_data, identifier_field) if identifier_field else FIELD_MISSING
    gov_record = get_gov_record(government_records, source, identifier)
    gov_value = get_gov_value(gov_record, requirement.get("gov_value_field"))

    comparison = compare_to_government(base["extracted_value"], gov_value)

    if comparison == "GOV_DATA_UNAVAILABLE":
        if base["status"] == "PASS":
            return {
                "status": "REVIEW",
                "extracted_value": _clean(base["extracted_value"]),
                "government_value": None,
                "reason": (
                    f"{base['reason']} However, no matching {source} government record was found "
                    f"for verification (identifier: {identifier!r}), so this requires manual review."
                ),
            }
        # base already FAILed on self-declared data; government data being
        # unavailable doesn't change that.
        return {
            "status": base["status"],
            "extracted_value": _clean(base["extracted_value"]),
            "government_value": None,
            "reason": f"{base['reason']} No matching {source} government record was found to cross-check.",
        }

    if comparison == "MISMATCH":
        if base["status"] == "PASS":
            return {
                "status": "REVIEW",
                "extracted_value": _clean(base["extracted_value"]),
                "government_value": _clean(gov_value),
                "reason": (
                    f"Self-declared data ({base['extracted_value']!r}) satisfies the requirement, but the "
                    f"{source} government record shows a different value ({gov_value!r}). Requires manual review."
                ),
            }
        return {
            "status": base["status"],
            "extracted_value": _clean(base["extracted_value"]),
            "government_value": _clean(gov_value),
            "reason": f"{base['reason']} The {source} government record also shows a differing/non-conforming value ({gov_value!r}).",
        }

    # comparison == "MATCH"
    return {
        "status": base["status"],
        "extracted_value": _clean(base["extracted_value"]),
        "government_value": _clean(gov_value),
        "reason": f"{base['reason']} Confirmed against {source} government record.",
    }


def evaluate_requirement(requirement: dict, bidder_data: dict, government_records: dict) -> dict:
    """Evaluate a single tender requirement against one bidder. Returns a
    fully-formed requirement result dict (see evaluate_bidder for shape)."""
    operator = requirement["operator"]

    if operator == "not_in_blacklist":
        outcome = _evaluate_blacklist_requirement(requirement, bidder_data, government_records)
    elif operator == "name_consistency":
        identity = check_identity_consistency(bidder_data)
        outcome = {
            "status": identity["status"],
            "extracted_value": identity["extracted_value"],
            "government_value": None,
            "reason": identity["reason"],
        }
    else:
        outcome = _evaluate_standard_requirement(requirement, bidder_data, government_records)

    return {
        "requirement_id": requirement["requirement_id"],
        "requirement_name": requirement["requirement_name"],
        "category": requirement.get("category"),
        "mandatory": bool(requirement.get("mandatory", False)),
        "verification_source": requirement.get("verification_source"),
        "status": outcome["status"],
        "extracted_value": outcome["extracted_value"],
        "required_value": requirement.get("value"),
        "government_value": outcome["government_value"],
        "reason": outcome["reason"],
    }


def _extract_requirements_and_tender_id(tender_requirements: Union[dict, list]) -> (str, List[dict]):
    if isinstance(tender_requirements, dict):
        tender_id = tender_requirements.get("tender_id", "UNKNOWN")
        requirements = tender_requirements.get("requirements", [])
    else:
        tender_id = "UNKNOWN"
        requirements = tender_requirements
    return tender_id, requirements


def evaluate_bidder(bidder_data: dict, tender_requirements: Union[dict, list], government_records: dict) -> dict:
    """Evaluate ONE bidder against the tender's requirements and mock/real
    government records. This is the single public entry point of the
    engine, designed to be called the same way whether the data comes
    from mock JSON files or a real document extractor / FastAPI request.
    """
    tender_id, requirements = _extract_requirements_and_tender_id(tender_requirements)

    requirement_results = [
        evaluate_requirement(req, bidder_data, government_records) for req in requirements
    ]

    scoring = score_results(requirement_results)

    return {
        "company_name": bidder_data.get("company_name", "UNKNOWN"),
        "tender_id": tender_id,
        "compliance_percentage": scoring["compliance_percentage"],
        "summary": scoring["summary"],
        "mandatory_failure": scoring["mandatory_failure"],
        "mandatory_missing": scoring["mandatory_missing"],
        "overall_status": scoring["overall_status"],
        "requirements": requirement_results,
    }


def evaluate_all_bidders(bidders: List[dict], tender_requirements: Union[dict, list], government_records: dict) -> List[dict]:
    """Convenience wrapper: evaluate a list of bidders in one call."""
    return [evaluate_bidder(bidder, tender_requirements, government_records) for bidder in bidders]
