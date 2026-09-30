import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { Role } from "../types";
import { Page, Loading, ErrorState, EmptyState } from "../components/Page";

function summaryOf(row: any) {
  return row.summary || row.result_data?.summary || {};
}

export function Analytics({ role }: { role: Role }) {
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true); setError("");
    try {
      const reports = await api.getReports();
      const seen = new Set<string>();
      const normalized = (reports || []).filter((row: any) => {
        const key = `${row.bidder_id || ""}-${row.tender_id || row.result_data?.tender_id || ""}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      setRows(normalized);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to load tender analytics."); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  return <Page title="Tender Analytics" description="Descriptive tender-level analytics only. No prediction, ranking, or outcome recommendation is performed.">
    {loading ? <Loading /> : error ? <ErrorState message={error} retry={load} /> : rows.length ? (
      <>
        <div className="stat-grid">
          <div className="stat-card"><div className="stat-icon">T</div><div><span>Verification Records</span><strong>{rows.length}</strong></div></div>
          <div className="stat-card"><div className="stat-icon">%</div><div><span>Average Compliance</span><strong>{(() => { const values = rows.map((r) => Number(r.compliance_percentage)).filter(Number.isFinite); return values.length ? `${(values.reduce((a,b)=>a+b,0)/values.length).toFixed(2)}%` : "—"; })()}</strong></div></div>
          <div className="stat-card"><div className="stat-icon">✓</div><div><span>Pass Checks</span><strong>{rows.reduce((s,r)=>s+Number(summaryOf(r).pass||0),0)}</strong></div></div>
          <div className="stat-card"><div className="stat-icon">!</div><div><span>Review Checks</span><strong>{rows.reduce((s,r)=>s+Number(summaryOf(r).review||0),0)}</strong></div></div>
        </div>
        <div className="panel"><div className="panel-header"><h2>Bidder Verification by Tender</h2></div><div className="table-wrap"><table><thead><tr><th>Tender</th><th>Bidder</th><th>Compliance</th><th>PASS</th><th>FAIL</th><th>REVIEW</th><th>MISSING</th><th>Status</th></tr></thead><tbody>
          {rows.map((r,i)=>{const s=summaryOf(r);return <tr key={r.id||i}><td>{r.tender_id||r.result_data?.tender_id||"—"}</td><td>{r.result_data?.company_name||r.bidder_id||"—"}</td><td>{r.compliance_percentage!=null?`${r.compliance_percentage}%`:"—"}</td><td>{s.pass??0}</td><td>{s.fail??0}</td><td>{s.review??0}</td><td>{s.missing??0}</td><td>{r.overall_status||r.result_data?.overall_status||"—"}</td></tr>})}
        </tbody></table></div></div>
      </>
    ) : <EmptyState title="No analytics data returned" description="Analytics will populate after backend verification records are available." />}
  </Page>;
}
