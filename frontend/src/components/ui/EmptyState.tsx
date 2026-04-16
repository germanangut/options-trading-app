type EmptyStateProps = {
  title: string;
  message: string;
};

export function EmptyState({ title, message }: EmptyStateProps) {
  return (
    <div className="rounded-panel border border-dashed border-slate-300 bg-surface-1 px-6 py-10 text-center">
      <h3 className="text-lg font-semibold text-ink-1">{title}</h3>
      <p className="mx-auto mt-2 max-w-2xl text-sm text-ink-2">{message}</p>
    </div>
  );
}
