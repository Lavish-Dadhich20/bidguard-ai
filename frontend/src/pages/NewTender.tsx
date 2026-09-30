import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Trash2 } from "lucide-react";
import { api } from "../services/api";
import { Page } from "../components/Page";
import type { TenderRequirement } from "../types";

const STANDARD_REQUIREMENTS: Omit<TenderRequirement, "id">[] = [
  { requirement: "GST Registration Active", operator: "==", requiredValue: "ACTIVE", mandatory: true, fieldToCheck: "gst.status", verificationSource: "GST", category: "STATUTORY" },
  { requirement: "PAN Valid", operator: "==", requiredValue: "VALID", mandatory: true, fieldToCheck: "pan.status", verificationSource: "PAN", category: "STATUTORY" },
  { requirement: "Udyam Registration Active", operator: "==", requiredValue: "ACTIVE", mandatory: true, fieldToCheck: "udyam.status", verificationSource: "UDYAM", category: "MSME" },
  { requirement: "Minimum Annual Turnover (Rs. 5 Crore)", operator: ">=", requiredValue: 50000000, mandatory: true, fieldToCheck: "turnover.annual_turnover", verificationSource: "TURNOVER", category: "FINANCIAL" },
  { requirement: "ITR Filing Compliant", operator: "==", requiredValue: "FILED", mandatory: true, fieldToCheck: "itr.filing_status", verificationSource: "ITR", category: "STATUTORY" },
  { requirement: "EPFO Compliance", operator: "==", requiredValue: "COMPLIANT", mandatory: true, fieldToCheck: "epfo.status", verificationSource: "EPFO", category: "LABOUR_COMPLIANCE" },
  { requirement: "ESIC Compliance", operator: "==", requiredValue: "COMPLIANT", mandatory: true, fieldToCheck: "esic.status", verificationSource: "ESIC", category: "LABOUR_COMPLIANCE" },
  { requirement: "Minimum Local Content (50%)", operator: ">=", requiredValue: 50, mandatory: true, fieldToCheck: "local_content.percentage", verificationSource: "MAKE_IN_INDIA", category: "MANUFACTURING" },
  { requirement: "OEM Authorization Mandatory", operator: "boolean", requiredValue: true, mandatory: true, fieldToCheck: "oem_authorization.valid", verificationSource: "OEM", category: "MANUFACTURING" },
  { requirement: "Bidder Not Blacklisted / Debarred", operator: "not_in_blacklist", requiredValue: null, mandatory: true, fieldToCheck: null, verificationSource: "BLACKLIST", category: "ELIGIBILITY" },
  { requirement: "Certificate of Incorporation / Business Registration", operator: "==", requiredValue: "REGISTERED", mandatory: true, fieldToCheck: "incorporation.status", verificationSource: "MCA", category: "LEGAL" },
  { requirement: "Minimum Relevant Experience (3 Years)", operator: ">=", requiredValue: 3, mandatory: false, fieldToCheck: "experience.years", verificationSource: null, category: "ELIGIBILITY" },
  { requirement: "Legal Name Consistency Across Documents", operator: "name_consistency", requiredValue: null, mandatory: false, fieldToCheck: null, verificationSource: null, category: "IDENTITY" },
];

function makeRequirements(): TenderRequirement[] {
  return STANDARD_REQUIREMENTS.map((item, index) => ({
    ...item,
    id: item.requirement.replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "").toLowerCase() || `REQ-${index + 1}`,
  }));
}

const initialForm = {
  id: "",
  reference: "",
  title: "",
  organization: "",
  category: "",
  tenderValue: "",
  deadline: "",
  bidderType: "",
};

