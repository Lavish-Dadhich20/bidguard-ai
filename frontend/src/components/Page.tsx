import type { ReactNode } from "react";

export function Page({ title, description, action, children }: {
  title: string; description?: string; action?: ReactNode; children: ReactNode;
}) {
  return <section className="page">
    <div className="breadcrumb">BidGuard AI <span>/</span> {title}</div>
    <div className="page-heading">
      <div><h1>{title}</h1>{description && <p>{description}</p>}</div>
      {action}
    </div>
    {children}
  </section>;
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return <div className="empty-state"><div className="empty-icon"><FileTextIcon /></div><h3>{title}</h3><p>{description}</p></div>;
}
function FileTextIcon() { return <FileText />; }
import { FileText } from "lucide-react";

export function Loading() {
  return <div className="loading-state"><div className="spinner" /> Loading data from the backend…</div>;
}

export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="error-state"><strong>Unable to load data</strong><p>{message}</p>{retry && <button className="btn secondary" onClick={retry}>Retry</button>}</div>;
}