import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getTradeLifecycle,
  listTradeLifecycles,
  upsertTradeLifecycle,
} from "../api/scansApi";
import { QUERY_KEYS } from "../../../lib/constants";
import type {
  TradeLifecycleRecord,
  TradeLifecycleState,
  TradeLifecycleUpsertPayload,
} from "../../../types/api";


export function useLifecycleRecords() {
  return useQuery({
    queryKey: QUERY_KEYS.lifecycleList,
    queryFn: async () => {
      const response = await listTradeLifecycles();
      return response.items;
    },
  });
}


export function useTradeLifecycle(tradeId?: string) {
  return useQuery({
    queryKey: [...QUERY_KEYS.tradeLifecycle, tradeId],
    enabled: Boolean(tradeId),
    queryFn: async (): Promise<TradeLifecycleRecord | null> => {
      if (!tradeId) {
        return null;
      }

      return getTradeLifecycle(tradeId);
    },
  });
}


export function useUpsertTradeLifecycle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ tradeId, payload }: { tradeId: string; payload: TradeLifecycleUpsertPayload }) => {
      return upsertTradeLifecycle(tradeId, payload);
    },
    onSuccess: async (record, variables) => {
      queryClient.setQueryData([...QUERY_KEYS.tradeLifecycle, variables.tradeId], record);
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.lifecycleList });
    },
  });
}


export function getLifecycleStateLabel(state: TradeLifecycleState | string | null | undefined): string {
  const normalized = (state ?? "new").toString();
  const labels: Record<string, string> = {
    new: "New",
    saved: "Saved",
    watching: "Watching",
    execution_ready: "Execution Ready",
    paper_submitted: "Paper Submitted",
    paper_filled: "Paper Filled",
    paper_closed: "Paper Closed",
    dismissed: "Dismissed",
  };

  return labels[normalized] ?? "New";
}
