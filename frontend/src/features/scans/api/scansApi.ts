import { apiClient } from "../../../lib/apiClient";
import type { ScanRequest, ScanResult } from "../../../types/api";

export function runScan(payload: ScanRequest): Promise<ScanResult> {
  return apiClient.post<ScanResult>("/scans", payload);
}

export function getLatestScan(): Promise<ScanResult> {
  return apiClient.get<ScanResult>("/scans/latest");
}
