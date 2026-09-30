"""
Common interface for all document-type-specific extractors.

Adding a new document type means:
    1. Write schemas/<type>.py   (field list + validation)
    2. Write extractors/<type>.py, subclassing BaseExtractor
    3. Register it in extractors/registry.py

Nothing else in the pipeline changes.
"""

from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    # A short machine-readable identifier, e.g. "GST_REG_06", "PAN", "UDYAM".
    document_type: str = None

    # Human-readable label used in the document-type selection menu.
    display_name: str = None

    @abstractmethod
    def extract(self, text: str) -> dict:
        """
        Given raw text (from the PDF text layer or from OCR), return a
        dict of extracted fields specific to this document type.

        Implementations must NOT invent values. Fields that cannot be
        confidently located in the text should be set to None.
        """
        raise NotImplementedError

    def validate(self, fields: dict) -> dict:
        """
        Optional structural validation (e.g. GSTIN format, required
        fields present). Default: no-op. Extractors should override this
        by delegating to their matching schemas/<type>.py::validate().
        """
        return {}
