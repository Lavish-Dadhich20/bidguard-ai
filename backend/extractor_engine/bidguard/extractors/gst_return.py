"""Extractor for GST Return Filing Records."""

from extractors.base import BaseExtractor
from extractors.utils import search_first, search_line_value, normalize_date
from schemas import gst_return as schema


class GSTReturnExtractor(BaseExtractor):
    document_type = schema.DOCUMENT_TYPE
    display_name = "GST Return Filing Record"

    def extract(self, text: str) -> dict:
        gstin = search_first(text, [
            r"(?:GSTIN|GSTIN/UIN)\s*[:\-]?\s*([0-9A-Z]{15})",
            r"GST Identification Number\s*[:\-]?\s*([0-9A-Z]{15})",
        ])
        return {
            "gstin": schema.normalize_gstin(gstin),
            "legal_name": search_line_value(text, [
                "Legal Name", "Legal Name of Business", "Name of Taxpayer"
            ]),
            "return_period": search_line_value(text, [
                "Return Period", "Tax Period", "Tax Period / Return Period", "Period"
            ]),
            "return_type": search_line_value(text, [
                "Return Type", "Form Type", "Return Form", "Return Form Type"
            ]),
            "filing_date": normalize_date(search_line_value(text, [
                "Date of Filing", "Filing Date", "Filed On"
            ])),
            "filing_status": search_line_value(text, [
                "Filing Status", "Return Filing Status"
            ]),
            "acknowledgement_number": search_line_value(text, [
                "Acknowledgement Number", "Acknowledgment Number", "ARN",
                "Acknowledgement No.", "Acknowledgment No."
            ]),
            "financial_year": search_line_value(text, [
                "Financial Year", "FY", "Financial Year (FY)"
            ]),
            "compliance_status": search_line_value(text, [
                "Compliance Status", "Compliance Result", "Compliance"
            ]),
            "taxable_turnover": search_line_value(text, [
                "Taxable Turnover", "Taxable Value", "Taxable Amount"
            ]),
            "tax_liability": search_line_value(text, [
                "Tax Liability", "Total Tax Liability", "Tax Payable"
            ]),
            "tax_paid": search_line_value(text, [
                "Tax Paid", "Total Tax Paid", "Tax Amount Paid"
            ]),
        }

    def validate(self, fields):
        return schema.validate(fields)
