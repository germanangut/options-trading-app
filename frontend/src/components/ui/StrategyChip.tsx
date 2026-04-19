import { Chip } from "./Chip";

type StrategyChipProps = {
  label: string;
};

export function StrategyChip({ label }: StrategyChipProps) {
  return <Chip tone="accent">{label}</Chip>;
}