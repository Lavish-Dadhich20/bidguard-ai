import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";

import { api } from "../services/api";
import type { Role, Tender, User } from "../types";
import { Page, Loading, ErrorState, EmptyState } from "../components/Page";

type TenderRequirement = {
  id?: string;
  requirement_id?: string;
  requirement?: string;
  requirement_name?: string;
  category?: string;
  mandatory?: boolean;
  verification_source?: string;
  required_value?: string | number | null;

  operator?: string;
  condition?: string;
  requiredValue?: string | number | null;
};

function formatValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "number") {
    return value.toLocaleString("en-IN");
  }

  return String(value);
}

export function TenderDetails({ role, user }: { role: Role; user?: User }) {
  const { id = "" } = useParams();

  const [tender, setTender] = useState<Tender | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");

    api
      .getTender(id)
      .then(setTender)
      .catch((e) =>
        setError(
          e instanceof Error ? e.message : "Unable to load tender."
        )
      )
      .finally(() => setLoading(false));
  }, [id]);

  async function apply() {
    if (!confirm("Are you sure you want to apply for this tender?")) {
      return;
    }

    setBusy(true);
    setMessage("");

    try {
      const bidderId = user?.id === "frontend-preview" ? "BID-DEMO-001" : user?.id;
      if (!bidderId) throw new Error("Bidder account could not be identified.");
      await api.applyForTender(id, bidderId);

      // The backend may return an object, so show a fixed
      // human-readable success message instead of rendering it.
      setMessage("Successfully applied for this tender.");
    } catch (e) {
      setMessage(
        e instanceof Error ? e.message : "Application failed."
      );
    } finally {
      setBusy(false);
    }
  }

  const requirements =
    ((tender?.requirements ?? []) as unknown) as TenderRequirement[];

  return (
    <Page
      title="Tender Details"
      description="Tender information and requirements returned by the backend."
    >
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState
          message={error}
          retry={() => window.location.reload()}
        />
      ) : !tender ? (
        <EmptyState
          title="Tender unavailable"
          description="The backend did not return this tender."
        />
      ) : (
        <>
          {message && (
            <div className="success-banner">
              <CheckCircle2 size={18} />
              <span>{message}</span>
            </div>
          )}

          <div className="detail-grid">
            {[
              ["Tender ID", tender.id],
              ["Tender Reference", tender.reference],
              ["Tender Title", tender.title],
              ["Organization", tender.organization],
              ["Category", tender.category],
              ["Tender Value", tender.tenderValue],
              ["Deadline", tender.deadline],
              ["Bidder Type", tender.bidderType],
            ].map(([key, value]) => (
              <div className="detail-field" key={String(key)}>
                <span>{key}</span>
                <strong>{value || "—"}</strong>
              </div>
            ))}
          </div>

          <div className="panel">
            <div className="panel-header">
              <h2>Requirements</h2>
            </div>

            {requirements.length > 0 ? (
              <div className="requirement-list">
                {requirements.map((requirement, index) => {
                  const name =
                    requirement.requirement_name ||
                    requirement.requirement ||
                    "Requirement";

                  const requirementId =
                    requirement.requirement_id ||
                    requirement.id ||
                    `REQ-${String(index + 1).padStart(3, "0")}`;

                  const value =
                    requirement.required_value ??
                    requirement.requiredValue;

                  const condition =
                    requirement.operator ||
                    requirement.condition ||
                    "";

                  return (
                    <div
                      className="requirement"
                      key={requirementId}
                    >
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "6px",
                          flex: 1,
                          minWidth: 0,
                        }}
                      >
                        <strong>
                          {requirementId}: {name}
                        </strong>

                        <div
                          style={{
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "16px",
                            fontSize: "13px",
                          }}
                        >
                          {requirement.category && (
                            <span>
                              <strong>Category:</strong>{" "}
                              {requirement.category}
                            </span>
                          )}

                          {requirement.verification_source && (
                            <span>
                              <strong>Verification:</strong>{" "}
                              {requirement.verification_source}
                            </span>
                          )}
                        </div>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "flex-end",
                          gap: "6px",
                          minWidth: "130px",
                          marginLeft: "20px",
                        }}
                      >
                        {requirement.mandatory !== undefined && (
                          <span
                            style={{
                              fontSize: "13px",
                              fontWeight: 600,
                            }}
                          >
                            {requirement.mandatory
                              ? "Mandatory"
                              : "Optional"}
                          </span>
                        )}

                        {(condition || value !== undefined) && (
                          <span
                            style={{
                              fontSize: "13px",
                              fontWeight: 600,
                            }}
                          >
                            {condition && `${condition} `}
                            {formatValue(value)}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                title="No requirements returned"
                description="Requirements will appear here when supplied by the backend."
              />
            )}
          </div>

          {role === "BIDDER" && (
            <button
              className="btn primary"
              disabled={busy}
              onClick={apply}
            >
              {busy ? "Applying…" : "Apply for Tender"}
            </button>
          )}
        </>
      )}
    </Page>
  );
}