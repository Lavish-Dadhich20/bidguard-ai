import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Search } from "lucide-react";
import { api } from "../services/api";
import type { Role, Tender } from "../types";
import { Page, Loading, ErrorState, EmptyState } from "../components/Page";
import { StatusBadge } from "../components/StatusBadge";

export function Tenders({ role }: { role: Role }) {
  const [items, setItems] = useState<Tender[]>([]); const [q, setQ] = useState(""); const [loading,setLoading]=useState(true); const [error,setError]=useState("");
  async function load(){setLoading(true);setError("");try{setItems(await api.getTenders())}catch(e){setError(e instanceof Error?e.message:"Unable to load tenders.")}finally{setLoading(false)}}
  useEffect(()=>{load()},[]);
  const filtered=items.filter(t=>[t.id,t.reference,t.title,t.organization,t.category].join(" ").toLowerCase().includes(q.toLowerCase()));
  return <Page title={role==="BIDDER"?"Tender List":"Tender Management"} description={role==="BIDDER"?"View tenders returned by the procurement backend.":"Manage tenders returned by the procurement backend."} action={(role==="ADMIN"||role==="TENDER")&&<Link className="btn primary" to="/tenders/new"><Plus size={17}/> Upload New Tender</Link>}>
    {loading?<Loading/>:error?<ErrorState message={error} retry={load}/>:<div className="panel">
      <div className="toolbar"><div className="search"><Search size={17}/><input placeholder="Search tenders…" value={q} onChange={e=>setQ(e.target.value)}/></div></div>
      {filtered.length?<div className="table-wrap"><table><thead><tr><th>Tender ID</th><th>Reference</th><th>Title</th><th>Organization</th><th>Category</th><th>Tender Value</th><th>Deadline</th><th>Bidder Type</th><th>Status</th><th>Action</th></tr></thead><tbody>{filtered.map(t=><tr key={t.id}><td>{t.id}</td><td>{t.reference}</td><td>{t.title}</td><td>{t.organization}</td><td>{t.category}</td><td>{t.tenderValue}</td><td>{t.deadline}</td><td>{t.bidderType}</td><td><StatusBadge value={t.status}/></td><td><Link className="link-btn" to={`/tenders/${t.id}`}>View Tender</Link></td></tr>)}</tbody></table></div>:<EmptyState title="No tenders found" description="No tender records were returned by the backend for this account."/>}
    </div>}
  </Page>;
}