"""
cross_verification.py

Deliberately simple, explainable consistency checks:

  1. compare_to_government(): does a bidder-declared value match what
     the (mock) government/reference source says?
  2. check_identity_consistency(): do the legal names on PAN / GST /
     Udyam / Certificate of Incorporation all refer to the same entity?

Per the project brief: fuzzy string matching is NOT used to declare a
company compliant. Names are normalized (case, punctuation, whitespace)
and then compared exactly. If they don't match after normalization, the
result is REVIEW (human judgement needed) -- never an automatic PASS,
and never an automatic FAIL either, since a genuine clerical/formatting
difference is common and not proof of fraud.
"""

import re
from typing import Any, Optional

from engine.requirement_checker import FIELD_MISSING, get_nested_value


def normalize_name(name: Any) -> Optional[str]:
    """Normalize a legal name for comparison: uppercase, collapse
    whitespace, and strip punctuation (periods, commas, ampersands-as-
    words are kept as characters but standalone punctuation is removed).
    This is normalization, NOT fuzzy/similarity matching -- it does not
    expand abbreviations like 'Ltd' -> 'Limited'.
    """
    if not name or name is FIELD_MISSING or not isinstance(name, str):
        return None
    cleaned = re.sub(r"[.,]", "", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().upper()
    return cleaned or None


def compare_to_government(bidder_value: Any, gov_value: Any) -> str:
    """Compare a bidder-declared value against the government/reference
    value for the same field.

    Returns one of: "MATCH", "MISMATCH", "GOV_DATA_UNAVAILABLE"
    """
    if gov_value is FIELD_MISSING or gov_value is None:
        return "GOV_DATA_UNAVAILABLE"

    if isinstance(bidder_value, str) or isinstance(gov_value, str):
        b = str(bidder_value).strip().upper() if bidder_value is not None else ""
        g = str(gov_value).strip().upper() if gov_value is not None else ""
        return "MATCH" if b == g else "MISMATCH"

    if isinstance(bidder_value, bool) or isinstance(gov_value, bool):
        return "MATCH" if bool(bidder_value) == bool(gov_value) else "MISMATCH"

    try:
        return "MATCH" if float(bidder_value) == float(gov_value) else "MISMATCH"
    except (TypeError, ValueError):
        return "MATCH" if bidder_value == gov_value else "MISMATCH"


def check_identity_consistency(bidder_data: dict) -> dict:
    """Compare the legal name declared on PAN, GST, Udyam and the
    Certificate of Incorporation for the same bidder.

    Returns a dict shaped like a requirement result:
        status: "PASS" | "REVIEW" | "MISSING"
        reason: explanation
        evidence: {source: normalized_name_or_None}
    """
    name_sources = {
        "PAN": "pan.legal_name",
        "GST": "gst.legal_name",
        "UDYAM": "udyam.legal_name",
        "INCORPORATION": "incorporation.legal_name",
    }

    raw_names = {}
    normalized_names = {}
    for source, path in name_sources.items():
        raw = get_nested_value(bidder_data, path)
        raw_names[source] = None if raw is FIELD_MISSING else raw
        normalized_names[source] = normalize_name(raw) if raw is not FIELD_MISSING else None

    available = {src: n for src, n in normalized_names.items() if n is not None}

    if len(available) < 2:
        return {
            "status": "MISSING",
            "extracted_value": raw_names,
            "reason": (
                "Fewer than two documents carry a legal name, so cross-document "
                "identity consistency cannot be checked."
            ),
        }

    distinct_names = set(available.values())
    if len(distinct_names) == 1:
        return {
            "status": "PASS",
            "extracted_value": raw_names,
            "reason": (
                f"Legal name is consistent across {', '.join(available.keys())}: "
                f"'{next(iter(distinct_names))}'."
            ),
        }

    mismatched = ", ".join(f"{src}='{name}'" for src, name in available.items())
    return {
        "status": "REVIEW",
        "extracted_value": raw_names,
        "reason": (
            f"Legal name differs across documents ({mismatched}). This may be a "
            f"harmless formatting difference or a genuine identity mismatch and "
            f"requires manual review."
        ),
    }
