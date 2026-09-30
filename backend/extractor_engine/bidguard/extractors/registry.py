"""
Central registry of document-type -> extractor.

All document-specific extraction remains inside extractors/ and schemas/.
The generic pipeline does not need to change when a new document type is added.
"""

from extractors.gst import GSTExtractor
from extractors.pan import PANExtractor
from extractors.udyam import UdyamExtractor
from extractors.itr import ITRExtractor
from extractors.oem import OEMExtractor
from extractors.epfo import EPFOExtractor
from extractors.esic import ESICExtractor

from extractors.gst_return import GSTReturnExtractor
from extractors.make_in_india import MakeInIndiaExtractor
from extractors.dpiit_startup import DPIITStartupExtractor
from extractors.nsic import NSICExtractor
from extractors.digilocker import DigiLockerExtractor
from extractors.blacklisting import BlacklistingExtractor
from extractors.tender_bid_compliance import TenderBidComplianceExtractor
from extractors.incorporation import IncorporationExtractor


REGISTRY = {
    "GST_REG_06": GSTExtractor,
    "PAN": PANExtractor,
    "UDYAM": UdyamExtractor,
    "ITR": ITRExtractor,
    "OEM": OEMExtractor,
    "EPFO": EPFOExtractor,
    "ESIC": ESICExtractor,

    "GST_RETURN": GSTReturnExtractor,
    "MAKE_IN_INDIA": MakeInIndiaExtractor,
    "DPIIT_STARTUP": DPIITStartupExtractor,
    "NSIC": NSICExtractor,
    "DIGILOCKER": DigiLockerExtractor,
    "BLACKLISTING_DECLARATION": BlacklistingExtractor,
    "TENDER_BID_COMPLIANCE": TenderBidComplianceExtractor,
    "INCORPORATION": IncorporationExtractor,
}


DOCUMENT_TYPE_MENU = [
    {"key": "GST_REG_06", "label": "GST Registration Certificate"},
    {"key": "PAN", "label": "PAN"},
    {"key": "UDYAM", "label": "Udyam / MSME Certificate"},
    {"key": "ITR", "label": "Income Tax Return / ITR"},
    {"key": "OEM", "label": "OEM Authorization"},
    {"key": "EPFO", "label": "EPFO"},
    {"key": "ESIC", "label": "ESIC"},
    {"key": "GST_RETURN", "label": "GST Return Filing Record"},
    {"key": "MAKE_IN_INDIA", "label": "Make in India / Local Content Declaration"},
    {"key": "DPIIT_STARTUP", "label": "DPIIT Startup Recognition Certificate"},
    {"key": "NSIC", "label": "NSIC Registration Certificate"},
    {"key": "DIGILOCKER", "label": "DigiLocker Document Verification Record"},
    {"key": "BLACKLISTING_DECLARATION", "label": "Blacklisting/Debarment Declaration"},
    {"key": "TENDER_BID_COMPLIANCE", "label": "Tender/Bid Compliance Declaration"},
    {"key": "INCORPORATION", "label": "Certificate of Incorporation / Business Registration Certificate"},
    {"key": "OTHER", "label": "Other"},
]


def get_extractor(document_type_key: str):
    extractor_cls = REGISTRY.get(document_type_key)
    if extractor_cls is None:
        raise ValueError(
            f"No extractor implemented for document type '{document_type_key}'. "
            f"Implemented types: {list(REGISTRY.keys())}"
        )
    return extractor_cls()
