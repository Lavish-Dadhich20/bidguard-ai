"""
Stage 1: document/data legitimacy verification.

This stage is intentionally separate from tender compliance. It verifies
that extracted document data is structurally usable and, where a
government/reference record exists, agrees with that record.

Statuses: VERIFIED / REVIEW / INVALID / MISSING
"""

from __future__ import annotations

from typing import Any

from engine.government_checker import get_gov_record
from engine.cross_verification import normalize_name


DOCUMENT_GOV_RULES = {
    "GST_REG_06": {"source": "GST", "identifier": "gstin", "gov_fields": ["status", "legal_name"]},
    "PAN": {"source": "PAN", "identifier": "pan_number", "gov_fields": ["status", "legal_name"]},
    "UDYAM": {"source": "UDYAM", "identifier": "udyam_registration_number", "gov_fields": ["status", "legal_name"]},
    "ITR": {"source": "ITR", "identifier": "pan", "gov_fields": ["filing_status"]},
    "EPFO": {"source": "EPFO", "identifier": "pan", "gov_fields": ["status"]},
    "ESIC": {"source": "ESIC", "identifier": "pan", "gov_fields": ["status"]},
    "MAKE_IN_INDIA": {"source": "MAKE_IN_INDIA", "identifier": "pan", "gov_fields": ["percentage"]},
    "OEM": {"source": "OEM", "identifier": "pan", "gov_fields": ["valid", "oem_name"]},
    "INCORPORATION": {"source": "MCA", "identifier": "cin_or_registration_number", "gov_fields": ["status", "legal_name"]},
    "BLACKLISTING_DECLARATION": {"source": "BLACKLIST", "identifier": "pan", "gov_fields": []},
}


def _first_nonempty(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _find_identifier(fields: dict, document_type: str, bidder_profile: dict) -> Any:
    key = DOCUMENT_GOV_RULES.get(document_type, {}).get("identifier")
    if not key:
        return None
    value = fields.get(key)
    if value:
        return value

    # Some documents do not carry the PAN themselves; use the already
    # extracted PAN for government sources that are keyed by PAN.
    if key == "pan":
        return bidder_profile.get("pan", {}).get("number")
    return None


def _structural_status(metadata: dict) -> tuple[str, str]:
    missing = metadata.get("missing_fields") or []
    if missing:
        return "MISSING", f"Required extracted fields are missing: {', '.join(missing)}."

    format_flags = [
        ("pan_format_valid", "PAN format is invalid."),
        ("gstin_format_valid", "GSTIN format is invalid."),
        ("udyam_format_valid", "Udyam registration number format is invalid."),
        ("code_format_valid", "EPFO establishment code format is invalid."),
        ("number_format_valid", "ESIC registration number format is invalid."),
    ]
    for flag, reason in format_flags:
        if flag in metadata and metadata[flag] is False:
            return "INVALID", reason

    return "VERIFIED", "Document was successfully extracted and passed structural validation."


def _compare(a: Any, b: Any) -> bool:
    if isinstance(a, str) or isinstance(b, str):
        return str(a).strip().upper() == str(b).strip().upper()
    return a == b


def verify_extractions(extractions: list[dict], bidder_profile: dict, government_records) -> dict:
    results = []
    for item in extractions:
        doc_type = item["document_type"]
        fields = item.get("fields", {})
        metadata = item.get("metadata", {})

        status, reason = _structural_status(metadata)
        rule = DOCUMENT_GOV_RULES.get(doc_type)

        result = {
            "document_type": doc_type,
            "status": status,
            "reason": reason,
            "government_source": rule.get("source") if rule else None,
            "government_checked": False,
            "comparisons": [],
        }

        if status in {"MISSING", "INVALID"}:
            results.append(result)
            continue

        if not rule:
            result["status"] = "REVIEW"
            result["reason"] = (
                "Document extraction is structurally valid, but no government/reference "
                "source is configured for this document type."
            )
            results.append(result)
            continue

        source = rule["source"]
        identifier = _find_identifier(fields, doc_type, bidder_profile)

        if source == "BLACKLIST":
            from engine.government_checker import is_blacklisted
            identifiers = [
                bidder_profile.get("pan", {}).get("number"),
                bidder_profile.get("company_name"),
            ]
            blacklisted = is_blacklisted(government_records, identifiers)
            result["government_checked"] = True
            result["comparisons"].append({
                "field": "blacklist_status",
                "extracted": fields.get("blacklisting_status"),
                "government": "ON_BLACKLIST" if blacklisted else "NOT_ON_BLACKLIST",
                "match": not blacklisted,
            })
            if blacklisted:
                result["status"] = "INVALID"
                result["reason"] = "Government/reference blacklist data indicates the bidder is blacklisted/debarred."
            else:
                result["status"] = "VERIFIED"
                result["reason"] = "No matching bidder identifier was found on the government/reference blacklist."
            results.append(result)
            continue

        if not identifier:
            result["status"] = "MISSING"
            result["reason"] = (
                f"Cannot perform {source} verification because the required identifier "
                f"could not be extracted."
            )
            results.append(result)
            continue

        gov_record = get_gov_record(government_records, source, identifier)
        if not gov_record:
            result["status"] = "REVIEW"
            result["reason"] = (
                f"No matching {source} government/reference record was found for identifier {identifier!r}."
            )
            results.append(result)
            continue

        result["government_checked"] = True
        mismatches = []

        # Document-specific comparisons.
        if doc_type == "GST_REG_06":
            pairs = [
                ("legal_name", fields.get("legal_name"), gov_record.get("legal_name")),
            ]
        elif doc_type == "PAN":
            pairs = [
                ("legal_name", fields.get("name"), gov_record.get("legal_name")),
            ]
        elif doc_type == "UDYAM":
            pairs = [
                ("legal_name", fields.get("enterprise_name"), gov_record.get("legal_name")),
            ]
        elif doc_type == "INCORPORATION":
            pairs = [
                ("legal_name", fields.get("legal_name"), gov_record.get("legal_name")),
            ]
        elif doc_type == "ITR":
            # ITR document proves filing identity; filing status itself may be
            # supplied by the government record rather than printed on the acknowledgement.
            pairs = []
        elif doc_type == "MAKE_IN_INDIA":
            pairs = [
                ("local_content_percentage",
                 fields.get("local_content_percentage"),
                 gov_record.get("percentage")),
            ]
        elif doc_type == "OEM":
            pairs = [
                ("oem_name", fields.get("oem_name"), gov_record.get("oem_name")),
            ]
        else:
            pairs = []

        for field, extracted, government in pairs:
            if extracted in (None, "") or government in (None, ""):
                continue
            match = _compare(extracted, government)
            result["comparisons"].append({
                "field": field,
                "extracted": extracted,
                "government": government,
                "match": match,
            })
            if not match:
                mismatches.append(field)

        # Identifier itself is necessarily matched by lookup.
        if mismatches:
            result["status"] = "REVIEW"
            result["reason"] = (
                "Government/reference record was found, but one or more extracted "
                f"fields do not match: {', '.join(mismatches)}."
            )
        else:
            result["status"] = "VERIFIED"
            result["reason"] = f"Matched {source} government/reference record successfully."

        results.append(result)

    return {
        "summary": {
            "verified": sum(r["status"] == "VERIFIED" for r in results),
            "review": sum(r["status"] == "REVIEW" for r in results),
            "invalid": sum(r["status"] == "INVALID" for r in results),
            "missing": sum(r["status"] == "MISSING" for r in results),
            "total": len(results),
        },
        "documents": results,
    }
