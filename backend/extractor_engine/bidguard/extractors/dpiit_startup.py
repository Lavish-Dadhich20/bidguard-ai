"""Extractor for DPIIT Startup Recognition Certificates."""

from extractors.base import BaseExtractor
from extractors.utils import search_line_value, search_first, normalize_date
from schemas import dpiit_startup as schema


class DPIITStartupExtractor(BaseExtractor):
    document_type = schema.DOCUMENT_TYPE
    display_name = "DPIIT Startup Recognition Certificate"

    def extract(self, text: str) -> dict:
        pan = search_first(text, [
            r"(?:PAN|Permanent Account Number)\s*[:\-]?\s*([A-Z]{5}\d{4}[A-Z])"
        ])
        return {
            "recognition_number": search_line_value(text, [
                "DPIIT Recognition Number", "Recognition No.", "Recognition Number",
                "Certificate Number", "Startup Recognition Number"
            ]),
            "startup_name": search_line_value(text, [
                "Startup Name", "Name of Startup", "Entity Name", "Legal Name"
            ]),
            "cin": search_line_value(text, [
                "CIN", "Corporate Identification Number"
            ]),
            "pan": pan,
            "date_of_incorporation": normalize_date(search_line_value(
                text, ["Date of Incorporation", "Incorporation Date"]
            )),
            "date_of_recognition": normalize_date(search_line_value(
                text, ["Date of Recognition", "Recognition Date", "Certificate Date"]
            )),
            "state": search_line_value(text, ["State", "State of Registration"]),
            "entity_type": search_line_value(text, ["Entity Type", "Type of Entity", "Constitution"]),
            "industry_or_sector": search_line_value(text, [
                "Industry", "Sector", "Industry / Sector", "Sector of Operation"
            ]),
            "registered_address": search_line_value(text, [
                "Registered Address", "Registered Office Address", "Address"
            ]),
            "recognition_status": search_line_value(text, [
                "Recognition Status", "Status", "Startup Status"
            ]),
            "authorized_signatory": search_line_value(text, [
                "Authorized Signatory", "Authorised Signatory"
            ]),
        }

    def validate(self, fields):
        return schema.validate(fields)
