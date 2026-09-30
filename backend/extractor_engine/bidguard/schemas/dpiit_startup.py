"""Schema for a DPIIT Startup Recognition Certificate."""

DOCUMENT_TYPE = "DPIIT_STARTUP"

REQUIRED_FIELDS = [
    "recognition_number",
    "startup_name",
    "date_of_recognition",
    "entity_type",
    "state",
    "recognition_status",
]


def validate(fields):
    missing = [f for f in REQUIRED_FIELDS if fields.get(f) in (None, "")]
    return {
        "missing_fields": missing,
        "recognition_status_present": bool(fields.get("recognition_status")),
    }
