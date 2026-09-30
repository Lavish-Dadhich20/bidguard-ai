import json
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


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

results_path = BASE_DIR / "output" / "results.json"

if not results_path.exists():
    raise RuntimeError(f"Results file not found: {results_path}")

with open(results_path, "r", encoding="utf-8") as f:
    data = json.load(f)

results = data if isinstance(data, list) else data.get("results", [])

target = None

for result in results:
    if result.get("tender_id") == "TDR-DEMO-001":
        target = result
        break

if not target:
    raise RuntimeError(
        "TDR-DEMO-001 was not found in output/results.json"
    )

requirements = target.get("requirements", [])

if len(requirements) != 13:
    raise RuntimeError(
        f"Expected 13 compliance requirements, found {len(requirements)}"
    )

response = (
    supabase
    .table("tenders")
    .update({"requirements": requirements})
    .eq("id", "TDR-DEMO-001")
    .execute()
)

print()
print("=" * 60)
print("TENDER REQUIREMENTS UPDATED")
print("=" * 60)
print("Tender: TDR-DEMO-001")
print(f"Requirements added: {len(requirements)}")
print("=" * 60)
print()

for requirement in requirements:
    print(
        f"{requirement.get('requirement_id')}: "
        f"{requirement.get('requirement_name')}"
    )