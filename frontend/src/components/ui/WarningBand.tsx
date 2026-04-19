import type { PropsWithChildren } from "react";
import { Banner } from "./Banner";

type WarningBandProps = PropsWithChildren<{
  title: string;
  tone?: "info" | "success" | "warning" | "danger";
}>;

export function WarningBand({ title, tone = "warning", children }: WarningBandProps) {
  return (
    <Banner tone={tone} title={title}>
      {children}
    </Banner>
  );
}