import { API_BASE_URL } from "./constants";

type RequestInitWithBody = RequestInit & {
  body?: unknown;
};

async function request<T>(path: string, init?: RequestInitWithBody): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
    body: init?.body !== undefined ? JSON.stringify(init.body) : undefined,
  });

  if (!response.ok) {
    let detail = "Request failed.";

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload?.detail) {
        detail = payload.detail;
      }
    } catch {
      detail = response.statusText || detail;
    }

    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  get<T>(path: string) {
    return request<T>(path, { method: "GET" });
  },
  post<T>(path: string, body: unknown) {
    return request<T>(path, { method: "POST", body });
  },
};
