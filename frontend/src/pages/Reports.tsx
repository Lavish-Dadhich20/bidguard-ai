import { useEffect, useState } from "react";
import { FileText, Download } from "lucide-react";
import { api } from "../services/api";
import type { Role, User } from "../types";
import { Page, Loading, ErrorState, EmptyState } from "../components/Page";
import { StatusBadge } from "../components/StatusBadge";

function bidderIdFor(user: User) { return user.id === "frontend-preview" ? "BID-DEMO-001" : user.id; }

export function Reports({ role, user }: { role: Role; user: User }) {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true); setError("");
    try {
      const data = await api.getReports(role === "BIDDER" ? { bidderId: bidderIdFor(user) } : undefined);
      setItems(data || []);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to load reports."); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [role, user.id]);

  function downloadReport(report: any) {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `BidGuard_Report_${report.bidder_id || "report"}_${report.tender_id || "tender"}.json`;
    document.body.appendChild(anchor); anchor.click(); anchor.remove(); URL.revokeObjectURL(url);
  }

  const title = role === "ADMIN" ? "System Reports" : role === "TENDER" ? "Tender Reports" : "My Reports";
  const description = role === "ADMIN" ? "System-wide compliance and verification reports." : role === "TENDER" ? "Tender-level bidder verification and compliance reports." : "Your own verification and compliance reports.";

  return <Page title={title} description={description}>
    {loading ? <Loading /> : error ? <ErrorState message={error} retry={load} /> : items.length ? (
      <div className="report-list">
        {items.map((report, index) => {
          const summary = report.summary || report.result_data?.summary || {};
          return <div className="report-row" key={report.id || index}>
            <div className="doc-icon"><FileText size={19} /></div>
            <div className="report-main">
              <strong>{report.result_data?.company_name || report.bidder_id || "Unknown Bidder"}</strong>
              <span>Tender: {report.tender_id || report.result_data?.tender_id || "—"}</span>
              {role !== "BIDDER" && <span>Bidder ID: {report.bidder_id || "—"}</span>}
              <div className="report-summary"><span>Compliance: <strong>{report.compliance_percentage != null ? `${report.compliance_percentage}%` : "—"}</strong></span><span>Pass: {summary.pass ?? 0}</span><span>Fail: {summary.fail ?? 0}</span><span>Review: {summary.review ?? 0}</span><span>Missing: {summary.missing ?? 0}</span></div>
            </div>
            <div className="report-actions"><StatusBadge value={report.overall_status || "NOT_AVAILABLE"} /><button className="btn secondary" onClick={() => downloadReport(report)} type="button"><Download size={16} /> Download JSON</button></div>
          </div>;
        })}
      </div>
    ) : <EmptyState title="No reports returned" description="Reports will appear here when backend verification records are available." />}
  </Page>;
}
