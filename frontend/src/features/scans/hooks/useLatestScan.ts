import { useQuery } from "@tanstack/react-query";

import { getLatestScan } from "../api/scansApi";
import { QUERY_KEYS } from "../../../lib/constants";
import { ApiError } from "../../../lib/apiClient";

export function useLatestScan() {
  return useQuery({
    queryKey: QUERY_KEYS.latestScan,
    queryFn: async () => {
      try {
        return await getLatestScan();
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }

        throw error;
      }
    },
  });
}
