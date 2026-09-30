"""Schema for a DigiLocker Document Verification Record."""

DOCUMENT_TYPE = "DIGILOCKER"

REQUIRED_FIELDS = [
    "verification_id",
    "document_type",
    "issuer",
    "document_number",
    "holder_name",
    "verification_date",
    "verification_status",
]


def validate(fields):
    missing = [f for f in REQUIRED_FIELDS if fields.get(f) in (None, "")]
    status = (fields.get("verification_status") or "").strip().lower()
    recognized = status in {
        "verified", "valid", "success", "successful",
        "failed", "invalid", "pending", "not verified"
    }
    return {
        "missing_fields": missing,
        "verification_status_recognized": recognized,
    }
