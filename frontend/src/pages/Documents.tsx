import { useEffect, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import {
  Eye,
  FileText,
  RefreshCw,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";
import { supabase } from "../services/supabase";
import { api } from "../services/api";
import {
  DOCUMENT_TYPES,
  type DocumentRecord,
  type User,
} from "../types";
import {
  Page,
  Loading,
  ErrorState,
} from "../components/Page";
import { StatusBadge } from "../components/StatusBadge";

type LocalDocument = DocumentRecord & {
  previewUrl?: string;
};

const STORAGE_BUCKET = "bidder-documents";

// UI labels are intentionally kept separate from the document-type
// codes expected by the backend extractor.
const DOCUMENT_TYPE_CODES: Record<string, string> = {
  "Udyam Registration Certificate": "UDYAM",
  "GST Registration Certificate": "GST_REG_06",
  "GST Return Filing Record": "GST_RETURN",
  "PAN Card": "PAN",
  "Income Tax Return (ITR) Acknowledgement": "ITR",
  "Make in India / Local Content Declaration": "MAKE_IN_INDIA",
  "EPFO Registration & Compliance Record": "EPFO",
  "ESIC Registration & Compliance Record": "ESIC",
  "DPIIT Startup Recognition Certificate": "DPIIT_STARTUP",
  "NSIC Registration Certificate": "NSIC",
  "OEM Authorization Certificate/Letter": "OEM",
  "DigiLocker Document Verification Record": "DIGILOCKER",
  "Blacklisting/Debarment Declaration": "BLACKLISTING_DECLARATION",
  "Tender/Bid Compliance Declaration": "TENDER_BID_COMPLIANCE",
  "Certificate of Incorporation / Business Registration Certificate":
    "INCORPORATION",
};

const DOCUMENT_TYPE_LABELS: Record<string, string> =
  Object.fromEntries(
    Object.entries(DOCUMENT_TYPE_CODES).map(
      ([label, code]) => [code, label]
    )
  );

function toBackendDocumentType(type: string): string {
  return DOCUMENT_TYPE_CODES[type] || type;
}

function toDisplayDocumentType(type: string): string {
  return DOCUMENT_TYPE_LABELS[type] || type;
}

export function Documents({ user }: { user: User }) {
  const [documents, setDocuments] = useState<LocalDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [viewing, setViewing] =
    useState<LocalDocument | null>(null);

  const currentBidderId =
    user.id === "frontend-preview"
      ? "BID-DEMO-001"
      : user.bidderId || user.id;

  async function loadDocuments() {
    setLoading(true);
    setError("");

    try {
      const data = await api.getDocuments(
        currentBidderId
      );

      setDocuments(
        (data || []).map((document) => ({
          ...document,
          type: toDisplayDocumentType(document.type),
          status: document.status || "UPLOADED",
        }))
      );
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Unable to load saved documents."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, [currentBidderId]);

  async function handleUpload(
    type: string,
    file: File
  ) {
    setBusy(type);
    setError("");

    try {
      if (
        file.type !== "application/pdf" &&
        !file.name.toLowerCase().endsWith(".pdf")
      ) {
        throw new Error(
          "Only PDF files are supported for document verification."
        );
      }

      const savedDocument =
        await api.uploadDocument(
          currentBidderId,
          toBackendDocumentType(type),
          file
        );

      const updatedDocument: LocalDocument = {
        ...savedDocument,
        type: toDisplayDocumentType(
          savedDocument.type
        ),
        status:
          savedDocument.status || "VERIFIED",
      };

      setDocuments((current) => [
        ...current.filter(
          (doc) => doc.type !== type
        ),
        updatedDocument,
      ]);

      if (viewing?.type === type) {
        setViewing(null);
      }
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "The document could not be uploaded."
      );
    } finally {
      setBusy("");
    }
  }

  async function handleRemove(
    document: LocalDocument
  ) {
    if (!document.id) {
      return;
    }

    if (
      !confirm(
        `Remove "${document.fileName}"?`
      )
    ) {
      return;
    }

    setBusy(document.type);
    setError("");

    try {
      await api.removeDocument(document.id);

      setDocuments((current) =>
        current.filter(
          (doc) => doc.type !== document.type
        )
      );

      if (
        viewing?.type === document.type
      ) {
        setViewing(null);
      }
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "The document could not be removed."
      );
    } finally {
      setBusy("");
    }
  }

  async function openDocument(
    document: LocalDocument
  ) {
    if (!document.storagePath) {
      setError(
        "The stored file path is missing."
      );
      return;
    }

    setBusy(`view-${document.type}`);
    setError("");

    try {
      const {
        data,
        error: signedUrlError,
      } = await supabase.storage
        .from(STORAGE_BUCKET)
        .createSignedUrl(
          document.storagePath,
          60 * 10
        );

      if (
        signedUrlError ||
        !data?.signedUrl
      ) {
        throw (
          signedUrlError ||
          new Error(
            "Unable to create document URL."
          )
        );
      }

      setViewing({
        ...document,
        previewUrl: data.signedUrl,
      });
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "The document could not be opened."
      );
    } finally {
      setBusy("");
    }
  }

  function closeViewer() {
    setViewing(null);
  }

  return (
    <>
      <Page
        title="Document Upload & Management"
        description="Upload, view and update each of the 15 supported document types."
      >
        <div className="notice">
          <UploadCloud size={18} />

          <div>
            <strong>
              Persistent document storage
            </strong>

            <span>
              Uploaded documents are securely
              stored in Supabase and remain
              available for future use.
            </span>
          </div>
        </div>

        {loading ? (
          <Loading />
        ) : error ? (
          <ErrorState
            message={error}
            retry={() => {
              setError("");
              loadDocuments();
            }}
          />
        ) : (
          <div className="document-grid">
            {DOCUMENT_TYPES.map((type) => {
              const document =
                documents.find(
                  (doc) => doc.type === type
                );

              const isBusy =
                busy === type ||
                busy === `view-${type}`;

              return (
                <DocumentCard
                  key={type}
                  type={type}
                  document={document}
                  busy={isBusy}
                  onUpload={handleUpload}
                  onView={openDocument}
                  onRemove={handleRemove}
                />
              );
            })}
          </div>
        )}
      </Page>

      {viewing && (
        <DocumentViewer
          document={viewing}
          onClose={closeViewer}
        />
      )}
    </>
  );
}

function documentVisualState(
  document?: LocalDocument
): "pass" | "missing" | "invalid" {
  if (!document?.fileName) {
    return "missing";
  }

  const status = String(
    document.status || ""
  ).toUpperCase();

  if (
    [
      "VERIFIED",
      "UPLOADED",
      "PASS",
      "VALID",
    ].includes(status)
  ) {
    return "pass";
  }

  // Review is intentionally displayed as invalid/red.
  return "invalid";
}

function documentVisualLabel(
  state: "pass" | "missing" | "invalid"
) {
  if (state === "pass") {
    return "PASS";
  }

  if (state === "missing") {
    return "MISSING";
  }

  return "INVALID";
}

function DocumentCard({
  type,
  document,
  busy,
  onUpload,
  onView,
  onRemove,
}: {
  type: string;
  document?: LocalDocument;
  busy: boolean;
  onUpload: (
    type: string,
    file: File
  ) => void;
  onView: (
    document: LocalDocument
  ) => void;
  onRemove: (
    document: LocalDocument
  ) => void;
}) {
  const inputRef =
    useRef<HTMLInputElement | null>(null);

  function selectFile() {
    inputRef.current?.click();
  }

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    onUpload(type, file);

    event.target.value = "";
  }

  const visualState =
    documentVisualState(document);

  return (
    <div
      className={`document-card document-card--${visualState}`}
    >
      <div className="doc-top">
        <div className="doc-icon">
          <FileText size={19} />
        </div>

        <div>
          <strong>{type}</strong>

          <span>
            Document type supported by
            BidGuard AI
          </span>
        </div>
      </div>

      <div className="doc-meta">
        {document?.fileName ? (
          <>
            <span
              className="filename"
              title={document.fileName}
            >
              {document.fileName}
            </span>

            <StatusBadge
              value={documentVisualLabel(
                visualState
              )}
            />
          </>
        ) : (
          <StatusBadge value="MISSING" />
        )}
      </div>

      <div className="doc-actions">
        <button
          type="button"
          className="btn secondary"
          onClick={selectFile}
          disabled={busy}
        >
          {busy && !document ? (
            <>
              <span className="mini-spinner" />
              Uploading…
            </>
          ) : document ? (
            <>
              <RefreshCw size={15} />
              Update
            </>
          ) : (
            <>
              <UploadCloud size={15} />
              Upload
            </>
          )}
        </button>

        <input
          ref={inputRef}
          type="file"
          hidden
          onChange={handleFileChange}
          accept=".pdf,application/pdf"
        />

        <button
          type="button"
          className="icon-btn"
          title={
            document
              ? `View ${type}`
              : "Upload this document before viewing"
          }
          aria-label={`View ${type}`}
          disabled={!document || busy}
          onClick={() =>
            document &&
            onView(document)
          }
        >
          {busy && document ? (
            <span className="mini-spinner" />
          ) : (
            <Eye size={16} />
          )}
        </button>

        {document && (
          <button
            type="button"
            className="icon-btn danger"
            title={`Remove ${type}`}
            aria-label={`Remove ${type}`}
            disabled={busy}
            onClick={() =>
              onRemove(document)
            }
          >
            <Trash2 size={16} />
          </button>
        )}
      </div>
    </div>
  );
}

