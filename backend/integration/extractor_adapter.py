"""
Adapter between the current 15-document BidGuard extractor and the
BidGuard compliance engine.

The extractor is kept as a replaceable component under extractor_engine/.
This adapter converts document-specific JSON into the normalized bidder
profile expected by engine.compliance_engine.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Make the bundled extractor importable without changing the user's global PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXTRACTOR_ROOT = PROJECT_ROOT / "extractor_engine" / "bidguard"
if str(EXTRACTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(EXTRACTOR_ROOT))

from pipeline import process_document  # noqa: E402


DOCUMENT_TYPES = {
    "GST_REG_06": "gst",
    "PAN": "pan",
    "UDYAM": "udyam",
    "ITR": "itr",
    "OEM": "oem",
    "EPFO": "epfo",
    "ESIC": "esic",
    "GST_RETURN": "gst_return",
    "MAKE_IN_INDIA": "make_in_india",
    "DPIIT_STARTUP": "dpiit_startup",
    "NSIC": "nsic",
    "DIGILOCKER": "digilocker",
    "BLACKLISTING_DECLARATION": "blacklisting_declaration",
    "TENDER_BID_COMPLIANCE": "tender_bid_compliance",
    "INCORPORATION": "incorporation",
}


def extract_document(pdf_path: str, document_type: str) -> dict:
    """Run the current extractor/OCR pipeline for one document."""
    if document_type not in DOCUMENT_TYPES:
        raise ValueError(
            f"Unsupported document type {document_type!r}. "
            f"Supported: {', '.join(DOCUMENT_TYPES)}"
        )
    return process_document(pdf_path, document_type)


def _first(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _upper(value):
    return value.strip().upper() if isinstance(value, str) else value


def _date(value):
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            pass
    return None


def _oem_valid(validity: dict | None) -> bool | None:
    if not validity:
        return None
    start = _date(validity.get("from"))
    end = _date(validity.get("to"))
    if start and end:
        today = datetime.now().date()
        return start <= today <= end
    return None


def _build_base_profile(extractions: list[dict]) -> dict:
    """Normalize raw extractor outputs into the engine's legacy field shape."""
    by_type = {item["document_type"]: item.get("fields", {}) for item in extractions}

    gst = by_type.get("GST_REG_06", {})
    pan = by_type.get("PAN", {})
    udyam = by_type.get("UDYAM", {})
    itr = by_type.get("ITR", {})
    oem = by_type.get("OEM", {})
    epfo = by_type.get("EPFO", {})
    esic = by_type.get("ESIC", {})
    gst_return = by_type.get("GST_RETURN", {})
    make_india = by_type.get("MAKE_IN_INDIA", {})
    dpiit = by_type.get("DPIIT_STARTUP", {})
    nsic = by_type.get("NSIC", {})
    digilocker = by_type.get("DIGILOCKER", {})
    blacklist_decl = by_type.get("BLACKLISTING_DECLARATION", {})
    tender_decl = by_type.get("TENDER_BID_COMPLIANCE", {})
    incorporation = by_type.get("INCORPORATION", {})

    company_name = _first(
        gst.get("legal_name"),
        pan.get("name"),
        udyam.get("enterprise_name"),
        incorporation.get("legal_name"),
        dpiit.get("startup_name"),
        nsic.get("enterprise_name"),
        gst_return.get("legal_name"),
        epfo.get("establishment_name"),
        esic.get("establishment_name"),
        blacklist_decl.get("bidder_name"),
        tender_decl.get("bidder_name"),
    )

    return {
        "company_name": company_name or "UNKNOWN",

        "pan": {
            "number": pan.get("pan_number"),
            "status": _upper(pan.get("status")),
            "legal_name": pan.get("name"),
        },

        "gst": {
            "gstin": gst.get("gstin"),
            "status": None,  # enriched from government/reference data when available
            "legal_name": gst.get("legal_name"),
        },

        "udyam": {
            "number": udyam.get("udyam_registration_number"),
            "status": None,  # enriched from government/reference data when available
            "legal_name": udyam.get("enterprise_name"),
        },

        "turnover": {
            "annual_turnover": None,  # government/reference value is authoritative
        },

        "itr": {
            "filing_status": ("FILED" if itr.get("acknowledgement_number") and itr.get("date_of_filing") else None),  # government value overrides when available
            "pan": itr.get("pan"),
            "assessment_year": itr.get("assessment_year"),
            "name_of_assessee": itr.get("name_of_assessee"),
            "gross_total_income": itr.get("gross_total_income"),
            "total_taxable_income": itr.get("total_taxable_income"),
            "tax_paid": itr.get("tax_paid"),
            "acknowledgement_number": itr.get("acknowledgement_number"),
            "date_of_filing": itr.get("date_of_filing"),
        },

        "epfo": {
            "status": _upper(epfo.get("compliance_status")),
            "establishment_code": epfo.get("epfo_establishment_code"),
            "establishment_name": epfo.get("establishment_name"),
        },

        "esic": {
            "status": _upper(esic.get("compliance_status")),
            "registration_number": esic.get("esic_registration_number"),
            "establishment_name": esic.get("establishment_name"),
        },

        "local_content": {
            "percentage": make_india.get("local_content_percentage"),
            "category": make_india.get("local_content_category"),
            "country_of_origin": make_india.get("country_of_origin"),
        },

        "oem_authorization": {
            "valid": _oem_valid(oem.get("validity")),
            "oem_name": oem.get("oem_name"),
            "authorized_bidder_name": oem.get("authorized_bidder_name"),
            "product_or_brand": oem.get("authorized_product_or_brand"),
            "letter_number": oem.get("authorization_letter_number"),
            "validity": oem.get("validity"),
        },

        "incorporation": {
            "status": _upper(incorporation.get("company_status")),
            "legal_name": incorporation.get("legal_name"),
            "cin": incorporation.get("cin_or_registration_number"),
            "company_type": incorporation.get("company_type"),
            "date_of_incorporation": incorporation.get("date_of_incorporation"),
        },

        # Experience is not a field printed by the current 15 extractors.
        "experience": {"years": None},

        # Keep all 15 document-specific results available to reports/frontend.
        "gst_return": gst_return,
        "make_in_india": make_india,
        "dpiit_startup": dpiit,
        "nsic": nsic,
        "digilocker": digilocker,
        "blacklisting_declaration": blacklist_decl,
        "tender_bid_compliance": tender_decl,
    }


