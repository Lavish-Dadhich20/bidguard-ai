"""Extractor for Certificates of Incorporation / Business Registration."""

from extractors.base import BaseExtractor
from extractors.utils import search_line_value, search_first, normalize_date
from schemas import incorporation as schema


class IncorporationExtractor(BaseExtractor):
    document_type = schema.DOCUMENT_TYPE
    display_name = "Certificate of Incorporation / Business Registration Certificate"

    def extract(self, text: str) -> dict:
        pan = search_first(text, [
            r"(?:PAN|Permanent Account Number)\s*[:\-]?\s*([A-Z]{5}\d{4}[A-Z])"
        ])
        return {
            "cin_or_registration_number": search_line_value(text, [
                "CIN", "CIN / Registration Number", "Registration Number",
                "Company Registration Number", "Business Registration Number"
            ]),
            "legal_name": search_line_value(text, [
                "Legal Name", "Company Name", "Name of Company", "Registered Name"
            ]),
            "company_type": search_line_value(text, [
                "Company Type", "Type of Company", "Constitution", "Entity Type"
            ]),
            "date_of_incorporation": normalize_date(search_line_value(text, [
                "Date of Incorporation", "Incorporation Date", "Date of Registration"
            ])),
            "state": search_line_value(text, ["State", "State of Registration"]),
            "country": search_line_value(text, ["Country", "Country of Registration"]),
            "pan": pan,
            "registered_office": search_line_value(text, [
                "Registered Office", "Registered Office Address", "Registered Address"
            ]),
            "registrar": search_line_value(text, [
                "Registrar", "Registrar of Companies", "Registration Authority"
            ]),
            "authorized_capital": search_line_value(text, [
                "Authorized Capital", "Authorised Capital"
            ]),
            "paid_up_capital": search_line_value(text, [
                "Paid-up Capital", "Paid Up Capital", "Paid-up Share Capital"
            ]),
            "company_status": search_line_value(text, [
                "Company Status", "Status", "Registration Status"
            ]),
            "date_of_issue": normalize_date(search_line_value(text, [
                "Date of Issue", "Issue Date"
            ])),
        }

    def validate(self, fields):
        return schema.validate(fields)
