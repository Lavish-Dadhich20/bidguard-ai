"""Load data/government_records.json into Supabase (safe to re-run: it upserts)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "government_records.json")
gov = json.load(open(path, encoding="utf-8"))

rows = [
    {"source": source, "identifier": ident, "data": data}
    for source, table in gov.items() if source != "BLACKLIST"
    for ident, data in table.items()
]
client.table("government_records").upsert(rows).execute()
print(f"Upserted {len(rows)} government records")

bl = [{"identifier": i.strip().upper(), "reason": "Mock debarment entry"} for i in gov.get("BLACKLIST", [])]
if bl:
    client.table("blacklist").upsert(bl).execute()
print(f"Upserted {len(bl)} blacklist entries")
