import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Search, X } from "lucide-react";
import { api } from "../services/api";
import type { Bidder } from "../types";
import { Page, Loading, ErrorState, EmptyState } from "../components/Page";
import { StatusBadge } from "../components/StatusBadge";

const emptyForm = { name: "", businessName: "", email: "", mobile: "", password: "" };

export function Bidders() {
  const [items, setItems] = useState<Bidder[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState("");

  async function load() {
    setLoading(true);
    try { setItems(await api.getBidders()); setError(""); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to load bidders."); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  const filtered = items.filter((b) => [b.id, b.name, b.businessName, b.email, b.mobile].join(" ").toLowerCase().includes(q.toLowerCase()));

  async function createBidder() {
    setSaving(true); setError(""); setSuccess("");
    try {
      if (!/^\d{10}$/.test(form.mobile)) throw new Error("Enter a valid 10-digit mobile number.");
      if (form.password.length < 6) throw new Error("Password must contain at least 6 characters.");
      const bidder = await api.createBidder(form);
      setItems((current) => [...current, bidder]);
      setSuccess(`Bidder created successfully. Login number: ${form.mobile}`);
      setForm(emptyForm);
      setShowAdd(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to create bidder.");
    } finally { setSaving(false); }
  }

  return (
    <Page title="Bidder Management" description="Create bidder accounts, manage bidder records and review verification state." action={<button className="btn primary" onClick={() => { setShowAdd(true); setSuccess(""); setError(""); }}><Plus size={17} /> Add Bidder</button>}>
      {success && <div className="success-banner">{success}</div>}
      {error && !loading && <div className="form-error">{error}</div>}

      {showAdd && (
        <div className="inline-modal-backdrop">
          <div className="inline-modal">
            <div className="panel-header"><div><h2>Add New Bidder</h2><p className="muted">The mobile number becomes the bidder's login number.</p></div><button className="icon-btn" onClick={() => setShowAdd(false)}><X size={18} /></button></div>
            <div className="form-grid">
              <label>Bidder Name<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Contact person name" /></label>
              <label>Business / Company Name<input value={form.businessName} onChange={(e) => setForm({ ...form, businessName: e.target.value })} placeholder="Company name" /></label>
              <label>Email<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="company@example.com" /></label>
              <label>Mobile / Login Number<input inputMode="numeric" maxLength={10} value={form.mobile} onChange={(e) => setForm({ ...form, mobile: e.target.value.replace(/\D/g, "") })} placeholder="10-digit mobile number" /></label>
              <label>Password<input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Minimum 6 characters" /></label>
            </div>
            <div className="form-actions"><button className="btn secondary" onClick={() => setShowAdd(false)}>Cancel</button><button className="btn primary" disabled={saving || !form.name || !form.businessName || !form.mobile || !form.password} onClick={createBidder}>{saving ? "Creating…" : "Create Bidder"}</button></div>
          </div>
        </div>
      )}

      {loading ? <Loading /> : (
        <div className="panel">
          <div className="toolbar"><div className="search"><Search size={17}/><input placeholder="Search bidders…" value={q} onChange={(e) => setQ(e.target.value)} /></div></div>
          {filtered.length ? <div className="table-wrap"><table><thead><tr><th>Bidder Name</th><th>Business Name</th><th>Email</th><th>Mobile / Login</th><th>Applied Tenders</th><th>Verification</th><th>Compliance</th><th>Actions</th></tr></thead><tbody>
            {filtered.map((b) => <tr key={b.id}><td>{b.name}</td><td>{b.businessName}</td><td>{b.email}</td><td>{b.mobile || "—"}</td><td>{b.appliedTenders ?? "—"}</td><td><StatusBadge value={b.verificationStatus || "NOT_AVAILABLE"} /></td><td>{b.complianceStatus ? <StatusBadge value={b.complianceStatus} /> : <span className="muted">Not returned</span>}</td><td><Link className="link-btn" to={`/bidders/${b.id}`}>View Profile</Link></td></tr>)}
          </tbody></table></div> : <EmptyState title="No bidders returned" description="Bidder records will appear here when provided by the backend." />}
        </div>
      )}
    </Page>
  );
}
