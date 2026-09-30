"""
providers.py

Data providers for government/reference records.

Both providers expose the same two methods, so the compliance engine
does not care where the data lives:

    get_record(source, identifier) -> dict | None
    is_blacklisted(identifiers)    -> bool
"""

from typing import Any, Optional


class SupabaseProvider:
    def __init__(self, client, records_table: str = "government_records", blacklist_table: str = "blacklist"):
        self.client = client
        self.records_table = records_table
        self.blacklist_table = blacklist_table

    def get_record(self, source: str, identifier: Any) -> Optional[dict]:
        res = (
            self.client.table(self.records_table)
            .select("data")
            .eq("source", source)
            .eq("identifier", str(identifier).strip())
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return rows[0]["data"] if rows else None

    def is_blacklisted(self, identifiers: list) -> bool:
        cleaned = [str(i).strip().upper() for i in identifiers if i is not None]
        if not cleaned:
            return False
        res = self.client.table(self.blacklist_table).select("identifier").in_("identifier", cleaned).execute()
        return bool(res.data)


def create_supabase_provider() -> SupabaseProvider:
    """Build a provider from SUPABASE_URL / SUPABASE_SERVICE_KEY in .env."""
    import os
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file.")
    return SupabaseProvider(create_client(url, key))
