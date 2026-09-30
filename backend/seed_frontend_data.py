import json
import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import create_client


# ============================================================
# BidGuard AI - Frontend Application Data Seeder
# ============================================================
# This script ONLY seeds the frontend/application tables.
# It does NOT modify the extractor or compliance engine.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is missing from .env")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is missing from .env")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)


def load_json(relative_path: str):
    path = BASE_DIR / relative_path

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sha256_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def first_value(data, *keys, default=None):
    if not isinstance(data, dict):
        return default

    for key in keys:
        value = data.get(key)

        if value is not None and value != "":
            return value

    return default


def extract_company_name(bidder):
    if not isinstance(bidder, dict):
        return None

    return first_value(
        bidder,
        "company_name",
        "company",
        "name",
        "legal_name",
        default="Unknown Bidder",
    )


def extract_bidder_id(bidder, index):
    if isinstance(bidder, dict):
        value = first_value(
            bidder,
            "bidder_id",
            "id",
            "bidderId",
        )

        if value:
            return str(value)

    return f"BID-DEMO-{index:03d}"


def normalize_requirements(raw):
    if isinstance(raw, dict):
        requirements = raw.get("requirements", [])
    elif isinstance(raw, list):
        requirements = raw
    else:
        requirements = []

    return requirements


def main():

    print()
    print("=" * 60)
    print("        BIDGUARD AI FRONTEND DATA SEEDER")
    print("=" * 60)

    # --------------------------------------------------------
    # Load existing project data
    # --------------------------------------------------------

    bidders_raw = load_json("data/bidders.json")
    requirements_raw = load_json("data/tender_requirements.json")
    results_raw = load_json("output/results.json")

    if isinstance(bidders_raw, dict):
        bidders = bidders_raw.get("bidders", [])
    else:
        bidders = bidders_raw

    requirements = normalize_requirements(requirements_raw)

    if not isinstance(results_raw, list):
        results = results_raw.get("results", [])
    else:
        results = results_raw

    print(f"Existing bidders loaded: {len(bidders)}")
    print(f"Existing requirements loaded: {len(requirements)}")
    print(f"Existing compliance results loaded: {len(results)}")

    # --------------------------------------------------------
    # Tender information
    # --------------------------------------------------------

    tender_id = "TDR-DEMO-001"

    tender = {
        "id": tender_id,
        "title": "Supply of Industrial Equipment",
        "description": (
            "Demo procurement tender used for BidGuard AI "
            "compliance verification."
        ),
        "organization": "Government Procurement Department",
        "category": "Industrial Equipment",
        "location": "Rajasthan",
        "status": "OPEN",
        "bidder_count": len(results),
    }

    supabase.table("tenders").upsert(
        tender,
        on_conflict="id",
    ).execute()

    print(f"✓ Tender seeded: {tender_id}")

    # --------------------------------------------------------
    # Tender requirements
    # --------------------------------------------------------

    requirement_rows = []

    for index, requirement in enumerate(requirements, start=1):

        if not isinstance(requirement, dict):
            continue

        requirement_id = str(
            requirement.get(
                "requirement_id",
                f"REQ-{index:03d}",
            )
        )

        requirement_name = requirement.get(
            "requirement_name",
            requirement.get(
                "name",
                "Requirement",
            ),
        )

        document_type = requirement.get(
            "document_type",
            requirement.get(
                "document",
                requirement_id,
            ),
        )

        requirement_rows.append(
            {
                "id": requirement_id,
                "tender_id": tender_id,
                "document_type": str(document_type),
                "requirement_name": str(requirement_name),
                "description": requirement.get(
                    "description",
                    requirement.get(
                        "reason",
                        "",
                    ),
                ),
                "mandatory": bool(
                    requirement.get(
                        "mandatory",
                        True,
                    )
                ),
            }
        )

    if requirement_rows:
        supabase.table("tender_requirements").upsert(
            requirement_rows,
            on_conflict="id",
        ).execute()

    print(
        f"✓ Tender requirements seeded: "
        f"{len(requirement_rows)}"
    )

    # --------------------------------------------------------
    # Users + bidders
    # --------------------------------------------------------

    bidder_rows = []
    user_rows = []
    application_rows = []

    # Results contain the compliance output and therefore give
    # us the exact bidder names used by the existing engine.

    result_by_company = {}

    for result in results:
        if not isinstance(result, dict):
            continue

        company_name = result.get("company_name")

        if company_name:
            result_by_company[
                str(company_name).strip().lower()
            ] = result

    # Use the actual bidders.json records when available.
    source_bidders = bidders if bidders else []

    # If bidders.json has no usable list, derive bidder names
    # from the existing compliance results.
    if not source_bidders:
        source_bidders = [
            {
                "company_name": result.get("company_name"),
                "bidder_id": f"BID-DEMO-{index:03d}",
            }
            for index, result in enumerate(
                results,
                start=1,
            )
        ]

    for index, bidder in enumerate(
        source_bidders,
        start=1,
    ):

        company_name = extract_company_name(bidder)

        if not company_name:
            continue

        bidder_id = extract_bidder_id(
            bidder,
            index,
        )

        # Keep IDs simple and stable for the demo.
        bidder_id = str(bidder_id)

        user_id = f"USER-{bidder_id}"

        email = (
            f"bidder{index}@bidguard.demo"
        )

        username = (
            f"bidder{index}"
        )

        # Demo password.
        # This is only for the hackathon/demo environment.
        password_hash = sha256_password(
            "BidGuard@123"
        )

        user_rows.append(
            {
                "id": user_id,
                "name": company_name,
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "role": "BIDDER",
            }
        )

        bidder_rows.append(
            {
                "id": bidder_id,
                "user_id": user_id,
                "company_name": company_name,
                "contact_person": first_value(
                    bidder,
                    "contact_person",
                    "contactPerson",
                    "representative",
                ),
                "email": first_value(
                    bidder,
                    "email",
                    "contact_email",
                    default=email,
                ),
                "phone": first_value(
                    bidder,
                    "phone",
                    "mobile",
                ),
                "pan": first_value(
                    bidder,
                    "pan",
                    "pan_number",
                ),
                "gstin": first_value(
                    bidder,
                    "gstin",
                    "gstin_number",
                ),
                "udyam_number": first_value(
                    bidder,
                    "udyam_number",
                    "udyam",
                    "udyam_registration_number",
                ),
                "status": "ACTIVE",
            }
        )

        application_rows.append(
            {
                "id": f"APP-{bidder_id}-{tender_id}",
                "tender_id": tender_id,
                "bidder_id": bidder_id,
                "status": "APPLIED",
            }
        )

    if user_rows:
        supabase.table("users").upsert(
            user_rows,
            on_conflict="id",
        ).execute()

    if bidder_rows:
        supabase.table("bidders").upsert(
            bidder_rows,
            on_conflict="id",
        ).execute()

    if application_rows:
        supabase.table("tender_applications").upsert(
            application_rows,
            on_conflict="id",
        ).execute()

    print(
        f"✓ Users seeded: {len(user_rows)}"
    )

    print(
        f"✓ Bidders seeded: {len(bidder_rows)}"
    )

    print(
        f"✓ Tender applications seeded: "
        f"{len(application_rows)}"
    )

    # --------------------------------------------------------
    # Verification results
    # --------------------------------------------------------

    verification_rows = []

    bidder_lookup = {
        str(row["company_name"]).strip().lower(): row["id"]
        for row in bidder_rows
    }

    for result in results:

        if not isinstance(result, dict):
            continue

        company_name = result.get(
            "company_name"
        )

        if not company_name:
            continue

        bidder_id = bidder_lookup.get(
            str(company_name).strip().lower()
        )

        if not bidder_id:
            continue

        summary = result.get(
            "summary",
            {},
        )

        verification_rows.append(
            {
                "bidder_id": bidder_id,
                "tender_id": tender_id,
                "compliance_percentage": result.get(
                    "compliance_percentage"
                ),
                "overall_status": result.get(
                    "overall_status"
                ),
                "summary": summary,
                "result_data": result,
                "verified_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        )

    if verification_rows:

        # Remove old demo verification rows first so
        # repeated runs don't create duplicates.

        supabase.table(
            "verification_results"
        ).delete().eq(
            "tender_id",
            tender_id,
        ).execute()

        supabase.table(
            "verification_results"
        ).insert(
            verification_rows
        ).execute()

    print(
        f"✓ Verification results seeded: "
        f"{len(verification_rows)}"
    )

    # --------------------------------------------------------
    # Audit trail
    # --------------------------------------------------------

    audit_row = {
        "action": "SEED_FRONTEND_DEMO_DATA",
        "entity_type": "SYSTEM",
        "entity_id": tender_id,
        "details": {
            "tender_id": tender_id,
            "bidders": len(bidder_rows),
            "requirements": len(requirement_rows),
            "verification_results": len(
                verification_rows
            ),
            "source": "existing_bidguard_demo_data",
        },
    }

    supabase.table(
        "audit_trail"
    ).insert(
        audit_row
    ).execute()

    print("✓ Audit trail entry created")

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    tender_check = (
        supabase.table("tenders")
        .select("id,title,bidder_count")
        .eq("id", tender_id)
        .execute()
    )

    bidder_check = (
        supabase.table("bidders")
        .select("id,company_name")
        .execute()
    )

    result_check = (
        supabase.table("verification_results")
        .select(
            "bidder_id,tender_id,"
            "compliance_percentage,overall_status"
        )
        .eq("tender_id", tender_id)
        .execute()
    )

    print()
    print("=" * 60)
    print("                 SEED COMPLETE")
    print("=" * 60)

    print(
        f"Tenders in database: "
        f"{len(tender_check.data or [])}"
    )

    print(
        f"Bidders in database: "
        f"{len(bidder_check.data or [])}"
    )

    print(
        f"Verification results: "
        f"{len(result_check.data or [])}"
    )

    print("=" * 60)
    print()
    print(
        "Demo bidder login password: BidGuard@123"
    )
    print()


if __name__ == "__main__":
    main()