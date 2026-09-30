"""Extractor for Tender / Bid Compliance Declarations."""

from extractors.base import BaseExtractor
from extractors.utils import search_line_value, search_first, normalize_date
from schemas import tender_bid_compliance as schema


class TenderBidComplianceExtractor(BaseExtractor):
    document_type = schema.DOCUMENT_TYPE
    display_name = "Tender/Bid Compliance Declaration"

    def extract(self, text: str) -> dict:
        pan = search_first(text, [
            r"(?:PAN|Permanent Account Number)\s*[:\-]?\s*([A-Z]{5}\d{4}[A-Z])"
        ])
        gstin = search_first(text, [
            r"(?:GSTIN|GSTIN/UIN)\s*[:\-]?\s*([0-9A-Z]{15})"
        ])
        return {
            "tender_reference": search_line_value(text, [
                "Tender Reference", "Tender ID", "Tender No.", "Bid Reference"
            ]),
            "tender_title": search_line_value(text, ["Tender Title", "Title of Tender"]),
            "bidder_name": search_line_value(text, [
                "Bidder", "Bidder Name", "Name of Bidder", "Company Name", "Legal Name"
            ]),
            "pan": pan,
            "gstin": gstin,
            "declaration_type": search_line_value(text, [
                "Declaration Type", "Type of Declaration"
            ]),
            "declaration_text": search_line_value(text, ["Declaration"]),
            "compliance_status": search_line_value(text, [
                "Compliance Status", "Overall Compliance", "Compliance Result", "Status"
            ]),
            "deviations": search_line_value(text, [
                "Deviations", "Deviation Details", "Exceptions", "Exceptions / Deviations"
            ]),
            "remarks": search_line_value(text, [
                "Remarks", "Comments", "Additional Remarks"
            ]),
            "declaration_date": normalize_date(search_line_value(text, [
                "Declaration Date", "Date of Declaration", "Date"
            ])),
            "authorized_signatory": search_line_value(text, [
                "Authorized Signatory", "Authorised Signatory", "Signatory Name"
            ]),
            "signatory_designation": search_line_value(text, [
                "Signatory Designation", "Designation"
            ]),
        }

    def validate(self, fields):
        return schema.validate(fields)
