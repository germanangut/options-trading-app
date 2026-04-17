import { useMutationState } from "@tanstack/react-query";

import type { ScanRequest } from "../../../types/api";


export function useScanActivity() {
  const pendingMutations = useMutationState<ScanRequest | null>({
    filters: { mutationKey: ["run-scan"], status: "pending" },
    select: (mutation) => (mutation.state.variables as ScanRequest | undefined) ?? null,
  }).filter((value): value is ScanRequest => value !== null);

  return {
    isRunning: pendingMutations.length > 0,
    latestRequest: pendingMutations[pendingMutations.length - 1] ?? null,
  };
}