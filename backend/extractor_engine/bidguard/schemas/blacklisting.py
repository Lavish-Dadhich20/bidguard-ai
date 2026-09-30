"""Schema for a Blacklisting / Debarment Declaration."""

DOCUMENT_TYPE = "BLACKLISTING_DECLARATION"

REQUIRED_FIELDS = [
    "bidder_name",
    "declaration_text",
    "blacklisting_status",
    "declaration_date",
]


def validate(fields):
    missing = [f for f in REQUIRED_FIELDS if fields.get(f) in (None, "")]
    status = (fields.get("blacklisting_status") or "").strip().lower()
    recognized = status in {
        "not blacklisted", "not debarred", "blacklisted", "debarred",
        "under debarment", "pending", "clear", "no"
    }
    return {
        "missing_fields": missing,
        "blacklisting_status_recognized": recognized,
    }
