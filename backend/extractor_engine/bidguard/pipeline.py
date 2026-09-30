"""
Document Intelligence pipeline - Stage 1 of BidGuard.

    Document Upload
          |
          v
    Document Type (chosen by user / caller)
          |
          v
    Text Extraction / OCR   (core/text_extraction.py)
          |
          v
    Document-Type-Specific Extractor   (extractors/<type>.py)
          |
          v
    Schema Validation   (schemas/<type>.py)
          |
          v
    Structured JSON

This module intentionally contains NO document-type-specific logic. It
only orchestrates the generic steps above. Everything that differs
between GST / PAN / Udyam / ITR / OEM lives in extractors/ and schemas/.

Explicitly OUT OF SCOPE here (future pipeline stages, not built yet):
    - Cross-checking extracted data against government sources
    - Compliance scoring / risk level
    - Recommendations to the procurement officer
"""

from core.text_extraction import get_document_text
from extractors.registry import get_extractor


def process_document(pdf_path: str, document_type_key: str) -> dict:
    """
    Run the full extraction pipeline for a single uploaded document.

    Returns a JSON-serializable dict:
        {
            "document_type": "...",
            "fields": {...},            # only fields relevant to this document type
            "metadata": {
                "extraction_method": "PDF_TEXT" | "OCR",
                "ocr_used": bool,
                "pages_processed": int,
                "missing_fields": [...],
                "warnings": [...],
                ... (schema-specific validation info, e.g. gstin_format_valid)
            }
        }
    """
    extractor = get_extractor(document_type_key)

    extraction_result = get_document_text(pdf_path)

    fields = extractor.extract(extraction_result.text)
    validation = extractor.validate(fields)

    metadata = {
        "extraction_method": extraction_result.method,
        "ocr_used": extraction_result.ocr_used,
        "pages_processed": extraction_result.pages_processed,
        "warnings": extraction_result.warnings,
    }
    metadata.update(validation)  # e.g. missing_fields, gstin_format_valid

    return {
        "document_type": extractor.document_type,
        "fields": fields,
        "metadata": metadata,
    }
