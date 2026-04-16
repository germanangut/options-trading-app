import { useQuery } from "@tanstack/react-query";

import { getLatestScan } from "../api/scansApi";
import { QUERY_KEYS } from "../../../lib/constants";

export function useLatestScan() {
  return useQuery({
    queryKey: QUERY_KEYS.latestScan,
    queryFn: getLatestScan,
  });
}
