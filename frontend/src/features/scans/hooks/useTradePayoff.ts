import { useQuery } from "@tanstack/react-query";

import { QUERY_KEYS } from "../../../lib/constants";
import { ApiError } from "../../../lib/apiClient";
import { getTradePayoff } from "../api/scansApi";


export function useTradePayoff(scanId?: string, tradeId?: string) {
  return useQuery({
    queryKey: [...QUERY_KEYS.tradePayoff, scanId, tradeId],
    enabled: Boolean(scanId && tradeId),
    queryFn: async () => {
      if (!scanId || !tradeId) {
        return null;
      }

      try {
        return await getTradePayoff(scanId, tradeId);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }

        throw error;
      }
    },
  });
}
