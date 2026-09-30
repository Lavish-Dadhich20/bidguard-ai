"""Extractor for Blacklisting / Debarment Declarations."""

from extractors.base import BaseExtractor
from extractors.utils import search_line_value, search_first, normalize_date
from schemas import blacklisting as schema


class BlacklistingExtractor(BaseExtractor):
    document_type = schema.DOCUMENT_TYPE
    display_name = "Blacklisting/Debarment Declaration"

    def extract(self, text: str) -> dict:
        pan = search_first(text, [
            r"(?:PAN|Permanent Account Number)\s*[:\-]?\s*([A-Z]{5}\d{4}[A-Z])"
        ])
        return {
            "bidder_name": search_line_value(text, [
                "Bidder Name", "Name of Bidder", "Company Name", "Company", "Legal Name"
            ]),
            "pan": pan,
            "cin": search_line_value(text, ["CIN", "Corporate Identification Number"]),
            "declaration_status": search_line_value(text, [
                "Declaration Status", "Undertaking Status"
            ]),
            "declaration_text": search_line_value(text, ["Declaration"]),
            "blacklisting_status": search_line_value(text, [
                "Blacklisting Status", "Blacklisted Status", "Debarment Status",
                "Debarment / Blacklisting Status", "Status"
            ]),
            "authority": search_line_value(text, [
                "Authority", "Issuing Authority", "Competent Authority"
            ]),
            "reference_number": search_line_value(text, [
                "Reference Number", "Reference No.", "Order Number", "Order No."
            ]),
            "effective_from": normalize_date(search_line_value(text, [
                "Effective From", "Debarment From", "Blacklisting From"
            ])),
            "effective_to": normalize_date(search_line_value(text, [
                "Effective To", "Debarment To", "Blacklisting To", "Expiry Date"
            ])),
            "declaration_date": normalize_date(search_line_value(text, [
                "Declaration Date", "Date of Declaration", "Date"
            ])),
            "authorized_signatory": search_line_value(text, [
                "Authorized Signatory", "Authorised Signatory", "Signatory Name"
            ]),
        }

    def validate(self, fields):
        return schema.validate(fields)
