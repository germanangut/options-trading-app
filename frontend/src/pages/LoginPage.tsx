import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { Banner } from "../components/ui/Banner";
import { Card } from "../components/ui/Card";
import { useAuth } from "../features/auth/AuthContext";


type Mode = "login" | "register";


export function LoginPage() {
  const navigate = useNavigate();
  const auth = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (auth.status === "authenticated") {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      if (mode === "login") {
        await auth.login({ email, password });
      } else {
        await auth.register({ email, password });
      }

      navigate("/", { replace: true });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-surface-0 px-4 py-10 text-ink-1 sm:px-6 lg:px-8" data-testid="login-page-root">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(57,192,187,0.14),transparent_24%),radial-gradient(circle_at_bottom_right,rgba(255,189,89,0.08),transparent_20%)]" aria-hidden="true" />
      <div className="mx-auto flex min-h-[80vh] max-w-5xl items-center justify-center">
        <div className="grid w-full gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          <section className="panel-shell panel-glow relative overflow-hidden rounded-[28px] p-8" data-testid="login-hero-panel">
            <div className="absolute inset-0 app-grid-glow opacity-15" aria-hidden="true" />
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent/30 to-transparent" aria-hidden="true" />
            <div className="relative">
              <div className="flex flex-wrap items-center gap-2">
                <p className="eyebrow-label">Options Platform</p>
                <span className="rounded-pill border border-accent/20 bg-accent-soft/35 px-2.5 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-accent">
                  App identity
                </span>
              </div>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-ink-1">App Identity First</h1>
              <p className="mt-4 text-sm leading-6 text-ink-2">
              Sign in with an app-owned account to access your scans, history, alerts, and portfolio views.
              Broker connections remain a separate future seam and are not used for login.
              </p>
              <div className="mt-8 grid gap-3 text-sm text-ink-2">
                <div className="rounded-2xl border border-white/8 bg-surface-overlay/60 p-4">User ownership now scopes latest scan, trade detail, and history access.</div>
                <div className="rounded-2xl border border-white/8 bg-surface-overlay/60 p-4">Trading logic and scoring remain backend-owned and unchanged.</div>
                <div className="rounded-2xl border border-white/8 bg-surface-overlay/60 p-4">Future broker account linking can be added later without replacing app identity.</div>
              </div>
              <p className="mt-6 text-xs leading-5 text-ink-4">
                This route should feel like a secure workspace entrance, not a separate product with a different visual language.
              </p>
            </div>
          </section>

          <Card
            eyebrow="Workspace Access"
            title={mode === "login" ? "Sign In" : "Create Account"}
            subtitle={mode === "login" ? "Use your app identity to access user-owned scan data." : "Create a local app account for this workspace."}
            className="self-center"
          >
            <div className="space-y-5">
              <div className="grid grid-cols-2 gap-2" data-testid="auth-mode-toggle">
                <button
                  type="button"
                  onClick={() => setMode("login")}
                  data-testid="login-mode-button"
                  className={[
                    "rounded-xl border px-3 py-2 text-sm font-semibold transition-colors",
                    mode === "login" ? "border-accent/25 bg-accent text-surface-0 shadow-elevated" : "border-white/8 bg-surface-2 text-ink-2",
                  ].join(" ")}
                >
                  Login
                </button>
                <button
                  type="button"
                  onClick={() => setMode("register")}
                  data-testid="register-mode-button"
                  className={[
                    "rounded-xl border px-3 py-2 text-sm font-semibold transition-colors",
                    mode === "register" ? "border-accent/25 bg-accent text-surface-0 shadow-elevated" : "border-white/8 bg-surface-2 text-ink-2",
                  ].join(" ")}
                >
                  Register
                </button>
              </div>

              {errorMessage ? (
                <Banner tone="danger" title="Authentication failed">
                  {errorMessage}
                </Banner>
              ) : null}

              <form className="grid gap-4" onSubmit={handleSubmit} data-testid="login-form">
                <label className="grid gap-1 text-sm text-ink-2">
                  <span className="font-medium">Email</span>
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="rounded-xl border border-white/10 bg-surface-overlay/70 px-3 py-2 text-ink-1 outline-none transition focus:border-accent/35"
                    placeholder="you@example.com"
                    autoComplete="email"
                    required
                    data-testid="login-email-input"
                  />
                </label>

                <label className="grid gap-1 text-sm text-ink-2">
                  <span className="font-medium">Password</span>
                  <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="rounded-xl border border-white/10 bg-surface-overlay/70 px-3 py-2 text-ink-1 outline-none transition focus:border-accent/35"
                    placeholder="Minimum 8 characters"
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                    minLength={8}
                    required
                    data-testid="login-password-input"
                  />
                </label>

                <button
                  type="submit"
                  disabled={isSubmitting || auth.status === "loading"}
                  className="rounded-xl border border-accent/25 bg-accent px-4 py-2.5 text-sm font-semibold text-surface-0 transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
                  data-testid="login-submit-button"
                >
                  {isSubmitting ? "Submitting..." : mode === "login" ? "Sign In" : "Create Account"}
                </button>
              </form>

              <p className="text-xs leading-5 text-ink-4">
                Theme QA baseline: dark surface, accent primary action, ink hierarchy, and consistent premium spacing across both auth modes.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}