"""
main.py

Run:
    python main.py

Loads:
    data/tender_requirements.json
    data/bidders.json
    data/government_records.json

Produces:
    output/results.json   -- full detailed result for every bidder
    output/summary.csv     -- one-row-per-company summary table

Also prints a human-readable summary table to the console.
"""

import csv
import json
import os

from engine.compliance_engine import evaluate_all_bidders

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def load_json(filename: str):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_summary_table(results: list) -> None:
    header = f"{'Company':<42} {'PASS':>4} {'FAIL':>4} {'REVIEW':>6} {'MISS':>4} {'%':>6}  {'MANDATORY FAIL':<15} Overall Status"
    print(header)
    print("-" * len(header))
    for r in results:
        s = r["summary"]
        print(
            f"{r['company_name'][:42]:<42} "
            f"{s['pass']:>4} {s['fail']:>4} {s['review']:>6} {s['missing']:>4} "
            f"{r['compliance_percentage']:>5.1f}%  "
            f"{str(r['mandatory_failure']):<15} {r['overall_status']}"
        )


def write_summary_csv(results: list, path: str) -> None:
    fieldnames = [
        "company_name",
        "tender_id",
        "pass",
        "fail",
        "review",
        "missing",
        "compliance_percentage",
        "mandatory_failure",
        "mandatory_missing",
        "overall_status",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            s = r["summary"]
            writer.writerow(
                {
                    "company_name": r["company_name"],
                    "tender_id": r["tender_id"],
                    "pass": s["pass"],
                    "fail": s["fail"],
                    "review": s["review"],
                    "missing": s["missing"],
                    "compliance_percentage": r["compliance_percentage"],
                    "mandatory_failure": r["mandatory_failure"],
                    "mandatory_missing": r["mandatory_missing"],
                    "overall_status": r["overall_status"],
                }
            )


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    tender = load_json("tender_requirements.json")
    bidders = load_json("bidders.json")
    if os.getenv("GOV_SOURCE", "json").lower() == "supabase":
        from engine.providers import create_supabase_provider
        government_records = create_supabase_provider()
        print("Government data source: Supabase")
    else:
        government_records = load_json("government_records.json")
        print("Government data source: local JSON")

    print(f"Tender: {tender['tender_id']} - {tender['tender_title']}")
    print(f"Requirements: {len(tender['requirements'])}   Bidders: {len(bidders)}\n")

    results = evaluate_all_bidders(bidders, tender, government_records)

    results_path = os.path.join(OUTPUT_DIR, "results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    summary_path = os.path.join(OUTPUT_DIR, "summary.csv")
    write_summary_csv(results, summary_path)

    print_summary_table(results)

    print(f"\nDetailed results written to: {results_path}")
    print(f"Summary table written to:    {summary_path}")


if __name__ == "__main__":
    main()
