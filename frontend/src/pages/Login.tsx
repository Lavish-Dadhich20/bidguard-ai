import { useState } from "react";
import type { FormEvent } from "react";
import { LockKeyhole, Mail, ShieldCheck } from "lucide-react";
import { api } from "../services/api";
import type { User } from "../types";

export function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();

    setBusy(true);
    setError("");

    try {
      onLogin(
        await api.login({
          username,
          password,
        })
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to sign in."
      );
    } finally {
      setBusy(false);
    }
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

      <form
        className="login-card"
        onSubmit={submit}
      >
        <div className="section-kicker">
          SECURE ACCESS
        </div>

        <h2>Sign in</h2>

        <p className="muted">
          Use your authorized BidGuard account.
        </p>

        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        <label>
          Mobile Number / Username

          <input
            value={username}
            onChange={(e) =>
              setUsername(e.target.value)
            }
            autoComplete="username"
            required
            placeholder="Enter mobile number or username"
          />
        </label>

        <label>
          Password

          <input
            type="password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            autoComplete="current-password"
            required
            placeholder="Enter password"
          />
        </label>

        <button
          className="btn primary wide"
          disabled={busy}
        >
          {busy
            ? "Signing in…"
            : "Login"}
        </button>

        <button
          type="button"
          className="text-btn"
          onClick={() =>
            alert(
              "Password recovery must be handled by the connected backend."
            )
          }
        >
          Forgot Password
        </button>

        <div className="login-footer">
          <LockKeyhole size={16} />

          <span>
            Authentication is handled by your backend.
          </span>
        </div>
      </form>
    </div>
  );
}