import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent


@router.get("/tenders/{tender_id}/requirements")
def get_tender_requirements(tender_id: str):
    requirements_file = BASE_DIR / "output" / "results.json"

    if not requirements_file.exists():
        requirements_file = BASE_DIR / "data" / "tender_requirements.json"

    with open(requirements_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Use the actual compliance-engine results.
    if isinstance(data, list):
        results = data
    else:
        results = data.get("results", [])

    for result in results:
        if result.get("tender_id") == tender_id:
            requirements = result.get("requirements", [])

            return {
                "tender_id": tender_id,
                "requirements": requirements
            }

    return {
        "tender_id": tender_id,
        "requirements": []
    }