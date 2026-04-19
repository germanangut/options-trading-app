import { Link } from "react-router-dom";

import { formatPageTitle } from "../../lib/formatters";
import { useAuth } from "../../features/auth/AuthContext";
import { Chip } from "../../components/ui/Chip";
import { NAV_ITEMS } from "../../lib/constants";

type TopbarProps = {
  pathname: string;
  diagnosticsStatus?: {
    tone: "success" | "info" | "warning";
    label: string;
    detail: string;
    triggerLabel: string;
  } | null;
  onToggleDiagnostics?: () => void;
};

function isNavItemActive(pathname: string, to: string) {
  if (to === "/") {
    return pathname === "/";
  }

  if (to === "/qualified") {
    return pathname === "/qualified" || /^\/scans\/[^/]+\/trades\/[^/]+$/.test(pathname);
  }

  return pathname === to || pathname.startsWith(`${to}/`);
}

export function Topbar({ pathname, diagnosticsStatus, onToggleDiagnostics }: TopbarProps) {
  const auth = useAuth();

  const diagnosticsChipTone = diagnosticsStatus?.tone === "success"
    ? "success"
    : diagnosticsStatus?.tone === "warning"
      ? "warning"
      : "accent";

  return (
    <header className="border-b border-white/8 bg-surface-overlay/78 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl flex-col px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className="eyebrow-label">Live Decision Workspace</p>
              <span className="rounded-pill border border-white/8 bg-surface-2/65 px-2.5 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-ink-4">
                Review-first
              </span>
            </div>
            <h2 className="text-lg font-semibold tracking-tight text-ink-1">{formatPageTitle(pathname)}</h2>
          </div>
          <div className="flex w-full flex-col gap-3 sm:w-auto sm:items-end">
            {diagnosticsStatus ? (
              <div className="flex flex-wrap items-center gap-2" data-testid="diagnostics-status">
                <Chip tone={diagnosticsChipTone}>{diagnosticsStatus.label}</Chip>
                <p className="text-xs text-ink-3">{diagnosticsStatus.detail}</p>
                <button
                  type="button"
                  onClick={onToggleDiagnostics}
                  className="rounded-pill border border-white/10 bg-surface-overlay/70 px-3 py-1.5 text-xs font-semibold text-ink-2 transition hover:border-white/20 hover:bg-surface-2"
                >
                  {diagnosticsStatus.triggerLabel}
                </button>
              </div>
            ) : null}
            <div className="flex w-full flex-wrap items-center justify-between gap-3 sm:w-auto sm:justify-end">
              <div className="max-w-full truncate rounded-pill border border-white/8 bg-surface-2/70 px-3 py-1.5 text-xs font-medium text-ink-2 shadow-elevated">
                {auth.currentUser?.email ?? "Authenticated session"}
              </div>
              <button
                type="button"
                onClick={() => {
                  void auth.logout();
                }}
                className="rounded-pill border border-white/10 bg-surface-overlay/70 px-3 py-1.5 text-xs font-semibold text-ink-2 transition hover:border-white/20 hover:bg-surface-2"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        <nav aria-label="Workspace sections" className="border-t border-white/6 py-3" data-testid="workspace-nav">
          <div className="overflow-x-auto pb-1">
            <ul className="inline-flex min-w-max gap-2">
              {NAV_ITEMS.map((item) => {
                const active = isNavItemActive(pathname, item.to);

                return (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      aria-label={item.label}
                      aria-current={active ? "page" : undefined}
                      className={[
                        "flex items-center gap-2 rounded-pill border px-3 py-1.5 text-sm font-medium whitespace-nowrap transition-colors",
                        active
                          ? "border-accent/30 bg-accent-soft/60 text-ink-1 shadow-elevated"
                          : "border-white/8 bg-surface-overlay/45 text-ink-3 hover:border-white/14 hover:bg-surface-overlay/70 hover:text-ink-1",
                      ].join(" ")}
                    >
                      <span className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-ink-4">{item.shortcut}</span>
                      <span>{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        </nav>
      </div>
    </header>
  );
}
