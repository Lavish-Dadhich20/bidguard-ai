# Extractor Integration

The example manifest is a runnable smoke test using the seven sample PDFs bundled with the current extractor.

The extractor code supports all 15 document types, but this ZIP only contains sample PDFs for GST, PAN, Udyam, ITR, OEM, EPFO, and ESIC. Add the remaining eight PDFs to the extractor documents directory and add them to a manifest when testing all 15.

Run from the project root:

```powershell
$env:GOV_SOURCE="supabase"
python scripts/run_extractor_compliance.py --manifest integration\manifest_15_docs.example.json
```


## Current demo verification data

This integration package includes matching DEMO INNOVATIONS PRIVATE LIMITED reference
records in `data/government_records.json` for the seven bundled sample PDFs. If you use
Supabase, reseed after extracting this package:

```powershell
python scripts/seed_supabase.py
$env:GOV_SOURCE="supabase"
python scripts/run_extractor_compliance.py --manifest integration\manifest_15_docs.example.json
```

The bundled PAN sample currently extracts the name `. CATEGORY COMPANY`, while the
GST/Udyam/ITR/EPFO/ESIC documents extract `DEMO INNOVATIONS PRIVATE LIMITED`.
The integration intentionally does not overwrite that extractor output. The resulting
PAN identity discrepancy should therefore remain visible as `REVIEW`, which is useful
for testing cross-document inconsistency handling.

The seven bundled PDFs are a smoke-test set. The extractor code supports all 15
document types; the remaining eight document types require their actual PDFs to be
added to the manifest for a full 15-document run.
