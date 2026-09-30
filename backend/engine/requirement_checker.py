"""
requirement_checker.py

Pure, deterministic helpers for:
  1. Reading a dotted field path (e.g. "gst.status") out of a bidder's
     structured data.
  2. Applying a comparison operator (==, >=, contains, boolean, ...)
     between the extracted value and the value/threshold required by a
     tender requirement.

No AI/ML is used here on purpose -- comparisons like "turnover >= 5 crore"
are simple, explainable, deterministic rules and should stay that way.
"""

from typing import Any


class FieldMissing:
    """Sentinel returned when a required field does not exist in the
    bidder's extracted data at all (as opposed to being present but
    falsy, e.g. 0 or False)."""

    def __repr__(self) -> str:
        return "<FIELD_MISSING>"


FIELD_MISSING = FieldMissing()


def get_nested_value(data: dict, dotted_path: str) -> Any:
    """Fetch data["a"]["b"] for dotted_path == "a.b".

    Returns FIELD_MISSING if any key along the path does not exist,
    or if an intermediate value is not a dict.
    """
    if not dotted_path:
        return FIELD_MISSING

    current: Any = data
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            return FIELD_MISSING
        current = current[key]
    return current


SUPPORTED_OPERATORS = {
    "==", "!=", ">", ">=", "<", "<=", "contains", "boolean", "status_match",
}


def apply_operator(operator: str, actual: Any, expected: Any) -> bool:
    """Evaluate `actual <operator> expected` deterministically.

    Raises ValueError for an unsupported operator, and TypeError-safe
    comparisons return False instead of crashing (e.g. comparing None
    with a number) so the caller can turn that into a MISSING/REVIEW
    result instead of an unhandled exception.
    """
    if operator not in SUPPORTED_OPERATORS:
        raise ValueError(f"Unsupported operator: {operator!r}")

    try:
        if operator == "==":
            return _normalize(actual) == _normalize(expected)
        if operator == "!=":
            return _normalize(actual) != _normalize(expected)
        if operator == ">":
            return float(actual) > float(expected)
        if operator == ">=":
            return float(actual) >= float(expected)
        if operator == "<":
            return float(actual) < float(expected)
        if operator == "<=":
            return float(actual) <= float(expected)
        if operator == "contains":
            return str(expected).strip().lower() in str(actual).strip().lower()
        if operator == "boolean":
            return bool(actual) == bool(expected)
        if operator == "status_match":
            return _normalize(actual) == _normalize(expected)
    except (TypeError, ValueError):
        return False

    return False


def _normalize(value: Any) -> Any:
    """Case/whitespace-insensitive normalization for string comparisons
    so 'active' and 'ACTIVE ' are treated the same."""
    if isinstance(value, str):
        return value.strip().upper()
    return value


def check_field_requirement(requirement: dict, bidder_data: dict) -> dict:
    """Evaluate a single "field_to_check" style requirement purely against
    the bidder's own self-declared/extracted data (no government
    cross-check here -- that happens later in the pipeline).

    Returns a dict with:
        status: "PASS" | "FAIL" | "MISSING"
        extracted_value: the value found (or None if missing)
        reason: human-readable explanation
    """
    field_path = requirement["field_to_check"]
    operator = requirement["operator"]
    expected = requirement.get("value")

    actual = get_nested_value(bidder_data, field_path)

    if actual is FIELD_MISSING:
        return {
            "status": "MISSING",
            "extracted_value": None,
            "reason": (
                f"Required field '{field_path}' was not found in the "
                f"extracted bidder data. This document/data point may not "
                f"have been submitted or the extractor could not read it."
            ),
        }

    passed = apply_operator(operator, actual, expected)
    if passed:
        reason = f"'{field_path}' = {actual!r} satisfies the requirement ({operator} {expected!r})."
    else:
        reason = f"'{field_path}' = {actual!r} does NOT satisfy the requirement ({operator} {expected!r})."

    return {
        "status": "PASS" if passed else "FAIL",
        "extracted_value": actual,
        "reason": reason,
    }
