import { useQuery } from "@tanstack/react-query";

import { QUERY_KEYS } from "../../../lib/constants";
import { ApiError } from "../../../lib/apiClient";
import { getWorkbenchScenario } from "../api/scansApi";
import type { WorkbenchStrikeShift, WorkbenchWidthAdjustment } from "../../../types/api";


export function useWorkbenchScenario(
  scanId?: string,
  tradeId?: string,
  strikeShift: WorkbenchStrikeShift = "baseline",
  widthAdjustment: WorkbenchWidthAdjustment = "baseline",
) {
  return useQuery({
    queryKey: [...QUERY_KEYS.tradeWorkbench, scanId, tradeId, strikeShift, widthAdjustment],
    enabled: Boolean(scanId && tradeId),
    queryFn: async () => {
      if (!scanId || !tradeId) {
        return null;
      }

      try {
        return await getWorkbenchScenario(scanId, tradeId, strikeShift, widthAdjustment);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }

        throw error;
      }
    },
  });
}
