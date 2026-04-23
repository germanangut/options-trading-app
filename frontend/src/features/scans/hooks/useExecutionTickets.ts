import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createExecutionTicket,
  getExecutionTicket,
  listExecutionTickets,
  listExecutionTicketsByTrade,
  patchExecutionTicket,
} from "../api/scansApi";
import { QUERY_KEYS } from "../../../lib/constants";
import type {
  CreateTicketPayload,
  PatchTicketPayload,
} from "../../../types/api";


export function useExecutionTickets() {
  return useQuery({
    queryKey: QUERY_KEYS.ticketList,
    queryFn: async () => {
      const response = await listExecutionTickets();
      return response.items;
    },
  });
}


export function useExecutionTicketsByTrade(tradeId?: string) {
  return useQuery({
    queryKey: [...QUERY_KEYS.ticketsByTrade, tradeId],
    enabled: Boolean(tradeId),
    queryFn: async () => {
      if (!tradeId) {
        return [];
      }
      const response = await listExecutionTicketsByTrade(tradeId);
      return response.items;
    },
  });
}


export function useExecutionTicket(ticketId?: string) {
  return useQuery({
    queryKey: ["execution-ticket", ticketId],
    enabled: Boolean(ticketId),
    queryFn: async () => {
      if (!ticketId) {
        return null;
      }
      return getExecutionTicket(ticketId);
    },
  });
}


export function useCreateExecutionTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateTicketPayload) => {
      return createExecutionTicket(payload);
    },
    onSuccess: async (ticket) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ticketList }),
        queryClient.invalidateQueries({ queryKey: [...QUERY_KEYS.ticketsByTrade, ticket.trade_id] }),
      ]);
      queryClient.setQueryData(["execution-ticket", ticket.ticket_id], ticket);
    },
  });
}


export function usePatchExecutionTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ ticketId, payload }: { ticketId: string; payload: PatchTicketPayload }) => {
      return patchExecutionTicket(ticketId, payload);
    },
    onSuccess: async (ticket) => {
      queryClient.setQueryData(["execution-ticket", ticket.ticket_id], ticket);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ticketList }),
        queryClient.invalidateQueries({ queryKey: [...QUERY_KEYS.ticketsByTrade, ticket.trade_id] }),
      ]);
    },
  });
}
