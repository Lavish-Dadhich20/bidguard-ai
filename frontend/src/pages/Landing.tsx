import {
  ArrowRight,
  Check,
  ExternalLink,
  FileCheck2,
  LockKeyhole,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import type { User } from "../types";

const roles = [
  {
    title: "Bidder",
    role: "BIDDER" as const,
    icon: UserRound,
    description:
      "Manage your profile, upload compliance documents, track verification status and view compliance scorecards.",
    features: [
      "Document Upload & Management",
      "Compliance Dashboard",
      "Verification Evidence",
      "Downloadable Reports",
    ],
    className: "landing-role bidder",
  },
  {
    title: "Tender Officer",
    role: "TENDER" as const,
    icon: FileCheck2,
    description:
      "Manage tenders, inspect bidder registries, analyse compliance results and generate official procurement reports.",
    features: [
      "Tender Management",
      "Bidder Registry Inspection",
      "Compliance Analysis",
      "Tender Analytics",
    ],
    className: "landing-role officer",
  },
  {
    title: "System Admin",
    role: "ADMIN" as const,
    icon: LockKeyhole,
    description:
      "Full system governance, complete audit trail oversight, advanced analytics and inter-department controls.",
    features: [
      "Full System Governance",
      "Audit Trail (Admin Only)",
      "All Tenders & Bidders",
      "Advanced Analytics",
    ],
    className: "landing-role admin",
  },
];

export function Landing({
  onPortalSelect,
}: {
  onPortalSelect: (user: User) => void;
}) {
  function openPortal(
    role: "ADMIN" | "TENDER" | "BIDDER",
    name: string
  ) {
    onPortalSelect({
      id: "frontend-preview",
      name,
      email: "",
      role,
    });
  }

  return (
    <div className="landing-page">
      <header className="landing-header">
        <div className="landing-container landing-header-inner">
          <div className="landing-brand">
            <div className="landing-brand-mark">
              <ShieldCheck size={27} />
            </div>

            <div>
              <strong>BidGuard AI</strong>
              <span>GEM COMPLIANCE PLATFORM</span>
            </div>
          </div>

          <div className="landing-header-actions">
            <span className="landing-sih">SIH 2026</span>

            <button
              className="landing-signin"
              onClick={() => {
                window.location.href = "/login";
              }}
            >
              <ArrowRight size={17} />
              Sign In
            </button>
          </div>
        </div>
      </header>

      <main>
        <section className="landing-hero">
          <div className="landing-hero-map" aria-hidden="true" />

          <div className="landing-container landing-hero-content">
            <div className="landing-hero-copy">
              <div className="landing-kicker">
                SMART INDIA HACKATHON · GEM PROCUREMENT
              </div>

              <h1>
                AI-Powered Bid
                <br />
                Compliance Verification
              </h1>

              <p>
                Automated multi-registry verification of vendor bid
                submissions against GeM procurement tender specifications.
                Transparent. Efficient. Incorruptible.
              </p>

              <div className="landing-hero-actions">
                <button
                  className="landing-primary"
                  onClick={() => {
                    window.location.href = "/login";
                  }}
                >
                  Access Portal
                  <ArrowRight size={17} />
                </button>

                <a
                  className="landing-secondary"
                  href="https://gem.gov.in/"
                  target="_blank"
                  rel="noreferrer"
                >
                  Visit GeM Portal
                  <ExternalLink size={15} />
                </a>
              </div>
            </div>
          </div>
        </section>

        <section className="landing-stats">
          <div className="landing-container landing-stats-grid">
            <div>
              <strong>₹2.3L Cr+</strong>
              <span>ANNUAL GEM PROCUREMENT VALUE</span>
            </div>

            <div>
              <strong>63,000+</strong>
              <span>GOVERNMENT BUYER ORGANISATIONS</span>
            </div>

            <div>
              <strong>15 Categories</strong>
              <span>MANDATORY COMPLIANCE DOCUMENTS</span>
            </div>

            <div>
              <strong>10+ Registries</strong>
              <span>CROSS-VERIFIED GOVERNMENT DATABASES</span>
            </div>
          </div>
        </section>

        <section className="landing-about landing-container">
          <div className="landing-about-copy">
            <span className="landing-section-kicker">
              ABOUT THE PLATFORM
            </span>

            <h2>What is BidGuard AI?</h2>

            <p>
              BidGuard AI is an integrated bid compliance verification
              platform developed under the Smart India Hackathon initiative.
              It automates and accelerates verification of vendor bid
              submissions against GeM procurement tender specifications and
              statutory registries.
            </p>

            <p>
              The platform brings document validation, government-record
              cross-checking, tender requirements and compliance reporting
              into one workflow.
            </p>
          </div>

          <div className="landing-feature-grid">
            <div className="landing-feature-card">
              <div className="landing-feature-icon">
                <ShieldCheck size={20} />
              </div>

              <h3>Multi-Registry Verification</h3>

              <p>
                Cross-check statutory records including GST, PAN, Udyam,
                EPFO, ESIC and DPIIT.
              </p>
            </div>

            <div className="landing-feature-card">
              <div className="landing-feature-icon green">
                <FileCheck2 size={20} />
              </div>

              <h3>15 Document Categories</h3>

              <p>
                Structured document upload and validation for mandatory
                compliance categories.
              </p>
            </div>
          </div>
        </section>

        <section className="landing-roles landing-container">
          <span className="landing-section-kicker">
            ACCESS ROLES
          </span>

          <h2>Three Stakeholder Portals</h2>

          <div className="landing-role-grid">
            {roles.map(
              ({
                title,
                role,
                icon: Icon,
                description,
                features,
                className,
              }, index) => (
                <div key={title} className={className}>
                  {index === 1 && (
                    <span className="landing-most-used">
                      MOST USED
                    </span>
                  )}

                  <div className="landing-role-icon">
                    <Icon size={25} />
                  </div>

                  <h3>{title}</h3>

                  <p>{description}</p>

                  <ul>
                    {features.map((feature) => (
                      <li key={feature}>
                        <Check size={15} />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <button
                    className="landing-role-button"
                    onClick={() =>
                      openPortal(
                        role,
                        `${title} Preview`
                      )
                    }
                  >
                    {role === "TENDER"
                      ? "Login as Officer"
                      : role === "ADMIN"
                        ? "Login as Admin"
                        : "Login as Bidder"}
                  </button>
                </div>
              )
            )}
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <div className="landing-container">
          <div className="landing-footer-brand">
            <div className="landing-brand-mark small">
              <ShieldCheck size={20} />
            </div>

            <div>
              <strong>BidGuard AI</strong>
              <span>
                GeM Procurement Compliance Platform
              </span>
            </div>
          </div>

          <p>
            Ministry of Commerce &amp; Industry &nbsp;·&nbsp;
            Government e-Marketplace (GeM) &nbsp;·&nbsp;
            Smart India Hackathon 2026
          </p>

          <small>
            © 2026 BidGuard AI. All data shown is for demonstration
            purposes only.
          </small>
        </div>
      </footer>
    </div>
  );
}