# BidGuard Extractor Update

This version keeps the existing extraction architecture and document-type keys intact while improving the eight newly added document types to match the current SIH sample-document field labels.

## Updated document types

- GST Return Filing Record (`GST_RETURN`)
- Make in India / Local Content Declaration (`MAKE_IN_INDIA`)
- DPIIT Startup Recognition Certificate (`DPIIT_STARTUP`)
- NSIC Registration Certificate (`NSIC`)
- DigiLocker Document Verification Record (`DIGILOCKER`)
- Blacklisting/Debarment Declaration (`BLACKLISTING_DECLARATION`)
- Tender/Bid Compliance Declaration (`TENDER_BID_COMPLIANCE`)
- Certificate of Incorporation / Business Registration Certificate (`INCORPORATION`)

## Compatibility

Existing document-type keys and existing field names are preserved where possible. New fields were added rather than replacing the previous fields, so existing integrations should not need to be rebuilt from scratch.

The eight updated extractors now recognize labels used by the current sample documents, including `Company`, `Bidder`, `Recognition No.`, `NSIC Registration No.`, `Udyam No.`, `Holder/Entity`, `Document ID`, `Tender Title`, `CIN`, `PAN`, `State`, `Country`, `Financial Year`, and `Compliance Status`.

Validation was also adjusted so fields that are not present in the provided sample format are not incorrectly reported as required.

## OCR

The existing OCR auto-detection remains in place. It detects Tesseract and the WinGet Poppler installation without requiring a user-specific hardcoded Windows path.

## Run

```powershell
python main.py
```

The CLI asks for the PDF path and document type interactively.
