import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import type { User } from "../types";
import { api } from "../services/api";
import { Page } from "../components/Page";

export function Profile({user,onLogout}:{user:User;onLogout:()=>void}){
 const [form,setForm]=useState({name:user.name||"",mobileNumber:user.mobileNumber||"",email:user.email||"",businessName:user.businessName||"",businessType:user.businessType||""});const [message,setMessage]=useState("");
 const [password,setPassword]=useState({currentPassword:"",newPassword:""});const navigate=useNavigate();
 async function save(e:FormEvent){e.preventDefault();setMessage("Profile updates must be connected to your backend profile endpoint. The UI does not persist fake data.");}
 async function del(){if(!confirm("Delete your account? This action cannot be undone."))return;const p=prompt("Confirm with your password:");if(!p)return;try{await api.deleteAccount(p);onLogout();navigate("/login")}catch(e){setMessage(e instanceof Error?e.message:"Account deletion failed.")}}
 return <Page title="Profile" description="Manage your account information and security."><div className="form-card"><form onSubmit={save}><div className="form-grid">{Object.entries(form).map(([k,v])=><label key={k}>{({name:"Name",mobileNumber:"Mobile Number",email:"Email",businessName:"Business Name",businessType:"Business Type"} as any)[k]}<input value={v} onChange={e=>setForm({...form,[k]:e.target.value})}/></label>)}</div><button className="btn primary">Save</button></form><hr/><h2>Change Password</h2><div className="form-grid"><label>Current Password<input type="password" value={password.currentPassword} onChange={e=>setPassword({...password,currentPassword:e.target.value})}/></label><label>New Password<input type="password" value={password.newPassword} onChange={e=>setPassword({...password,newPassword:e.target.value})}/></label></div><button className="btn secondary" onClick={async()=>{try{await api.changePassword(password);setMessage("Password changed successfully.")}catch(e){setMessage(e instanceof Error?e.message:"Password change failed.")}}}>Change Password</button>{message&&<div className="notice compact">{message}</div>}<hr/><button className="btn danger-btn" onClick={del}>Delete Account</button></div></Page>
}