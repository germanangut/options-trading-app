import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { QUERY_KEYS } from "../../../lib/constants";
import { getPaperDashboard } from "../api/scansApi";


export function usePaperDashboard() {
  return useQuery({
    queryKey: QUERY_KEYS.paperDashboard,
    queryFn: async () => getPaperDashboard(false),
  });
}


export function useRefreshPaperDashboard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => getPaperDashboard(true),
    onSuccess: (dashboard) => {
      queryClient.setQueryData(QUERY_KEYS.paperDashboard, dashboard);
    },
  });
}
