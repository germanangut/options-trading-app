import { useMutation, useQueryClient } from "@tanstack/react-query";

import { runScan } from "../api/scansApi";
import { QUERY_KEYS } from "../../../lib/constants";
import type { ScanRequest } from "../../../types/api";

export function useRunScan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ScanRequest) => runScan(payload),
    onSuccess: (data) => {
      queryClient.setQueryData(QUERY_KEYS.latestScan, data);
    },
  });
}
