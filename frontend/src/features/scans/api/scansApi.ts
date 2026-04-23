import { apiClient } from "../../../lib/apiClient";
import type {
  ScanRequest,
  ScanResult,
  TradeDetailResponse,
  TradeLifecycleListResponse,
  TradeLifecycleRecord,
  TradeLifecycleUpsertPayload,
} from "../../../types/api";

export function runScan(payload: ScanRequest): Promise<ScanResult> {
  return apiClient.post<ScanResult>("/scans", payload);
}

export function getLatestScan(): Promise<ScanResult> {
  return apiClient.get<ScanResult>("/scans/latest");
}


export function getScanById(scanId: string): Promise<ScanResult> {
  return apiClient.get<ScanResult>(`/api/v1/scans/${encodeURIComponent(scanId)}`);
}


export function getTradeDetail(scanId: string, tradeId: string): Promise<TradeDetailResponse> {
  return apiClient.get<TradeDetailResponse>(
    `/api/v1/scans/${encodeURIComponent(scanId)}/trades/${encodeURIComponent(tradeId)}`,
  );
}

export function listTradeLifecycles(): Promise<TradeLifecycleListResponse> {
  return apiClient.get<TradeLifecycleListResponse>("/api/v1/lifecycle");
}

export function getTradeLifecycle(tradeId: string): Promise<TradeLifecycleRecord> {
  return apiClient.get<TradeLifecycleRecord>(`/api/v1/lifecycle/${encodeURIComponent(tradeId)}`);
}

export function upsertTradeLifecycle(
  tradeId: string,
  payload: TradeLifecycleUpsertPayload,
): Promise<TradeLifecycleRecord> {
  return apiClient.patch<TradeLifecycleRecord>(
    `/api/v1/lifecycle/${encodeURIComponent(tradeId)}`,
    payload,
  );
}
