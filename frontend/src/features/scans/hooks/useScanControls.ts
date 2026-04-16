import { useEffect, useState } from "react";

import { DEFAULT_SCAN_REQUEST } from "../../../lib/constants";
import type { ScanRequest, ScanResult } from "../../../types/api";

export type ScanControlMode = "guided" | "expert";

export function useScanControls(latestScan?: ScanResult | null) {
  const [mode, setMode] = useState<ScanControlMode>("guided");
  const [request, setRequest] = useState<ScanRequest>(DEFAULT_SCAN_REQUEST);

  useEffect(() => {
    const latestRequest = latestScan?.scan_metadata?.request;
    if (!latestRequest) {
      return;
    }

    setRequest({
      ...DEFAULT_SCAN_REQUEST,
      ...latestRequest,
      selected_strategy_keys:
        latestRequest.selected_strategy_keys?.length > 0
          ? latestRequest.selected_strategy_keys
          : DEFAULT_SCAN_REQUEST.selected_strategy_keys,
    });
  }, [latestScan]);

  function updateField<K extends keyof ScanRequest>(key: K, value: ScanRequest[K]) {
    setRequest((current) => ({ ...current, [key]: value }));
  }

  function toggleStrategy(strategyKey: string) {
    setRequest((current) => {
      const exists = current.selected_strategy_keys.includes(strategyKey);
      return {
        ...current,
        selected_strategy_keys: exists
          ? current.selected_strategy_keys.filter((key) => key !== strategyKey)
          : [...current.selected_strategy_keys, strategyKey],
      };
    });
  }

  function resetToDefaults() {
    setRequest(DEFAULT_SCAN_REQUEST);
  }

  return {
    mode,
    setMode,
    request,
    updateField,
    toggleStrategy,
    resetToDefaults,
  };
}
