import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../services/api";
import type { Bidder, ComplianceResult } from "../types";
import {
  Page,
  Loading,
  ErrorState,
  EmptyState,
} from "../components/Page";
import { StatusBadge } from "../components/StatusBadge";

export function BidderDetails() {
  const { id = "" } = useParams();

  const [bidder, setBidder] = useState<Bidder | null>(null);
  const [compliance, setCompliance] =
    useState<ComplianceResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api.getBidder(id),
      api.getComplianceResult(id),
    ])
      .then(([bidderData, complianceData]) => {
        setBidder(bidderData);
        setCompliance(complianceData);
      })
      .catch((e) =>
        setError(
          e instanceof Error
            ? e.message
            : "Unable to load bidder."
        )
      )
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <Page
      title="Bidder Compliance Details"
      description="Backend verification and compliance evidence for this bidder."
    >
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} />
      ) : !bidder ? (
        <EmptyState
          title="Bidder unavailable"
          description="The backend did not return this bidder."
        />
      ) : (
        <>
          <div className="detail-grid">
            {[
              ["Bidder Name", bidder.name],
              ["Business Name", bidder.businessName],
              ["Email", bidder.email],
              ["Mobile", bidder.mobile || "—"],
              [
                "Verification Status",
                bidder.verificationStatus || "Not returned",
              ],
              [
                "Compliance Status",
                bidder.complianceStatus || "Not returned",
              ],
            ].map(([key, value]) => (
              <div
                className="detail-field"
                key={String(key)}
              >
                <span>{key}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>

          {compliance ? (
            <ComplianceView result={compliance} />
          ) : (
            <EmptyState
              title="No compliance result"
              description="No compliance result was returned by the backend."
            />
          )}
        </>
      )}
    </Page>
  );
}

export function ComplianceView({
  result,
}: {
  result: ComplianceResult;
}) {
  /*
   * The backend returns:
   * - compliance_percentage
   * - overall_status
   * - summary
   * - requirements
   *
   * The frontend previously expected:
   * - percentage
   * - overallStatus
   * - stage1
   * - stage2
   *
   * This adapter supports the actual backend response.
   */

  const raw = result as any;

  const summary = raw.summary ?? {};
  const requirements = Array.isArray(raw.requirements)
    ? raw.requirements
    : [];

  const percentage =
    raw.compliance_percentage ??
    raw.percentage ??
    null;

  const overallStatus =
    raw.overall_status ??
    raw.overallStatus ??
    "NOT_AVAILABLE";

  const pass =
    summary.pass ??
    raw.stage2?.pass ??
    0;

  const fail =
    summary.fail ??
    raw.stage2?.fail ??
    0;

  const review =
    summary.review ??
    raw.stage2?.review ??
    0;

  const missing =
    summary.missing ??
    raw.stage2?.missing ??
    0;

  const verified =
    raw.stage1?.verified ??
    pass;

  const invalid =
    raw.stage1?.invalid ??
    fail;

  const failedRequirements = requirements.filter(
    (item: any) => item.status === "FAIL"
  );

  const reviewItems = requirements.filter(
    (item: any) => item.status === "REVIEW"
  );

  return (
    <div className="compliance-stack">
      <div className="compliance-hero">
        <div>
          <span>Overall Compliance</span>

          <strong>
            {percentage !== null
              ? `${percentage}%`
              : "Not returned"}
          </strong>
        </div>

        <StatusBadge value={overallStatus} />
      </div>

      <div className="summary-grid">
        {[
          ["Verified", verified],
          ["Review", review],
          ["Invalid", invalid],
          ["Missing", missing],
          ["PASS", pass],
          ["FAIL", fail],
          ["Review", review],
          ["Missing", missing],
        ].map(([key, value], index) => (
          <div
            className="mini-stat"
            key={`${String(key)}-${index}`}
          >
            <span>{key}</span>
            <strong>{value ?? "—"}</strong>
          </div>
        ))}
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2>Verification Requirements</h2>
        </div>

        {requirements.length > 0 ? (
          <ResultTable items={requirements} />
        ) : (
          <EmptyState
            title="No requirements returned"
            description="The backend did not return requirement-level verification data."
          />
        )}
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2>Failed Requirements</h2>
        </div>

        {failedRequirements.length > 0 ? (
          <ResultTable items={failedRequirements} />
        ) : (
          <EmptyState
            title="No failed requirements"
            description="All returned requirements passed verification."
          />
        )}
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2>Review Items</h2>
        </div>

        {reviewItems.length > 0 ? (
          <ResultTable items={reviewItems} />
        ) : (
          <EmptyState
            title="No review items"
            description="No requirements require manual review."
          />
        )}
      </div>
    </div>
  );
}

function ResultTable({ items }: { items: any[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Requirement</th>
            <th>Category</th>
            <th>Status</th>
            <th>Required Value</th>
            <th>Evidence</th>
            <th>Reason</th>
          </tr>
        </thead>

        <tbody>
          {items.map((item, index) => (
            <tr
              key={
                item.requirement_id ||
                item.id ||
                index
              }
            >
              <td>
                <strong>
                  {item.requirement_name ||
                    item.requirement ||
                    item.name ||
                    "—"}
                </strong>
              </td>

              <td>
                {item.category || "—"}
              </td>

              <td>
                <StatusBadge
                  value={item.status || "—"}
                />
              </td>

              <td>
                {item.required_value !== null &&
                item.required_value !== undefined
                  ? String(item.required_value)
                  : "—"}
              </td>

              <td>
                {item.extracted_value !== null &&
                item.extracted_value !== undefined
                  ? typeof item.extracted_value ===
                    "object"
                    ? JSON.stringify(
                        item.extracted_value
                      )
                    : String(item.extracted_value)
                  : "—"}
              </td>

              <td>
                {item.reason || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}