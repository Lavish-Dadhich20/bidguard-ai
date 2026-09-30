# BidGuard AI — Bid Compliance Verification Engine

This is the **comparison / verification / compliance engine** for BidGuard AI
(Smart India Hackathon). It intentionally does **not** include OCR, document
upload, or the extractor — that's a teammate's separate module. This engine
starts from *already-extracted, structured* bidder data (mock JSON here,
a real extractor's output later) and decides compliance against a tender.

```
Tender requirements + Extracted bidder data + Mock government data
                              ↓
                     COMPARISON / VERIFICATION
                              ↓
              PASS / FAIL / REVIEW / MISSING (per requirement)
                              ↓
                     Compliance score + evidence
```

## Project structure

```
bidguard_compliance/
├── data/
│   ├── tender_requirements.json   # 1 tender, 13 requirements
│   ├── bidders.json               # 10 synthetic bidder companies
│   └── government_records.json    # mock GST/PAN/UDYAM/EPFO/... reference data
├── engine/
│   ├── requirement_checker.py     # dotted-field lookup + operator logic (deterministic)
│   ├── government_checker.py      # government record lookup + blacklist check
│   ├── cross_verification.py      # bidder-vs-government comparison + identity name check
│   ├── compliance_engine.py       # orchestrator: evaluate_bidder() / evaluate_all_bidders()
│   └── scorer.py                  # PASS/FAIL/REVIEW/MISSING counts + compliance %
├── output/
│   ├── results.json               # generated: full detailed result per company
│   └── summary.csv                # generated: one-row-per-company summary table
├── tests/
│   └── test_compliance_engine.py  # 19 automated tests (10 scenarios + unit tests)
├── main.py                        # CLI entry point
└── README.md
```

## How to run it

Requires only Python 3.8+ (standard library only, no dependencies).

```bash
cd bidguard_compliance
python3 main.py
```

This prints a summary table to the console and writes:
- `output/results.json` — full detail (every requirement, status, evidence, reason) for all 10 companies
- `output/summary.csv` — the summary table as CSV

### Run the tests

```bash
python3 -m unittest discover -s tests -v
```
or, if you have pytest installed:
```bash
pytest tests/ -v
```

19 tests should pass, covering: a fully compliant bidder, turnover below
threshold, GST inactive, legal-name mismatch, missing data, local content
below threshold, a blacklisted bidder, a government-data-unavailable case,
a bidder with multiple simultaneous issues, and a compliant bidder with one
non-critical review item — plus unit tests for the operator/comparison logic.

## The public API

Everything goes through one function, ready to be wrapped in a FastAPI
endpoint later:

```python
from engine.compliance_engine import evaluate_bidder

result = evaluate_bidder(bidder_data, tender_requirements, government_records)
```

- `bidder_data`: a dict shaped like one entry in `data/bidders.json` — i.e.
  exactly what your teammate's extractor is expected to eventually produce.
- `tender_requirements`: either the full tender dict (as in
  `tender_requirements.json`) or just the `requirements` list.
- `government_records`: the dict in `government_records.json` (mock today,
  a real government API/database lookup later — same shape).

`result` is a plain JSON-serializable dict (see "Output shape" below), so it
can be returned directly from a FastAPI route or dumped to a file.

**Swapping in the real extractor:** once your teammate's OCR/extraction
module is ready, replace the contents of `bidders.json` (or the in-memory
dict you build from an uploaded document) with its output — as long as it
uses the same field names (`pan.number`, `gst.status`, `turnover.annual_turnover`,
etc., documented via the `_scenario_note` examples in `bidders.json`), nothing
in `engine/` needs to change.

## How a decision is reached

For every requirement:

1. **Read** the relevant field out of the bidder's extracted data
   (`requirement_checker.py`). If it's not there at all → **MISSING**.
2. **Evaluate** the deterministic rule (`==`, `>=`, `contains`, `boolean`, ...)
   against the tender's required value/threshold → base **PASS** or **FAIL**.
3. **Cross-check** the same value against the mock government/reference
   record for that source (`government_checker.py` + `cross_verification.py`):
   - Government record agrees → status stands (PASS stays PASS, FAIL stays FAIL), evidence attached.
   - Government record is **unavailable** and the base result was PASS → downgraded to **REVIEW** ("can't independently verify").
   - Government record **disagrees** and the base result was PASS → downgraded to **REVIEW** ("self-declared says X, government says Y").
   - Government record disagrees and the base result was already FAIL → stays **FAIL**, with the disagreement noted as extra evidence.
4. Two special checks don't map to a single field:
   - **REQ-010 (blacklist)**: checked purely against the government
     `BLACKLIST` list by PAN and company name — never against bidder
     self-declared data (a company won't self-report being blacklisted).
   - **REQ-013 (legal name consistency)**: compares the legal name on PAN,
     GST, Udyam and the Certificate of Incorporation *within the bidder's
     own documents*. Names are normalized (case/whitespace/punctuation only
     — **no fuzzy matching**, so `Ltd` and `Limited` are still treated as
     different tokens on purpose) and a mismatch always produces **REVIEW**,
     never an automatic PASS or FAIL.

No ML/AI is used for these comparisons — `₹7 crore >= ₹5 crore` is a plain
deterministic rule and stays fully explainable. The engine is structured so
that an NLP layer could later be added *upstream* (e.g. to turn free-text
tender clauses into structured `requirement` rows) without touching this
comparison/scoring logic at all.

## Scoring rules

- `compliance_percentage` = PASS ÷ total requirements × 100.
- `summary` always separately shows `pass`, `fail`, `review`, `missing` —
  none of these are ever hidden inside the percentage.
- `mandatory_failure` is `true` if **any mandatory** requirement is FAIL,
  regardless of how high the overall percentage is (see the "Ganga Steel"
  bidder in the mock data: ~92% compliant but blacklisted → mandatory
  failure still shown).
- `mandatory_missing` is `true` if any mandatory requirement's data is MISSING.
- `overall_status` is a **visibility flag, not an automatic rejection**:
  `NON_COMPLIANT_MANDATORY_FAILURE` → `INCOMPLETE_MANDATORY_DATA_MISSING` →
  `NEEDS_MANUAL_REVIEW` → `COMPLIANT`, in that priority order. The tender
  owner (or a later rules layer) decides what to actually do with a bidder;
  this engine's job is to make every relevant fact visible with evidence.

## Output shape

```json
{
  "company_name": "Alpha Engineering Works Pvt Ltd",
  "tender_id": "TDR-DEMO-001",
  "compliance_percentage": 100.0,
  "summary": { "pass": 13, "fail": 0, "review": 0, "missing": 0, "total_requirements": 13 },
  "mandatory_failure": false,
  "mandatory_missing": false,
  "overall_status": "COMPLIANT",
  "requirements": [
    {
      "requirement_id": "REQ-001",
      "requirement_name": "GST Registration Active",
      "category": "STATUTORY",
      "mandatory": true,
      "verification_source": "GST",
      "status": "PASS",
      "extracted_value": "ACTIVE",
      "required_value": "ACTIVE",
      "government_value": "ACTIVE",
      "reason": "'gst.status' = 'ACTIVE' satisfies the requirement (== 'ACTIVE'). Confirmed against GST government record."
    }
  ]
}
```

## The 10 mock bidder scenarios

| # | Company | Scenario |
|---|---------|----------|
| 1 | Alpha Engineering Works Pvt Ltd | Fully compliant |
| 2 | Bharat Precision Tools Ltd | Turnover below ₹5 crore threshold |
| 3 | Chandra Fabrication Industries Pvt Ltd | GST inactive |
| 4 | Deccan Metal Works Pvt Ltd | Udyam legal-name mismatch → REVIEW |
| 5 | Everest Heavy Machinery Ltd | OEM authorization data missing |
| 6 | Fortune Industrial Solutions Pvt Ltd | Local content below 50% |
| 7 | Ganga Steel & Allied Industries Limited | Blacklisted (high score, still flagged) |
| 8 | Hind Auto Components Pvt Ltd | Government EPFO record unavailable → REVIEW |
| 9 | Indus Global Manufacturing Pvt Ltd | Multiple simultaneous inconsistencies |
| 10 | Jaipur Precision Castings Ltd | Compliant with one non-critical review item |

## Not included on purpose

OCR / PDF extraction, document upload UI, React frontend, authentication,
chatbot, payments, notifications, or unrelated ML models — per project scope.
This repo is only the requirements ↔ bidder data ↔ government data
comparison engine, ready to be called from a FastAPI backend.


## Current extractor integration

This version replaces the old extractor integration with the latest 15-document
BidGuard extractor under `extractor_engine/bidguard/`.

The current extractor provides:
- 15 document types
- PDF text extraction
- OCR fallback with Tesseract/Poppler
- document-specific extraction
- schema validation
- extraction metadata and warnings

### Run the existing mock compliance engine

```powershell
$env:GOV_SOURCE="supabase"
python main.py
```

This remains unchanged for regression testing.

### Run the real extractor -> verification -> compliance pipeline

Create a manifest using `integration/manifest_15_docs.example.json` and replace
the paths with the bidder's uploaded files.

```powershell
$env:GOV_SOURCE="supabase"
python scripts/run_extractor_compliance.py --manifest path\to\manifest.json
```

The result is written to:

```text
output/extractor_compliance_result.json
```

The result contains:
1. raw extraction results for every uploaded document
2. normalized bidder profile
3. Stage 1 document/reference verification
4. Stage 2 tender compliance
5. compliance score and reasons

### Important integration rule

The extractor is responsible for extraction/OCR only. Government/reference
verification and tender compliance remain in the compliance project. The
adapter never invents extracted values. Government values are only used for
reference verification/enrichment.

### Dependencies

The root `requirements.txt` now includes both the compliance engine and the
current extractor/OCR dependencies. Tesseract OCR and Poppler are external
system dependencies and must be installed on machines that need OCR fallback.
