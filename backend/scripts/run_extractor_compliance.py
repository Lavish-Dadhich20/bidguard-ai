"""
Run the current 15-document extractor and the BidGuard compliance engine.

Example:
    python scripts/run_extractor_compliance.py --manifest path/to/manifest.json

Manifest format:
{
  "company_id": "BID-001",
  "tender_id": "TDR-DEMO-001",
  "documents": [
    {"document_type": "GST_REG_06", "path": "docs/gst.pdf"},
    {"document_type": "PAN", "path": "docs/pan.pdf"}
  ]
}

The script:
  1. runs the CURRENT extractor/OCR for every uploaded document
  2. builds one normalized bidder profile
  3. runs Stage 1 verification
  4. runs Stage 2 tender compliance, gating unverified document data
  5. writes one JSON result containing extraction + verification + compliance
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from integration.extractor_adapter import build_bidder_profile, extract_document
from integration.stage1_verifier import verify_extractions
from engine.compliance_engine import evaluate_bidder
from engine.providers import create_supabase_provider


REQUIREMENT_DOC_MAP = {
    "gst": "GST_REG_06",
    "pan": "PAN",
    "udyam": "UDYAM",
    "itr": "ITR",
    "epfo": "EPFO",
    "esic": "ESIC",
    "local_content": "MAKE_IN_INDIA",
    "oem_authorization": "OEM",
    "incorporation": "INCORPORATION",
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_government_provider():
    if os.getenv("GOV_SOURCE", "supabase").lower() == "supabase":
        print("Government data source: Supabase")
        return create_supabase_provider()

    path = PROJECT_ROOT / "data" / "government_records.json"
    print("Government data source: local JSON")
    return load_json(path)


def gate_compliance_results(compliance: dict, stage1: dict) -> dict:
    """Prevent Stage 2 from passing data that Stage 1 did not verify."""
    verification = {
        r["document_type"]: r["status"]
        for r in stage1["documents"]
    }

    for result in compliance["requirements"]:
        path = None
        # requirement objects in the current project don't retain field_to_check,
        # so infer the document from requirement name/verification source.
        source = result.get("verification_source")
        source_to_doc = {
            "GST": "GST_REG_06",
            "PAN": "PAN",
            "UDYAM": "UDYAM",
            "ITR": "ITR",
            "EPFO": "EPFO",
            "ESIC": "ESIC",
            "MAKE_IN_INDIA": "MAKE_IN_INDIA",
            "OEM": "OEM",
            "MCA": "INCORPORATION",
            "BLACKLIST": "BLACKLISTING_DECLARATION",
        }
        doc = source_to_doc.get(source)

        if not doc:
            continue

        doc_status = verification.get(doc)

        if doc_status == "INVALID":
            result["status"] = "FAIL"
            result["reason"] = (
                "Stage 1 document verification failed, so this requirement "
                "cannot be treated as compliant. " + result["reason"]
            )
        elif doc_status == "MISSING":
            result["status"] = "MISSING"
            result["reason"] = (
                "Stage 1 could not verify the required document because required "
                "extracted data is missing. " + result["reason"]
            )
        elif doc_status == "REVIEW":
            result["status"] = "REVIEW"
            result["reason"] = (
                "Stage 1 document/reference verification requires manual review. "
                + result["reason"]
            )

    # Recompute score after the gate.
    from engine.scorer import score_results
    scoring = score_results(compliance["requirements"])
    compliance.update(scoring)
    return compliance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="Path to the document manifest JSON")
    parser.add_argument(
        "--tender",
        default="data/tender_requirements.json",
        help="Tender requirements JSON path",
    )
    parser.add_argument(
        "--output",
        default="output/extractor_compliance_result.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    manifest = load_json(manifest_path)

    tender_path = (PROJECT_ROOT / args.tender).resolve() if not Path(args.tender).is_absolute() else Path(args.tender)
    tender = load_json(tender_path)

    government_records = load_government_provider()

    extractions = []
    for doc in manifest.get("documents", []):
        doc_type = doc["document_type"]
        raw_path = Path(doc["path"])
        pdf_path = raw_path if raw_path.is_absolute() else manifest_path.parent / raw_path
        pdf_path = pdf_path.resolve()

        if not pdf_path.is_file():
            raise FileNotFoundError(f"Document not found: {pdf_path}")

        print(f"Extracting {doc_type}: {pdf_path.name}")
        extraction = extract_document(str(pdf_path), doc_type)
        extraction["source_file"] = str(pdf_path)
        extractions.append(extraction)

    profile = build_bidder_profile(extractions, government_records)
    stage1 = verify_extractions(extractions, profile, government_records)

    # Tender can be overridden by manifest for dynamic frontend uploads.
    tender_id = manifest.get("tender_id")
    if tender_id and tender.get("tender_id") != tender_id:
        raise ValueError(
            f"Manifest tender_id={tender_id!r} does not match loaded tender "
            f"{tender.get('tender_id')!r}. Pass the correct tender JSON."
        )

    compliance = evaluate_bidder(profile, tender, government_records)
    compliance = gate_compliance_results(compliance, stage1)

    result = {
        "bidder_id": manifest.get("company_id") or manifest.get("bidder_id"),
        "company_name": profile.get("company_name"),
        "tender_id": tender.get("tender_id"),
        "extractions": extractions,
        "normalized_bidder_profile": profile,
        "stage1_document_verification": stage1,
        "stage2_tender_compliance": compliance,
    }

    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n=== BidGuard Integrated Verification ===")
    print(f"Company: {result['company_name']}")
    print(f"Stage 1: {stage1['summary']}")
    print(f"Stage 2: {compliance['summary']}")
    print(f"Overall: {compliance['overall_status']}")
    print(f"Result: {output_path}")


if __name__ == "__main__":
    main()
