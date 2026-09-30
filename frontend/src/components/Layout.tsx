import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Activity,
  BarChart3,
  FileCheck2,
  FileText,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  ShieldCheck,
  UploadCloud,
  Users,
  X,
} from "lucide-react";
import type { Role, User } from "../types";
import { api, FRONTEND_ONLY } from "../services/api";

const navByRole: Record<
  Role,
  {
    label: string;
    path: string;
    icon: typeof LayoutDashboard;
  }[]
> = {
  ADMIN: [
    {
      label: "Dashboard",
      path: "/",
      icon: LayoutDashboard,
    },
    {
      label: "Tender Management",
      path: "/tenders",
      icon: FileText,
    },
    {
      label: "Bidder Management",
      path: "/bidders",
      icon: Users,
    },
    {
      label: "Verification Results",
      path: "/verification",
      icon: ShieldCheck,
    },
    {
      label: "Tender Analytics",
      path: "/analytics",
      icon: BarChart3,
    },
    {
      label: "Reports",
      path: "/reports",
      icon: FileCheck2,
    },
    {
      label: "Audit Trail",
      path: "/audit",
      icon: History,
    },
    {
      label: "Profile",
      path: "/profile",
      icon: Settings,
    },
  ],

  TENDER: [
    {
      label: "Dashboard",
      path: "/",
      icon: LayoutDashboard,
    },
    {
      label: "Tender Management",
      path: "/tenders",
      icon: FileText,
    },
    {
      label: "Upload New Tender",
      path: "/tenders/new",
      icon: UploadCloud,
    },
    {
      label: "Tender Analytics",
      path: "/analytics",
      icon: BarChart3,
    },
    {
      label: "Reports",
      path: "/reports",
      icon: FileCheck2,
    },
    {
      label: "Profile",
      path: "/profile",
      icon: Settings,
    },
  ],

  BIDDER: [
    {
      label: "Dashboard",
      path: "/",
      icon: LayoutDashboard,
    },
    {
      label: "Tender List",
      path: "/tenders",
      icon: FileText,
    },
    {
      label: "My Documents",
      path: "/documents",
      icon: UploadCloud,
    },
    {
      label: "My Compliance",
      path: "/compliance",
      icon: ShieldCheck,
    },
    {
      label: "Verification Results",
      path: "/verification",
      icon: ShieldCheck,
    },
    {
      label: "Reports",
      path: "/reports",
      icon: FileCheck2,
    },
    {
      label: "Profile",
      path: "/profile",
      icon: Settings,
    },
  ],
};

export function Layout({
  user,
  onLogout,
}: {
  user: User;
  onLogout: () => void;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const navigate = useNavigate();
  const nav = navByRole[user.role];

  async function logout() {
    try {
      await api.logout();
    } catch {}

    onLogout();

    // Return to landing page after logout
    navigate("/", { replace: true });
  }

  return (
    <div className="app-shell">
      <aside
        className={`sidebar ${mobileOpen ? "open" : ""}`}
      >
        <div className="brand">
          <div className="brand-mark">
            <ShieldCheck size={23} />
          </div>

          <div>
            <strong>BidGuard AI</strong>
            <span>Bid Compliance Platform</span>
          </div>

          <button
            className="icon-btn mobile-close"
            onClick={() => setMobileOpen(false)}
            aria-label="Close navigation"
          >
            <X />
          </button>
        </div>

        <div className="role-pill">
          {user.role} PORTAL
        </div>

        <nav>
          {nav.map(
            ({ label, path, icon: Icon }) => (
              <NavLink
                key={path}
                to={path}
                end={path === "/"}
                onClick={() =>
                  setMobileOpen(false)
                }
              >
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            )
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="security-note">
            <Activity size={16} />

            <span>
              Backend verification
              <br />
              is authoritative
            </span>
          </div>

          <button
            className="logout-link"
            onClick={logout}
          >
            <LogOut size={17} />
            Logout
          </button>
        </div>
      </aside>

      <main className="main">
        {FRONTEND_ONLY && (
          <div className="preview-banner">
            Frontend preview mode · Backend not connected
          </div>
        )}

        <header className="topbar">
          <button
            className="icon-btn hamburger"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Menu />
          </button>

          <div className="topbar-title">
            <span>BidGuard AI</span>

            <small>
              AI-Powered Bid Compliance Verification Platform
            </small>
          </div>

          <div className="user-menu">
            <div className="avatar">
              {user.name
                ?.charAt(0)
                ?.toUpperCase() || "U"}
            </div>

            <div>
              <strong>
                {user.name || "User"}
              </strong>

              <span>{user.role}</span>
            </div>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}