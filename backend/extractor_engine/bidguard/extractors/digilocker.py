"""Extractor for DigiLocker Document Verification Records."""

from extractors.base import BaseExtractor
from extractors.utils import search_line_value, normalize_date
from schemas import digilocker as schema


class DigiLockerExtractor(BaseExtractor):
    document_type = schema.DOCUMENT_TYPE
    display_name = "DigiLocker Document Verification Record"

    def extract(self, text: str) -> dict:
        return {
            "verification_id": search_line_value(text, [
                "Verification ID", "Verification Reference", "Verification Reference ID"
            ]),
            "document_type": search_line_value(text, [
                "Document Type", "Verified Document Type"
            ]),
            "issuer": search_line_value(text, [
                "Issuer", "Document Issuer", "Issuing Authority"
            ]),
            "document_number": search_line_value(text, [
                "Document ID", "Document Number", "Document No.",
                "Certificate Number", "Registration Number"
            ]),
            "holder_name": search_line_value(text, [
                "Holder/Entity", "Holder / Entity", "Holder Name", "Document Holder",
                "Name of Holder", "Name", "Entity Name"
            ]),
            "verification_date": normalize_date(search_line_value(text, [
                "Verification Date", "Date of Verification", "Verified On"
            ])),
            "verification_status": search_line_value(text, [
                "Verification Status", "Status", "Verification Result"
            ]),
            "document_uri": search_line_value(text, [
                "DigiLocker URI", "Document URI", "URI", "Document Link"
            ]),
            "document_hash": search_line_value(text, [
                "Document Hash", "Hash", "SHA-256 Hash"
            ]),
        }

    def validate(self, fields):
        return schema.validate(fields)
