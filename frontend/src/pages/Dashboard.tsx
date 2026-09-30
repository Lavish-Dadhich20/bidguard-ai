import { useEffect, useState } from "react";
import {
  Activity,
  FileCheck2,
  FileText,
  ShieldCheck,
  Users,
  UploadCloud,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { api } from "../services/api";
import type { Role, Tender, Bidder, User } from "../types";
import {
  Page,
  Loading,
  ErrorState,
  EmptyState,
} from "../components/Page";
import { StatusBadge } from "../components/StatusBadge";

type Report = {
  id?: string;
  bidder_id?: string;
  tender_id?: string;
  compliance_percentage?: number;
  overall_status?: string;
  summary?: {
    pass?: number;
    fail?: number;
    review?: number;
    missing?: number;
  };
  result_data?: {
    company_name?: string;
    overall_status?: string;
  };
  verified_at?: string;
};

type Stat = [LucideIcon, string, string | number];

function bidderIdFor(user: User) {
  if (user.bidderId) return user.bidderId;
  return user.id === "frontend-preview" ? "BID-DEMO-001" : user.id;
}

export function Dashboard({
  role,
  user,
}: {
  role: Role;
  user?: User;
}) {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [bidders, setBidders] = useState<Bidder[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [documentsCount, setDocumentsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");

    try {
      const [t, b, r] = await Promise.all([
        api.getTenders(),
        role === "BIDDER"
          ? Promise.resolve([] as Bidder[])
          : api.getBidders(),
        api.getReports(
          role === "BIDDER" && user
            ? { bidderId: bidderIdFor(user) }
            : undefined
        ),
      ]);

      setTenders(t);
      setBidders(b);
      setReports((r || []) as Report[]);

      if (role === "BIDDER" && user) {
        const docs = await api.getDocuments(
          bidderIdFor(user)
        );
        setDocumentsCount(docs.length);
      }
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Unable to load dashboard."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [role, user?.id]);

  const activeTenders = tenders.filter((t) =>
    ["OPEN", "ACTIVE"].includes(
      String(t.status).toUpperCase()
    )
  ).length;

  const pendingReviews = reports.filter((r) =>
    ["REVIEW", "NEEDS_MANUAL_REVIEW"].includes(
      String(r.overall_status).toUpperCase()
    )
  ).length;

  const verified = reports.filter(
    (r) => r.overall_status
  ).length;

  const applications = tenders.reduce(
    (sum, t) => sum + Number(t.bidderCount || 0),
    0
  );

  const bidderReports =
    role === "BIDDER" ? reports : [];

  const bidderName = user?.name || "Bidder";

  let stats: Stat[] = [];

  if (role === "ADMIN") {
    stats = [
      [FileText, "Total Tenders", tenders.length],
      [Activity, "Active Tenders", activeTenders],
      [Users, "Total Bidders", bidders.length],
      [ShieldCheck, "Verified Bids", verified],
      [UploadCloud, "Pending Reviews", pendingReviews],
      [FileCheck2, "Verification Reports", reports.length],
    ];
  } else if (role === "TENDER") {
    stats = [
      [FileText, "Tenders", tenders.length],
      [Activity, "Active Tenders", activeTenders],
      [Users, "Applications Received", applications],
      [ShieldCheck, "Verified Bids", verified],
      [UploadCloud, "Pending Reviews", pendingReviews],
      [FileCheck2, "Tender Reports", reports.length],
    ];
  } else {
    stats = [
      [FileText, "Available Tenders", activeTenders],
      [Activity, "Open Tenders", activeTenders],
      [UploadCloud, "Documents Submitted", documentsCount],
      [ShieldCheck, "My Verification Records", bidderReports.length],
      [FileCheck2, "My Compliance Reports", bidderReports.length],
      [Activity, "My Pending Reviews", pendingReviews],
    ];
  }

  const title =
    role === "ADMIN"
      ? "Admin Dashboard"
      : role === "TENDER"
        ? "Tender Dashboard"
        : "Bidder Dashboard";

  const description =
    role === "ADMIN"
      ? "System-wide procurement, bidder and verification overview."
      : role === "TENDER"
        ? "Tender workspace and tender-level verification activity."
        : "Your tenders, submitted documents and verification activity.";

  return (
    <Page
      title={title}
      description={description}
    >
      {role === "BIDDER" && user && (
        <div className="notice">
          <ShieldCheck size={18} />

          <div>
            <strong>
              Signed in as {bidderName}
            </strong>

            <span>
              {user.businessName
                ? `${user.businessName} · `
                : ""}
              Only your documents, applications and verification
              records are shown here.
            </span>
          </div>
        </div>
      )}

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState
          message={error}
          retry={load}
        />
      ) : (
        <>
          <div className="stat-grid">
            {stats.map(([Icon, label, value]) => (
              <div
                className="stat-card"
                key={label}
              >
                <div className="stat-icon">
                  <Icon size={19} />
                </div>

                <div>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              </div>
            ))}
          </div>

          <div className="two-col">
            <div className="panel">
              <div className="panel-header">
                <h2>
                  {role === "BIDDER"
                    ? "Available Tenders"
                    : "Recent Tender Activity"}
                </h2>
              </div>

              {tenders.length ? (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Reference</th>
                        <th>Title</th>
                        <th>Status</th>
                      </tr>
                    </thead>

                    <tbody>
                      {tenders
                        .slice(0, 6)
                        .map((t) => (
                          <tr key={t.id}>
                            <td>{t.reference}</td>
                            <td>{t.title}</td>
                            <td>
                              <StatusBadge
                                value={t.status}
                              />
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState
                  title="No tenders returned"
                  description="Tender records will appear here when the backend provides them."
                />
              )}
            </div>

            <div className="panel">
              <div className="panel-header">
                <h2>
                  {role === "BIDDER"
                    ? "My Verification Activity"
                    : "Recent Verification Activity"}
                </h2>
              </div>

              {reports.length ? (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>
                          {role === "BIDDER"
                            ? "Tender"
                            : "Bidder / Company"}
                        </th>
                        <th>Compliance</th>
                        <th>Status</th>
                      </tr>
                    </thead>

                    <tbody>
                      {reports
                        .slice(0, 6)
                        .map((r, i) => (
                          <tr key={r.id || i}>
                            <td>
                              {role === "BIDDER"
                                ? r.tender_id || "—"
                                : r.result_data
                                    ?.company_name ||
                                  r.bidder_id ||
                                  "—"}
                            </td>

                            <td>
                              {r.compliance_percentage != null
                                ? `${r.compliance_percentage}%`
                                : "—"}
                            </td>

                            <td>
                              <StatusBadge
                                value={
                                  r.overall_status || "—"
                                }
                              />
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState
                  title={
                    role === "BIDDER"
                      ? "No personal verification records"
                      : "No verification records"
                  }
                  description="Verification activity will appear here after verification is completed."
                />
              )}
            </div>
          </div>
        </>
      )}
    </Page>
  );
}