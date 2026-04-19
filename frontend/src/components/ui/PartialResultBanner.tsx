import { WarningBand } from "./WarningBand";

type PartialResultBannerProps = {
  title: string;
  message: string;
};

export function PartialResultBanner({ title, message }: PartialResultBannerProps) {
  return <WarningBand title={title}>{message}</WarningBand>;
}