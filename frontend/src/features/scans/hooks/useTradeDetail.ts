import { useQuery } from "@tanstack/react-query";

import { getTradeDetail } from "../api/scansApi";
import { QUERY_KEYS } from "../../../lib/constants";
import { ApiError } from "../../../lib/apiClient";


export function useTradeDetail(scanId?: string, tradeId?: string) {
  return useQuery({
    queryKey: [...QUERY_KEYS.tradeDetail, scanId, tradeId],
    enabled: Boolean(scanId && tradeId),
    queryFn: async () => {
      if (!scanId || !tradeId) {
        return null;
      }

      try {
        return await getTradeDetail(scanId, tradeId);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }

        throw error;
      }
    },
  });
}