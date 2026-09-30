import { useEffect, useMemo, useState } from "react";
import { api } from "../services/api";
import type { ComplianceResult, Role, User } from "../types";
import { Page, Loading, ErrorState, EmptyState } from "../components/Page";
import { StatusBadge } from "../components/StatusBadge";

function bidderIdFor(user: User) { return user.id === "frontend-preview" ? "BID-DEMO-001" : user.id; }

function DetailTable({ result }: { result: any }) {
  const requirements = Array.isArray(result?.requirements) ? result.requirements : [];
  if (!requirements.length) return <EmptyState title="No verification items returned" description="The backend did not supply requirement-level verification data." />;
  return <div className="table-wrap"><table><thead><tr><th>Requirement</th><th>Category</th><th>Status</th><th>Required Value</th><th>Evidence</th><th>Government Value</th><th>Reason</th></tr></thead><tbody>
    {requirements.map((item: any, index: number) => <tr key={item.requirement_id || item.id || index}>
      <td><strong>{item.requirement_name || item.requirement || "—"}</strong></td>
      <td>{item.category || "—"}</td>
      <td><StatusBadge value={item.status || "—"} /></td>
      <td>{item.required_value == null ? "—" : typeof item.required_value === "object" ? JSON.stringify(item.required_value) : String(item.required_value)}</td>
      <td>{item.extracted_value == null ? "—" : typeof item.extracted_value === "object" ? JSON.stringify(item.extracted_value) : String(item.extracted_value)}</td>
      <td>{item.government_value == null ? "—" : typeof item.government_value === "object" ? JSON.stringify(item.government_value) : String(item.government_value)}</td>
      <td>{item.reason || "—"}</td>
    </tr>)}
  </tbody></table></div>;
}

export function Verification({ role, user }: { role: Role; user: User }) {
  const [reports, setReports] = useState<any[]>([]);
  const [selected, setSelected] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true); setError("");
    try {
      const data = role === "BIDDER"
        ? [await api.getVerificationResult(bidderIdFor(user))]
        : await api.getReports();
      setReports((data || []).filter(Boolean));
      setSelected((data || []).filter(Boolean)[0] || null);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to load verification results."); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [role, user.id]);

  const selectedResult = useMemo(() => selected?.result_data || selected, [selected]);
  const title = role === "ADMIN" ? "Verification Results" : "My Verification Results";
  const description = role === "ADMIN" ? "System-wide government/reference and tender compliance verification results." : "Your government/reference and tender compliance verification results.";

  return <Page title={title} description={description}>
    {loading ? <Loading /> : error ? <ErrorState message={error} retry={load} /> : !reports.length ? <EmptyState title="No verification results" description="No verification records are currently available." /> : (
      <div className="verification-stack">
        {role === "ADMIN" && <div className="panel"><div className="panel-header"><h2>Verification Records</h2></div><div className="table-wrap"><table><thead><tr><th>Bidder</th><th>Tender</th><th>Compliance</th><th>Status</th><th>Verified</th><th>Action</th></tr></thead><tbody>
          {reports.map((r, i) => <tr key={r.id || i}><td>{r.result_data?.company_name || r.bidder_id || "—"}</td><td>{r.tender_id || r.result_data?.tender_id || "—"}</td><td>{r.compliance_percentage != null ? `${r.compliance_percentage}%` : "—"}</td><td><StatusBadge value={r.overall_status || r.result_data?.overall_status || "—"} /></td><td>{r.verified_at ? new Date(r.verified_at).toLocaleString() : "—"}</td><td><button className="link-btn" onClick={() => setSelected(r)}>View Details</button></td></tr>)}
        </tbody></table></div></div>}

        <div className="panel"><div className="panel-header"><div><h2>Document / Requirement Verification</h2><span className="muted">Backend verification details.</span></div><strong>{selectedResult?.compliance_percentage != null ? `${selectedResult.compliance_percentage}%` : "—"}</strong></div><DetailTable result={selectedResult} /></div>
      </div>
    )}
  </Page>;
}