function DocumentViewer({
  document,
  onClose,
}: {
  document: LocalDocument;
  onClose: () => void;
}) {
  const previewUrl =
    document.previewUrl;

  if (!previewUrl) {
    return null;
  }

  const isImage =
    document.mimeType?.startsWith(
      "image/"
    ) ||
    /\.(jpg|jpeg|png|webp)$/i.test(
      document.fileName || ""
    );

  const isPdf =
    document.mimeType ===
      "application/pdf" ||
    document.fileName
      ?.toLowerCase()
      .endsWith(".pdf");

  return (
    <div
      className="document-modal-backdrop"
      onMouseDown={(event) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onClose();
        }
      }}
    >
      <div className="document-modal">
        <div className="document-modal-header">
          <div>
            <span className="section-kicker">
              DOCUMENT VIEWER
            </span>

            <h2>{document.type}</h2>

            <p>
              {document.fileName}
            </p>
          </div>

          <button
            type="button"
            className="icon-btn"
            onClick={onClose}
            aria-label="Close document viewer"
          >
            <X size={18} />
          </button>
        </div>

        <div className="document-preview">
          {isImage && (
            <img
              src={previewUrl}
              alt={document.type}
              className="document-preview-image"
            />
          )}

          {isPdf && (
            <iframe
              src={previewUrl}
              title={document.type}
              className="document-preview-frame"
            />
          )}

          {!isImage && !isPdf && (
            <div className="document-no-preview">
              <FileText size={36} />

              <h3>
                Preview unavailable
              </h3>

              <p>
                This file type cannot be
                previewed directly in the
                browser.
              </p>

              <a
                className="btn primary"
                href={previewUrl}
                target="_blank"
                rel="noreferrer"
              >
                Open File
              </a>
            </div>
          )}
        </div>

        <div className="document-modal-footer">
          <div>
            <strong>
              {document.fileName}
            </strong>

            <span>
              {document.fileSize
                ? `${(
                    document.fileSize /
                    1024 /
                    1024
                  ).toFixed(2)} MB`
                : "Unknown size"}

              {" · "}

              {document.mimeType ||
                "Unknown file type"}
            </span>
          </div>

          <a
            className="btn secondary"
            href={previewUrl}
            target="_blank"
            rel="noreferrer"
          >
            Open in New Tab
          </a>
        </div>
      </div>
    </div>
  );
}