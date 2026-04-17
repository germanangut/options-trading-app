import { useQuery } from "@tanstack/react-query";

import { getScanById } from "../api/scansApi";
import { QUERY_KEYS } from "../../../lib/constants";
import { ApiError } from "../../../lib/apiClient";


export function useScanById(scanId?: string) {
  return useQuery({
    queryKey: [...QUERY_KEYS.scanById, scanId],
    enabled: Boolean(scanId),
    queryFn: async () => {
      if (!scanId) {
        return null;
      }

      try {
        return await getScanById(scanId);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }

        throw error;
      }
    },
  });
}