export function NewTender() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [reqs, setReqs] = useState<TenderRequirement[]>(makeRequirements());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const available = useMemo(() => STANDARD_REQUIREMENTS.filter((candidate) => !reqs.some((r) => r.requirement === candidate.requirement)), [reqs]);

  function updateRequirement(index: number, patch: Partial<TenderRequirement>) {
    setReqs((current) => current.map((row, i) => i === index ? { ...row, ...patch } : row));
  }

  function addRequirement() {
    const next = available[0];
    if (!next) return;
    setReqs((current) => [...current, { ...next, id: crypto.randomUUID() }]);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (!form.id.trim() || !form.reference.trim() || !form.title.trim()) {
        throw new Error("Tender ID, Tender Reference and Tender Title are required.");
      }
      const created = await api.createTender({
        ...form,
        tenderValue: form.tenderValue,
        requirements: reqs,
      });
      navigate(`/tenders/${created.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to create tender.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title="Upload New Tender" description="Create a tender using the standard BidGuard compliance requirements.">
      <form className="form-card" onSubmit={submit}>
        {error && <div className="form-error">{error}</div>}

        <div className="form-grid">
          <label>Tender ID<input required value={form.id} placeholder="TDR-2026-001" onChange={(e) => setForm({ ...form, id: e.target.value })} /></label>
          <label>Tender Reference<input required value={form.reference} placeholder="GEM/2026/B/001" onChange={(e) => setForm({ ...form, reference: e.target.value })} /></label>
          <label>Tender Title<input required value={form.title} placeholder="Supply of Industrial Equipment" onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
          <label>Organization<input required value={form.organization} placeholder="Government Procurement Department" onChange={(e) => setForm({ ...form, organization: e.target.value })} /></label>
          <label>Category<input required value={form.category} placeholder="Industrial Equipment" onChange={(e) => setForm({ ...form, category: e.target.value })} /></label>
          <label>Tender Value<input required value={form.tenderValue} placeholder="50000000" onChange={(e) => setForm({ ...form, tenderValue: e.target.value })} /></label>
          <label>Deadline<input required type="datetime-local" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} /></label>
          <label>Bidder Type<input required value={form.bidderType} placeholder="Manufacturer / Supplier / OEM" onChange={(e) => setForm({ ...form, bidderType: e.target.value })} /></label>
        </div>

        <div className="requirements-editor">
          <div className="panel-header">
            <div>
              <h2>Compliance Requirements</h2>
              <p className="muted">The standard BidGuard requirements are preloaded. Remove any requirement that is not applicable to this tender.</p>
            </div>
            <button type="button" className="btn secondary" onClick={addRequirement} disabled={!available.length}>Add Requirement</button>
          </div>

          <div className="requirement-editor-list">
            {reqs.map((r, i) => (
              <div className="req-row" key={r.id}>
                <select value={r.requirement} onChange={(e) => {
                  const selected = STANDARD_REQUIREMENTS.find((x) => x.requirement === e.target.value);
                  updateRequirement(i, selected ? { ...selected } : { requirement: e.target.value });
                }}>
                  {STANDARD_REQUIREMENTS.map((option) => <option key={option.requirement}>{option.requirement}</option>)}
                </select>
                <select value={r.operator || ""} onChange={(e) => updateRequirement(i, { operator: e.target.value })}>
                  <option value="">Operator</option><option value="==">=</option><option value=">=">≥</option><option value=">">&gt;</option><option value="<=">≤</option><option value="<">&lt;</option><option value="boolean">Boolean</option><option value="not_in_blacklist">Blacklist check</option><option value="name_consistency">Name consistency</option>
                </select>
                <input placeholder="Required value" value={r.requiredValue == null ? "" : String(r.requiredValue)} onChange={(e) => updateRequirement(i, { requiredValue: e.target.value })} />
                <label className="req-check"><input type="checkbox" checked={r.mandatory !== false} onChange={(e) => updateRequirement(i, { mandatory: e.target.checked })} /> Mandatory</label>
                <button type="button" className="icon-btn danger" onClick={() => setReqs((current) => current.filter((_, rowIndex) => rowIndex !== i))} aria-label="Remove requirement"><Trash2 size={17} /></button>
              </div>
            ))}
          </div>
        </div>

        <div className="form-actions"><button className="btn primary" disabled={busy}>{busy ? "Creating…" : "Create Tender"}</button></div>
      </form>
    </Page>
  );
}
