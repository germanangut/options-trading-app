import type { PropsWithChildren } from "react";


type ActionRowProps = PropsWithChildren<{
  className?: string;
}>;


export function ActionRow({ children, className }: ActionRowProps) {
  return <div className={["flex flex-wrap items-center gap-3", className].filter(Boolean).join(" ")}>{children}</div>;
}