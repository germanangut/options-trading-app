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
    <div className="min-h-screen bg-surface-0 px-4 py-10 text-ink-1 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[80vh] max-w-5xl items-center justify-center">
        <div className="grid w-full gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          <section className="rounded-[28px] border border-slate-200 bg-white p-8 shadow-[0_24px_60px_rgba(15,23,42,0.08)]">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-3">Options Platform</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-ink-1">App Identity First</h1>
            <p className="mt-4 text-sm leading-6 text-ink-2">
              Sign in with an app-owned account to access your scans, history, alerts, and portfolio views.
              Broker connections remain a separate future seam and are not used for login.
            </p>
            <div className="mt-8 grid gap-3 text-sm text-ink-2">
              <div className="rounded-2xl bg-surface-1 p-4">User ownership now scopes latest scan, trade detail, and history access.</div>
              <div className="rounded-2xl bg-surface-1 p-4">Trading logic and scoring remain backend-owned and unchanged.</div>
              <div className="rounded-2xl bg-surface-1 p-4">Future broker account linking can be added later without replacing app identity.</div>
            </div>
          </section>

          <Card
            title={mode === "login" ? "Sign In" : "Create Account"}
            subtitle={mode === "login" ? "Use your app identity to access user-owned scan data." : "Create a local app account for this workspace."}
          >
            <div className="space-y-5">
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setMode("login")}
                  className={[
                    "rounded-xl px-3 py-2 text-sm font-semibold transition-colors",
                    mode === "login" ? "bg-accent text-white" : "bg-surface-2 text-ink-2",
                  ].join(" ")}
                >
                  Login
                </button>
                <button
                  type="button"
                  onClick={() => setMode("register")}
                  className={[
                    "rounded-xl px-3 py-2 text-sm font-semibold transition-colors",
                    mode === "register" ? "bg-accent text-white" : "bg-surface-2 text-ink-2",
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

              <form className="grid gap-4" onSubmit={handleSubmit}>
                <label className="grid gap-1 text-sm text-ink-2">
                  <span className="font-medium">Email</span>
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="rounded-xl border bg-white px-3 py-2 text-ink-1"
                    placeholder="you@example.com"
                    autoComplete="email"
                    required
                  />
                </label>

                <label className="grid gap-1 text-sm text-ink-2">
                  <span className="font-medium">Password</span>
                  <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="rounded-xl border bg-white px-3 py-2 text-ink-1"
                    placeholder="Minimum 8 characters"
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                    minLength={8}
                    required
                  />
                </label>

                <button
                  type="submit"
                  disabled={isSubmitting || auth.status === "loading"}
                  className="rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? "Submitting..." : mode === "login" ? "Sign In" : "Create Account"}
                </button>
              </form>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}