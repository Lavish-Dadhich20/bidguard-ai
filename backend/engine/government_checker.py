"""
government_checker.py

Helpers for looking up the mock government/reference verification data
(GST, PAN, UDYAM, EPFO, ESIC, MCA, TURNOVER, OEM, MAKE_IN_INDIA, ITR,
BLACKLIST) that a real system would receive from official sources.

This module never decides PASS/FAIL by itself -- it only *fetches*
government-side values and *decides* whether a given bidder identifier
appears on the blacklist. The comparison logic against bidder-declared
data lives in cross_verification.py.
"""

from typing import Any, Optional

from engine.requirement_checker import get_nested_value, FIELD_MISSING


def get_gov_record(government_records: dict, source: Optional[str], identifier: Any) -> Optional[dict]:
    """Look up the government record for `source` (e.g. "GST") keyed by
    `identifier` (e.g. a GSTIN or PAN number).

    Returns None if the source is unknown, the identifier is missing/
    unusable, or there is simply no record for that identifier --
    which is exactly the "cannot verify with government data" case.
    """
    if not source:
        return None
    if identifier is FIELD_MISSING or identifier is None:
        return None

    # A provider object (e.g. SupabaseProvider) instead of a plain dict
    if not isinstance(government_records, dict):
        return government_records.get_record(source, identifier)

    source_table = government_records.get(source)
    if not isinstance(source_table, dict):
        return None

    return source_table.get(identifier)


def get_gov_value(gov_record: Optional[dict], gov_value_field: Optional[str]) -> Any:
    """Pull a specific field out of a government record dict."""
    if gov_record is None or not gov_value_field:
        return FIELD_MISSING
    return get_nested_value(gov_record, gov_value_field) if "." in gov_value_field else gov_record.get(
        gov_value_field, FIELD_MISSING
    )


def _normalize_identifier(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def is_blacklisted(government_records: dict, identifiers: list) -> bool:
    """Check whether any of the given identifiers (PAN number, company
    name, GSTIN, etc.) appears on the government BLACKLIST/debarment
    list. Comparison is exact (case/whitespace-insensitive) on purpose --
    blacklist decisions should never rest on fuzzy matching.
    """
    if not isinstance(government_records, dict):
        return government_records.is_blacklisted(
            [i for i in identifiers if i is not FIELD_MISSING and i is not None]
        )

    blacklist = government_records.get("BLACKLIST", [])
    normalized_blacklist = {_normalize_identifier(entry) for entry in blacklist}

    for identifier in identifiers:
        if identifier is FIELD_MISSING or identifier is None:
            continue
        if _normalize_identifier(identifier) in normalized_blacklist:
            return True
    return False
