"""Extractor for Make in India / Local Content Declarations."""

from extractors.base import BaseExtractor
from extractors.utils import search_line_value, search_first, normalize_date, normalize_percentage
from schemas import make_in_india as schema


class MakeInIndiaExtractor(BaseExtractor):
    document_type = schema.DOCUMENT_TYPE
    display_name = "Make in India / Local Content Declaration"

    def extract(self, text: str) -> dict:
        percentage_raw = search_line_value(text, [
            "Local Content Percentage", "Local Content %", "Percentage of Local Content",
            "Local Content"
        ])
        pan = search_first(text, [
            r"(?:PAN|Permanent Account Number)\s*[:\-]?\s*([A-Z]{5}\d{4}[A-Z])"
        ])
        gstin = search_first(text, [
            r"(?:GSTIN|GSTIN/UIN)\s*[:\-]?\s*([0-9A-Z]{15})"
        ])
        return {
            "tender_reference": search_line_value(text, [
                "Tender Reference", "Tender ID", "Bid Reference", "Tender No."
            ]),
            "bidder_name": search_line_value(text, [
                "Bidder Name", "Name of Bidder", "Company Name", "Company", "Legal Name"
            ]),
            "pan": pan,
            "gstin": gstin,
            "product_or_service_description": search_line_value(text, [
                "Product / Service Description", "Product Description", "Product",
                "Description of Goods/Services"
            ]),
            "local_content_percentage": normalize_percentage(percentage_raw),
            "local_content_category": search_line_value(text, [
                "Local Content Category", "Class of Supplier", "Supplier Class",
                "Supplier Category"
            ]),
            "country_of_origin": search_line_value(text, ["Country of Origin", "Origin of Goods"]),
            "domestic_value_addition": search_line_value(text, [
                "Domestic Value Addition", "Value Addition in India", "Domestic Value Added"
            ]),
            "declaration_date": normalize_date(search_line_value(text, [
                "Declaration Date", "Date of Declaration", "Date"
            ])),
            "status": search_line_value(text, ["Status", "Declaration Status", "Compliance Status"]),
            "authorized_signatory": search_line_value(text, [
                "Authorized Signatory", "Authorised Signatory", "Signatory Name"
            ]),
            "declaration_reference": search_line_value(text, [
                "Declaration Reference", "Declaration No.", "Declaration Number"
            ]),
        }

    def validate(self, fields):
        return schema.validate(fields)
