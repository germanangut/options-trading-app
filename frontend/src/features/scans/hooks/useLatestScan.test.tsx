import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../../../lib/apiClient";
import { getLatestScan } from "../api/scansApi";
import { useLatestScan } from "./useLatestScan";


vi.mock("../api/scansApi", () => ({
  getLatestScan: vi.fn(),
}));


function Wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}


function Probe() {
  const query = useLatestScan();

  if (query.isLoading) {
    return <div>loading</div>;
  }

  return <div>{query.data === null ? "empty" : "present"}</div>;
}


describe("useLatestScan", () => {
  it("treats a missing latest scan as an empty state instead of an error", async () => {
    vi.mocked(getLatestScan).mockRejectedValueOnce(new ApiError("No scan result is available yet.", 404));

    render(
      <Wrapper>
        <Probe />
      </Wrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("empty")).toBeInTheDocument();
    });
  });
});