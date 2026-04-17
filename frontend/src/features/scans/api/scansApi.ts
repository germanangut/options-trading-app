import { apiClient } from "../../../lib/apiClient";
import type { ScanRequest, ScanResult, TradeDetailResponse } from "../../../types/api";

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
