import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { AuditEvent } from "../types";
import { Page, Loading, ErrorState, EmptyState } from "../components/Page";

export function Audit(){
 const [items,setItems]=useState<AuditEvent[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState("");
 useEffect(()=>{api.getAuditTrail().then(setItems).catch(e=>setError(e instanceof Error?e.message:"Unable to load audit trail.")).finally(()=>setLoading(false))},[]);
 return <Page title="Audit Trail" description="Administrative audit events returned by the backend.">{loading?<Loading/>:error?<ErrorState message={error}/>:items.length?<div className="panel"><div className="table-wrap"><table><thead><tr><th>User</th><th>Action</th><th>Timestamp</th><th>Related Entity</th><th>Details</th></tr></thead><tbody>{items.map(x=><tr key={x.id}><td>{x.user}</td><td>{x.action}</td><td>{x.timestamp}</td><td>{x.relatedEntity||"—"}</td><td>{x.details||"—"}</td></tr>)}</tbody></table></div></div>:<EmptyState title="No audit events returned" description="Audit activity will appear here when provided by the backend."/>}</Page>
}