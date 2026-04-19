import { Chip } from "./Chip";

type SignalChipGroupProps = {
  items: string[];
};

export function SignalChipGroup({ items }: SignalChipGroupProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <Chip key={item} tone="neutral">
          {item}
        </Chip>
      ))}
    </div>
  );
}