import { formatPageTitle } from "../../lib/formatters";
import { useAuth } from "../../features/auth/AuthContext";

type TopbarProps = {
  pathname: string;
};

export function Topbar({ pathname }: TopbarProps) {
  const auth = useAuth();

  return (
    <header className="border-b border-white/8 bg-surface-overlay/78 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="eyebrow-label">Live Decision Workspace</p>
            <span className="rounded-pill border border-white/8 bg-surface-2/65 px-2.5 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-ink-4">
              Review-first
            </span>
          </div>
          <h2 className="text-lg font-semibold tracking-tight text-ink-1">{formatPageTitle(pathname)}</h2>
        </div>
        <div className="flex items-center gap-3">
          <div className="rounded-pill border border-white/8 bg-surface-2/70 px-3 py-1.5 text-xs font-medium text-ink-2 shadow-elevated">
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
    </header>
  );
}
