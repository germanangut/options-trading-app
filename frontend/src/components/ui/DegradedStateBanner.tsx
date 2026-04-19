import { WarningBand } from "./WarningBand";

type DegradedStateBannerProps = {
  title: string;
  message: string;
  tone?: "info" | "success" | "warning" | "danger";
};

export function DegradedStateBanner({ title, message, tone = "warning" }: DegradedStateBannerProps) {
  return (
    <WarningBand title={title} tone={tone}>
      {message}
    </WarningBand>
  );
}