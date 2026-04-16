import { formatPageTitle } from "../../lib/formatters";

type TopbarProps = {
  pathname: string;
};

export function Topbar({ pathname }: TopbarProps) {
  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-3">
            Migration Workspace
          </p>
          <h2 className="text-lg font-semibold text-ink-1">{formatPageTitle(pathname)}</h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-surface-1 px-3 py-1 text-xs font-medium text-ink-2">
          Backend-driven UI foundation
        </div>
      </div>
    </header>
  );
}