def enrich_with_government_data(profile: dict, government_records) -> dict:
    """
    Enrich normalized fields only from a matching government/reference
    record. This does not invent extracted document values.

    Matching identifiers:
      GST -> GSTIN
      PAN -> PAN
      UDYAM -> Udyam number
      TURNOVER/ITR/EPFO/ESIC/MAKE_IN_INDIA/OEM -> PAN
      MCA -> CIN
    """
    from engine.government_checker import get_gov_record

    def lookup(source, identifier):
        return get_gov_record(government_records, source, identifier)

    pan_no = profile["pan"].get("number")
    gstin = profile["gst"].get("gstin")
    udyam_no = profile["udyam"].get("number")
    cin = profile["incorporation"].get("cin")

    gov_pan = lookup("PAN", pan_no)
    gov_gst = lookup("GST", gstin)
    gov_udyam = lookup("UDYAM", udyam_no)
    gov_turnover = lookup("TURNOVER", pan_no)
    gov_itr = lookup("ITR", pan_no)
    gov_epfo = lookup("EPFO", pan_no)
    gov_esic = lookup("ESIC", pan_no)
    gov_local = lookup("MAKE_IN_INDIA", pan_no)
    gov_oem = lookup("OEM", pan_no)
    gov_mca = lookup("MCA", cin)

    if gov_pan:
        profile["pan"]["status"] = _upper(gov_pan.get("status"))
        profile["pan"]["government_legal_name"] = gov_pan.get("legal_name")

    if gov_gst:
        profile["gst"]["status"] = _upper(gov_gst.get("status"))
        profile["gst"]["government_legal_name"] = gov_gst.get("legal_name")

    if gov_udyam:
        profile["udyam"]["status"] = _upper(gov_udyam.get("status"))
        profile["udyam"]["government_legal_name"] = gov_udyam.get("legal_name")

    if gov_turnover:
        profile["turnover"]["annual_turnover"] = gov_turnover.get("annual_turnover")

    if gov_itr:
        profile["itr"]["filing_status"] = _upper(gov_itr.get("filing_status"))

    if gov_epfo:
        profile["epfo"]["status"] = _upper(gov_epfo.get("status"))

    if gov_esic:
        profile["esic"]["status"] = _upper(gov_esic.get("status"))

    if gov_local:
        profile["local_content"]["government_percentage"] = gov_local.get("percentage")

    if gov_oem:
        profile["oem_authorization"]["government_valid"] = gov_oem.get("valid")
        profile["oem_authorization"]["government_oem_name"] = gov_oem.get("oem_name")

    if gov_mca:
        profile["incorporation"]["status"] = _upper(gov_mca.get("status"))
        profile["incorporation"]["government_legal_name"] = gov_mca.get("legal_name")

    return profile


def build_bidder_profile(extractions: list[dict], government_records=None) -> dict:
    profile = _build_base_profile(extractions)
    if government_records is not None:
        profile = enrich_with_government_data(profile, government_records)
    profile["_extractions"] = extractions
    return profile
