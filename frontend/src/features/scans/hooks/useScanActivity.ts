import { useMutationState } from "@tanstack/react-query";

import type { ScanRequest } from "../../../types/api";


type PendingScanActivity = {
  request: ScanRequest;
  submittedAt: number | null;
};

type ScanActivity = {
  isRunning: boolean;
  latestRequest: ScanRequest | null;
  latestSubmittedAt: number | null;
};


export function useScanActivity(): ScanActivity {
  const pendingMutations = useMutationState<PendingScanActivity | null>({
    filters: { mutationKey: ["run-scan"], status: "pending" },
    select: (mutation) => {
      const request = (mutation.state.variables as ScanRequest | undefined) ?? null;
      if (!request) {
        return null;
      }

      return {
        request,
        submittedAt: typeof mutation.state.submittedAt === "number" ? mutation.state.submittedAt : null,
      };
    },
  }).filter((value): value is PendingScanActivity => value !== null);

  const latestActivity = pendingMutations[pendingMutations.length - 1] ?? null;

  return {
    isRunning: pendingMutations.length > 0,
    latestRequest: latestActivity?.request ?? null,
    latestSubmittedAt: latestActivity?.submittedAt ?? null,
  };
}