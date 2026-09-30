"""Extractor for NSIC Registration Certificates."""

from extractors.base import BaseExtractor
from extractors.utils import search_line_value, normalize_date, search_first
from schemas import nsic as schema


class NSICExtractor(BaseExtractor):
    document_type = schema.DOCUMENT_TYPE
    display_name = "NSIC Registration Certificate"

    def extract(self, text: str) -> dict:
        pan = search_first(text, [
            r"(?:PAN|Permanent Account Number)\s*[:\-]?\s*([A-Z]{5}\d{4}[A-Z])"
        ])
        return {
            "registration_number": search_line_value(text, [
                "NSIC Registration Number", "NSIC Registration No.", "Registration Number",
                "NSIC No.", "NSIC Registration No.", "Registration No."
            ]),
            "enterprise_name": search_line_value(text, [
                "Enterprise Name", "Name of Enterprise", "Company Name", "Legal Name"
            ]),
            "pan": pan,
            "udyam_number": search_line_value(text, [
                "Udyam Registration Number", "Udyam Number", "Udyam No.", "Udyam Registration No."
            ]),
            "issue_date": normalize_date(search_line_value(text, [
                "Issue Date", "Date of Issue"
            ])),
            "validity_from": normalize_date(search_line_value(text, [
                "Validity From", "Valid From", "Validity Start Date"
            ])),
            "validity_to": normalize_date(search_line_value(text, [
                "Validity To", "Valid Until", "Valid To", "Expiry Date", "Validity End Date"
            ])),
            "status": search_line_value(text, ["Status", "Registration Status"]),
            "address": search_line_value(text, ["Address", "Registered Address", "Official Address"]),
            "certificate_category": search_line_value(text, [
                "Certificate Category", "Category", "Registration Category", "Enterprise Category"
            ]),
        }

    def validate(self, fields):
        return schema.validate(fields)
