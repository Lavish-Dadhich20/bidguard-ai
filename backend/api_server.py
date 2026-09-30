from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from supabase import create_client, Client

from engine.compliance_engine import evaluate_bidder
from engine.providers import create_supabase_provider
from integration.extractor_adapter import DOCUMENT_TYPES, extract_document

import tempfile
import re


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is missing from .env")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is missing from .env")


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="BidGuard AI API",
    version="1.0.0",
    description="BidGuard AI procurement bid compliance API",
)


# Frontend is running on the friend's computer.
# Allow local development requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://172.21.230.186:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HELPERS
# ============================================================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def normalize_user(row: dict[str, Any]) -> dict[str, Any]:
    result = {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
    }

    if row.get("role") == "BIDDER":
        try:
            bidder_response = (
                supabase
                .table("bidders")
                .select("id,company_name,phone")
                .eq("phone", row.get("username", ""))
                .limit(1)
                .execute()
            )
            if bidder_response.data:
                bidder = bidder_response.data[0]
                result["bidderId"] = bidder["id"]
                result["mobileNumber"] = bidder.get("phone")
                result["businessName"] = bidder.get("company_name")
        except Exception:
            pass

    return result


def get_user_by_username(username: str) -> Optional[dict[str, Any]]:
    response = (
        supabase
        .table("users")
        .select("*")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def get_user_by_id(user_id: str) -> Optional[dict[str, Any]]:
    response = (
        supabase
        .table("users")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def get_bidder(bidder_id: str) -> Optional[dict[str, Any]]:
    response = (
        supabase
        .table("bidders")
        .select("*")
        .eq("id", bidder_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def get_tender(tender_id: str) -> Optional[dict[str, Any]]:
    response = (
        supabase
        .table("tenders")
        .select("*")
        .eq("id", tender_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def load_local_json(filename: str) -> Any:
    path = PROJECT_ROOT / "data" / filename

    if not path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Required data file not found: {filename}",
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_government_records() -> dict:
    """
    Use the same Supabase government-data provider already used
    by the existing compliance engine.
    """
    provider = create_supabase_provider()
    return provider


def get_tender_requirements(tender_id: str) -> list[dict]:
    """
    Prefer the application's Supabase tender_requirements table.

    If no records exist there yet, fall back to the existing
    data/tender_requirements.json file.
    """

    response = (
        supabase
        .table("tender_requirements")
        .select("*")
        .eq("tender_id", tender_id)
        .order("id")
        .execute()
    )

    if response.data:
        requirements = []

        for row in response.data:
            requirements.append(
                {
                    "requirement_id": row["id"],
                    "requirement_name": row["requirement_name"],
                    "category": row.get("description") or "GENERAL",
                    "mandatory": row.get("mandatory", True),
                    "verification_source": None,
                    "operator": "field_present",
                }
            )

        return requirements

    # Fallback to original compliance-engine configuration.
    raw = load_local_json("tender_requirements.json")

    if isinstance(raw, dict):
        if "requirements" in raw:
            all_requirements = raw["requirements"]
        else:
            all_requirements = []
    else:
        all_requirements = raw

    return [
        requirement
        for requirement in all_requirements
        if requirement.get("tender_id") == tender_id
        or not requirement.get("tender_id")
    ]


def get_bidder_engine_data(bidder_id: str) -> dict:
    """
    Load the existing bidder data used by the compliance engine.

    The current engine works with the structured bidder JSON.
    We map the requested bidder ID to that existing data.
    """

    bidders = load_local_json("bidders.json")

    if not isinstance(bidders, list):
        raise HTTPException(
            status_code=500,
            detail="data/bidders.json must contain a list of bidders.",
        )

    for bidder in bidders:
        if bidder.get("bidder_id") == bidder_id:
            return bidder

        if bidder.get("id") == bidder_id:
            return bidder

    raise HTTPException(
        status_code=404,
        detail=f"Bidder {bidder_id} was not found in the compliance dataset.",
    )


# ============================================================
# REQUEST MODELS
# ============================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str


class ApplyRequest(BaseModel):
    pass


class VerifyRequest(BaseModel):
    tender_id: Optional[str] = None


class CreateTenderRequest(BaseModel):
    title: str
    description: Optional[str] = None
    organization: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    publish_date: Optional[str] = None
    submission_deadline: Optional[str] = None

class CreateBidderRequest(BaseModel):
    name: str
    businessName: str
    email: str
    mobile: str
    password: str


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "name": "BidGuard AI API",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "BidGuard AI API",
    }


# ============================================================
# AUTHENTICATION
# ============================================================

@app.post("/auth/login")
def login(payload: LoginRequest):

    user = get_user_by_username(payload.username)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    password_hash = hash_password(payload.password)

    if user["password_hash"] != password_hash:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    return normalize_user(user)


@app.post("/auth/logout")
def logout():
    return {"message": "Logged out successfully."}


@app.get("/auth/me")
def current_user():
    # The current frontend uses the returned user object directly.
    # Full persistent session handling will be added after the
    # API connection is verified.
    raise HTTPException(
        status_code=401,
        detail="No active API session.",
    )


@app.post("/auth/change-password")
def change_password(payload: ChangePasswordRequest):

    raise HTTPException(
        status_code=501,
        detail="Password change will be connected after authentication session wiring.",
    )


@app.delete("/auth/account")
def delete_account():
    raise HTTPException(
        status_code=501,
        detail="Account deletion is not enabled in the demo API.",
    )


# ============================================================
# TENDERS
# ============================================================

@app.get("/tenders")
def get_tenders():

    response = (
        supabase
        .table("tenders")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


@app.get("/tenders/{tender_id}")
def get_tender_by_id(tender_id: str):

    tender = get_tender(tender_id)

    if not tender:
        raise HTTPException(
            status_code=404,
            detail="Tender not found.",
        )

    return tender


@app.post("/tenders")
def create_tender(payload: CreateTenderRequest):

    tender_id = f"TDR-{os.urandom(4).hex().upper()}"

    row = {
        "id": tender_id,
        "title": payload.title,
        "description": payload.description,
        "organization": payload.organization,
        "category": payload.category,
        "location": payload.location,
        "publish_date": payload.publish_date,
        "submission_deadline": payload.submission_deadline,
        "status": "OPEN",
        "bidder_count": 0,
    }

    response = (
        supabase
        .table("tenders")
        .insert(row)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=500,
            detail="Unable to create tender.",
        )

    return response.data[0]


@app.post("/tenders/{tender_id}/apply")
def apply_for_tender(
    tender_id: str,
    bidder_id: str = Form(...),
):

    tender = get_tender(tender_id)

    if not tender:
        raise HTTPException(
            status_code=404,
            detail="Tender not found.",
        )

    bidder = get_bidder(bidder_id)

    if not bidder:
        raise HTTPException(
            status_code=404,
            detail="Bidder not found.",
        )

    application_id = f"APP-{os.urandom(4).hex().upper()}"

    row = {
        "id": application_id,
        "tender_id": tender_id,
        "bidder_id": bidder_id,
        "status": "APPLIED",
    }

    try:
        response = (
            supabase
            .table("tender_applications")
            .insert(row)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return response.data[0] if response.data else row


# ============================================================
# BIDDERS
# ============================================================

@app.post("/bidders")
def create_bidder(payload: CreateBidderRequest):
    mobile = payload.mobile.strip()

    if not re.fullmatch(r"[6-9]\d{9}", mobile):
        raise HTTPException(
            status_code=400,
            detail="Enter a valid 10-digit Indian mobile number.",
        )

    if len(payload.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters.",
        )

    existing_user = get_user_by_username(mobile)
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="A user with this mobile number already exists.",
        )

    existing_bidder = (
        supabase
        .table("bidders")
        .select("id")
        .eq("phone", mobile)
        .limit(1)
        .execute()
    )

    if existing_bidder.data:
        raise HTTPException(
            status_code=409,
            detail="A bidder with this mobile number already exists.",
        )

    bidder_id = f"BID-{os.urandom(4).hex().upper()}"

    try:
        bidder_response = (
            supabase
            .table("bidders")
            .insert({
                "id": bidder_id,
                "contact_person": payload.name.strip(),
                "company_name": payload.businessName.strip(),
                "email": payload.email.strip(),
                "phone": mobile,
                "status": "ACTIVE",
            })
            .execute()
        )

        if not bidder_response.data:
            raise HTTPException(
                status_code=500,
                detail="Unable to create bidder profile.",
            )

        user_response = (
            supabase
            .table("users")
            .insert({
                "username": mobile,
                "password_hash": hash_password(payload.password),
                "name": payload.name.strip(),
                "email": payload.email.strip(),
                "role": "BIDDER",
            })
            .execute()
        )

        if not user_response.data:
            try:
                supabase.table("bidders").delete().eq("id", bidder_id).execute()
            except Exception:
                pass
            raise HTTPException(
                status_code=500,
                detail="Unable to create bidder login account.",
            )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to create bidder account: {exc}",
        )

    return {
        "id": bidder_id,
        "name": payload.name.strip(),
        "businessName": payload.businessName.strip(),
        "email": payload.email.strip(),
        "mobile": mobile,
        "status": "ACTIVE",
    }


@app.get("/bidders")
def get_bidders():

    response = (
        supabase
        .table("bidders")
        .select("*")
        .order("created_at")
        .execute()
    )

    return response.data or []


@app.get("/bidders/{bidder_id}")
def get_bidder_by_id(bidder_id: str):

    bidder = get_bidder(bidder_id)

    if not bidder:
        raise HTTPException(
            status_code=404,
            detail="Bidder not found.",
        )

    return bidder


# ============================================================
# DOCUMENTS
# ============================================================

@app.get("/bidders/{bidder_id}/documents")
def get_documents(
    bidder_id: str,
    tender_id: Optional[str] = None,
):

    query = (
        supabase
        .table("bidder_documents")
        .select(
            "id,bidder_id,document_type,file_name,"
            "storage_path,mime_type,file_size,uploaded_at,updated_at"
        )
        .eq("bidder_id", bidder_id)
    )

    response = query.order(
        "uploaded_at",
        desc=True,
    ).execute()

    return [
        {
            "id": row["id"],
            "type": row["document_type"],
            "fileName": row["file_name"],
            "status": "UPLOADED",
            "uploadedAt": row["uploaded_at"],
            "storagePath": row["storage_path"],
            "mimeType": row.get("mime_type"),
            "fileSize": row.get("file_size"),
        }
        for row in (response.data or [])
    ]


def validate_extraction(document_type: str, extraction: dict) -> tuple[bool, str]:
    """Validate that the selected document type was actually extracted.

    This does not replace the existing extractor. It only checks the extractor
    output for the identifying fields that belong to the selected document.
    """
    fields = extraction.get("fields") or {}
    metadata = extraction.get("metadata") or {}

    required_any = {
        "GST_REG_06": ["gstin", "legal_name"],
        "PAN": ["pan_number"],
        "UDYAM": ["udyam_registration_number", "enterprise_name"],
        "ITR": ["acknowledgement_number", "assessment_year"],
        "OEM": ["authorized_bidder_name", "authorization_letter_number"],
        "EPFO": ["epfo_establishment_code", "establishment_name"],
        "ESIC": ["esic_registration_number", "establishment_name"],
        "GST_RETURN": ["gstin", "filing_status", "acknowledgement_number"],
        "MAKE_IN_INDIA": ["local_content_percentage", "local_content_category", "declaration_date"],
        "DPIIT_STARTUP": ["recognition_number", "startup_name"],
        "NSIC": ["registration_number", "enterprise_name"],
        "DIGILOCKER": ["verification_id", "verification_status"],
        "BLACKLISTING_DECLARATION": ["blacklisting_status", "declaration_text", "bidder_name"],
        "TENDER_BID_COMPLIANCE": ["tender_reference", "compliance_status", "declaration_text"],
        "INCORPORATION": ["cin_or_registration_number", "legal_name"],
    }

    expected = required_any.get(document_type)
    if not expected:
        return False, f"Unsupported document type: {document_type}"

    present = [key for key in expected if fields.get(key) not in (None, "", [])]
    if not present:
        return False, (
            f"The uploaded file does not appear to be a valid {document_type} document. "
            f"Expected identifying fields were not extracted."
        )

    warnings = metadata.get("warnings") or []
    if isinstance(warnings, list) and len(warnings) >= 3 and not present:
        return False, f"The extractor could not reliably identify this as {document_type}."

    return True, f"{document_type} document validated successfully."


async def _extract_and_validate_upload(contents: bytes, document_type: str, filename: str) -> dict:
    """Run the existing extractor against an uploaded file before storage."""
    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported document type '{document_type}'. "
                f"Supported types: {', '.join(DOCUMENT_TYPES.keys())}"
            ),
        )

    suffix = Path(filename or "document.pdf").suffix or ".pdf"
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name

        try:
            extraction = extract_document(temp_path, document_type)
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Document extraction failed for {document_type}: {exc}",
            )

        valid, reason = validate_extraction(document_type, extraction)
        if not valid:
            raise HTTPException(status_code=422, detail=reason)

        return {
            "document_type": document_type,
            "message": reason,
            "fields": extraction.get("fields") or {},
            "metadata": extraction.get("metadata") or {},
        }
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass


@app.post("/bidders/{bidder_id}/documents")
async def upload_document(
    bidder_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    tender_id: Optional[str] = Form(None),
):

    bidder = get_bidder(bidder_id)

    if not bidder:
        raise HTTPException(
            status_code=404,
            detail="Bidder not found.",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF documents are supported.",
        )

    # Validate the selected document type BEFORE saving it to Supabase.
    extraction = await _extract_and_validate_upload(
        contents,
        document_type,
        file.filename or "document.pdf",
    )

    safe_name = (
        file.filename or "document"
    ).replace(" ", "_")

    storage_path = (
        f"{bidder_id}/"
        f"{document_type}/"
        f"{os.urandom(6).hex()}_{safe_name}"
    )

    try:
        supabase.storage.from_("bidder-documents").upload(
            storage_path,
            contents,
            {
                "content-type": file.content_type
                or "application/pdf"
            },
        )

        existing = (
            supabase
            .table("bidder_documents")
            .select("*")
            .eq("bidder_id", bidder_id)
            .eq("document_type", document_type)
            .limit(1)
            .execute()
        )

        metadata = {
            "bidder_id": bidder_id,
            "document_type": document_type,
            "file_name": file.filename or safe_name,
            "storage_path": storage_path,
            "mime_type": file.content_type or "application/pdf",
            "file_size": len(contents),
        }

        if existing.data:
            old_path = existing.data[0]["storage_path"]

            supabase.table("bidder_documents").update(
                metadata
            ).eq(
                "id",
                existing.data[0]["id"],
            ).execute()

            try:
                supabase.storage.from_("bidder-documents").remove([old_path])
            except Exception:
                pass
        else:
            supabase.table("bidder_documents").insert(metadata).execute()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document upload failed: {exc}",
        )

    return {
        "type": document_type,
        "fileName": file.filename,
        "status": "UPLOADED",
        "storagePath": storage_path,
        "mimeType": file.content_type or "application/pdf",
        "fileSize": len(contents),
        "extraction": extraction,
    }


@app.put("/documents/{document_id}")
async def replace_document(
    document_id: str,
    file: UploadFile = File(...),
):

    existing = (
        supabase
        .table("bidder_documents")
        .select("*")
        .eq("id", document_id)
        .limit(1)
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    old = existing.data[0]

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF documents are supported.",
        )

    # Keep the original document type when replacing a document.
    extraction = await _extract_and_validate_upload(
        contents,
        old["document_type"],
        file.filename or "document.pdf",
    )

    safe_name = (
        file.filename or "document"
    ).replace(" ", "_")

    new_path = (
        f"{old['bidder_id']}/"
        f"{old['document_type']}/"
        f"{os.urandom(6).hex()}_{safe_name}"
    )

    try:
        supabase.storage.from_("bidder-documents").upload(
            new_path,
            contents,
            {
                "content-type": file.content_type
                or "application/pdf"
            },
        )

        update_data = {
            "file_name": file.filename or safe_name,
            "storage_path": new_path,
            "mime_type": file.content_type or "application/pdf",
            "file_size": len(contents),
        }

        response = (
            supabase
            .table("bidder_documents")
            .update(update_data)
            .eq("id", document_id)
            .execute()
        )

        try:
            supabase.storage.from_("bidder-documents").remove([old["storage_path"]])
        except Exception:
            pass

        return {
            **(response.data[0] if response.data else update_data),
            "extraction": extraction,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document replacement failed: {exc}",
        )


@app.delete("/documents/{document_id}")
def remove_document(document_id: str):

    existing = (
        supabase
        .table("bidder_documents")
        .select("*")
        .eq("id", document_id)
        .limit(1)
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    row = existing.data[0]

    try:
        supabase.storage.from_(
            "bidder-documents"
        ).remove([row["storage_path"]])
    except Exception:
        pass

    (
        supabase
        .table("bidder_documents")
        .delete()
        .eq("id", document_id)
        .execute()
    )

    return {
        "message": "Document deleted successfully."
    }


# ============================================================
# VERIFICATION / COMPLIANCE
# ============================================================

@app.post("/bidders/{bidder_id}/verify")
def verify_bidder(
    bidder_id: str,
    payload: VerifyRequest,
):

    bidder = get_bidder(bidder_id)

    if not bidder:
        raise HTTPException(
            status_code=404,
            detail="Bidder not found.",
        )

    tender_id = payload.tender_id

    if not tender_id:
        raise HTTPException(
            status_code=400,
            detail="tender_id is required for verification.",
        )

    tender = get_tender(tender_id)

    if not tender:
        raise HTTPException(
            status_code=404,
            detail="Tender not found.",
        )

    bidder_data = get_bidder_engine_data(bidder_id)

    requirements = get_tender_requirements(tender_id)

    government_records = get_government_records()

    result = evaluate_bidder(
        bidder_data,
        {
            "tender_id": tender_id,
            "requirements": requirements,
        },
        government_records,
    )

    supabase.table("verification_results").insert(
        {
            "bidder_id": bidder_id,
            "tender_id": tender_id,
            "compliance_percentage": result[
                "compliance_percentage"
            ],
            "overall_status": result["overall_status"],
            "summary": result["summary"],
            "result_data": result,
        }
    ).execute()

    return result


@app.get("/bidders/{bidder_id}/verification")
def get_verification_result(
    bidder_id: str,
    tender_id: Optional[str] = None,
):

    query = (
        supabase
        .table("verification_results")
        .select("*")
        .eq("bidder_id", bidder_id)
    )

    if tender_id:
        query = query.eq("tender_id", tender_id)

    response = (
        query
        .order("verified_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="No verification result found.",
        )

    row = response.data[0]

    if row.get("result_data"):
        return row["result_data"]

    return row


@app.get("/bidders/{bidder_id}/compliance")
def get_compliance_result(
    bidder_id: str,
    tender_id: Optional[str] = None,
):

    query = (
        supabase
        .table("verification_results")
        .select("*")
        .eq("bidder_id", bidder_id)
    )

    if tender_id:
        query = query.eq("tender_id", tender_id)

    response = (
        query
        .order("verified_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="No compliance result found.",
        )

    row = response.data[0]

    if row.get("result_data"):
        return row["result_data"]

    return row


@app.get("/tenders/{tender_id}/compliance")
def tender_compliance(tender_id: str):

    response = (
        supabase
        .table("verification_results")
        .select("*")
        .eq("tender_id", tender_id)
        .order("verified_at", desc=True)
        .execute()
    )

    results = []

    seen_bidders = set()

    for row in response.data or []:

        bidder_id = row["bidder_id"]

        if bidder_id in seen_bidders:
            continue

        seen_bidders.add(bidder_id)

        bidder = get_bidder(bidder_id)

        results.append(
            {
                "bidder": bidder,
                "compliance": row.get("result_data") or row,
            }
        )

    return results


# ============================================================
# REPORTS
# ============================================================

@app.get("/reports")
def reports():

    response = (
        supabase
        .table("verification_results")
        .select("*")
        .order("verified_at", desc=True)
        .execute()
    )

    return response.data or []


# ============================================================
# AUDIT TRAIL
# ============================================================

@app.get("/audit-trail")
def audit_trail():

    response = (
        supabase
        .table("audit_trail")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():

    print()
    print("=" * 60)
    print("        BIDGUARD AI API SERVER")
    print("=" * 60)
    print(f"Supabase: {SUPABASE_URL}")
    print("API status: READY")
    print("=" * 60)
    print()