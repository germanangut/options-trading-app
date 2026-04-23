import { useQuery } from "@tanstack/react-query";

import { QUERY_KEYS } from "../../../lib/constants";
import { ApiError } from "../../../lib/apiClient";
import { getTradeVariants } from "../api/scansApi";


export function useTradeVariants(scanId?: string, tradeId?: string) {
  return useQuery({
    queryKey: [...QUERY_KEYS.tradeVariants, scanId, tradeId],
    enabled: Boolean(scanId && tradeId),
    queryFn: async () => {
      if (!scanId || !tradeId) {
        return null;
      }

      try {
        return await getTradeVariants(scanId, tradeId);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }

        throw error;
      }
    },
  });
}
