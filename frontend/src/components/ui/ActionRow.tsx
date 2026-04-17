import type { PropsWithChildren } from "react";


type ActionRowProps = PropsWithChildren<{
  className?: string;
}>;


export function ActionRow({ children, className }: ActionRowProps) {
  return <div className={["flex flex-wrap gap-2", className].filter(Boolean).join(" ")}>{children}</div>;
}