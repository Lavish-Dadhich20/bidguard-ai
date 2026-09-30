import { useState } from "react";
import type { ReactNode } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useNavigate,
} from "react-router-dom";

import type { Role, User } from "./types";

import { Layout } from "./components/Layout";
import { Landing } from "./pages/Landing";
import { Dashboard } from "./pages/Dashboard";
import { Tenders } from "./pages/Tenders";
import { TenderDetails } from "./pages/TenderDetails";
import { NewTender } from "./pages/NewTender";
import { Bidders } from "./pages/Bidders";
import { BidderDetails } from "./pages/BidderDetails";
import { Documents } from "./pages/Documents";
import { Compliance } from "./pages/Compliance";
import { Verification } from "./pages/Verification";
import { Analytics } from "./pages/Analytics";
import { Reports } from "./pages/Reports";
import { Audit } from "./pages/Audit";
import { Profile } from "./pages/Profile";

/* =========================================================
   PORTAL PREVIEW / SELECTION PAGE
========================================================= */

function PortalLogin({
  onLogin,
}: {
  onLogin: (user: User) => void;
}) {
  const navigate = useNavigate();

  const roles: Role[] = [
    "ADMIN",
    "TENDER",
    "BIDDER",
  ];

  function selectPortal(role: Role) {
    const names: Record<Role, string> = {
      ADMIN: "System Admin",
      TENDER: "Tender Officer",
      BIDDER: "Bidder",
    };

    onLogin({
      id: "frontend-preview",
      name: names[role],
      email: "",
      role,
    });
  }

  return (
    <div className="login-page">
      <div className="login-brand">
        <div className="brand-mark large">
          <span>BG</span>
        </div>

        <h1>BidGuard AI</h1>

        <p>
          AI-Powered Bid Compliance Verification Platform
        </p>
      </div>

      <div className="login-card">
        <div className="section-kicker">
          FRONTEND PREVIEW
        </div>

        <h2>Choose a portal to preview</h2>

        <p className="muted">
          Select a role to directly open its BidGuard portal.
        </p>

        <div className="preview-role-list">
          {roles.map((role) => (
            <button
              key={role}
              type="button"
              className="btn secondary wide"
              onClick={() => selectPortal(role)}
            >
              {role} Portal
            </button>
          ))}
        </div>

        <button
          type="button"
          className="text-btn"
          style={{ marginTop: 16 }}
          onClick={() => navigate("/")}
        >
          ← Back to landing page
        </button>
      </div>
    </div>
  );
}

/* =========================================================
   ROLE GATE
========================================================= */

function RoleGate({
  user,
  roles,
  children,
}: {
  user: User;
  roles: Role[];
  children: ReactNode;
}) {
  return roles.includes(user.role) ? (
    <>{children}</>
  ) : (
    <Navigate to="/" replace />
  );
}

/* =========================================================
   APPLICATION ROUTES
========================================================= */

function AppRoutes({
  user,
  setUser,
}: {
  user: User;
  setUser: (user: User | null) => void;
}) {
  const navigate = useNavigate();

  function logout() {
    setUser(null);
    navigate("/", { replace: true });
  }

  return (
    <Routes>
      <Route
        element={
          <Layout
            user={user}
            onLogout={logout}
          />
        }
      >
        {/* DASHBOARD */}

        <Route
          index
          element={
            <Dashboard
              role={user.role}
              user={user}
            />
          }
        />

        {/* TENDERS */}

        <Route
          path="tenders"
          element={
            <Tenders
              role={user.role}
            />
          }
        />

        {/* NEW TENDER */}

        <Route
          path="tenders/new"
          element={
            <RoleGate
              user={user}
              roles={["ADMIN", "TENDER"]}
            >
              <NewTender />
            </RoleGate>
          }
        />

        {/* TENDER DETAILS */}

        <Route
          path="tenders/:id"
          element={
            <TenderDetails
              role={user.role}
              user={user}
            />
          }
        />

        {/* BIDDER MANAGEMENT */}

        <Route
          path="bidders"
          element={
            <RoleGate
              user={user}
              roles={["ADMIN"]}
            >
              <Bidders />
            </RoleGate>
          }
        />

        {/* BIDDER DETAILS */}

        <Route
          path="bidders/:id"
          element={
            <RoleGate
              user={user}
              roles={["ADMIN"]}
            >
              <BidderDetails />
            </RoleGate>
          }
        />

        {/* BIDDER DOCUMENTS */}

        <Route
          path="documents"
          element={
            <RoleGate
              user={user}
              roles={["BIDDER"]}
            >
              <Documents
                user={user}
              />
            </RoleGate>
          }
        />

        {/* BIDDER COMPLIANCE */}

        <Route
          path="compliance"
          element={
            <RoleGate
              user={user}
              roles={["BIDDER"]}
            >
              <Compliance
                user={user}
              />
            </RoleGate>
          }
        />

        {/* VERIFICATION */}

        <Route
          path="verification"
          element={
            <RoleGate
              user={user}
              roles={["ADMIN", "BIDDER"]}
            >
              <Verification
                role={user.role}
                user={user}
              />
            </RoleGate>
          }
        />

        {/* ANALYTICS */}

        <Route
          path="analytics"
          element={
            <RoleGate
              user={user}
              roles={["ADMIN", "TENDER"]}
            >
              <Analytics
                role={user.role}
              />
            </RoleGate>
          }
        />

        {/* REPORTS */}

        <Route
          path="reports"
          element={
            <Reports
              role={user.role}
              user={user}
            />
          }
        />

        {/* AUDIT */}

        <Route
          path="audit"
          element={
            <RoleGate
              user={user}
              roles={["ADMIN"]}
            >
              <Audit />
            </RoleGate>
          }
        />

        {/* PROFILE */}

        <Route
          path="profile"
          element={
            <Profile
              user={user}
              onLogout={logout}
            />
          }
        />

        {/* UNKNOWN ROUTE */}

        <Route
          path="*"
          element={
            <Navigate
              to="/"
              replace
            />
          }
        />
      </Route>
    </Routes>
  );
}

/* =========================================================
   MAIN APP
========================================================= */

export default function App() {
  const [user, setUser] =
    useState<User | null>(null);

  return (
    <BrowserRouter>
      {!user ? (
        <Routes>

          {/* =============================================
             LANDING PAGE
          ============================================= */}

          <Route
            path="/"
            element={
              <Landing
                onPortalSelect={setUser}
              />
            }
          />

          {/* =============================================
             SIGN IN / PORTAL SELECTION

             IMPORTANT:
             NO USERNAME/PASSWORD PAGE HERE.
             DIRECTLY SHOW ADMIN/TENDER/BIDDER.
          ============================================= */}

          <Route
            path="/login"
            element={
              <PortalLogin
                onLogin={setUser}
              />
            }
          />

          {/* =============================================
             ANY UNKNOWN LOGGED-OUT URL
             GO BACK TO LANDING
          ============================================= */}

          <Route
            path="*"
            element={
              <Navigate
                to="/"
                replace
              />
            }
          />

        </Routes>
      ) : (
        <AppRoutes
          user={user}
          setUser={setUser}
        />
      )}
    </BrowserRouter>
  );
}