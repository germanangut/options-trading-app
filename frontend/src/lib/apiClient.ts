import { API_BASE_URL } from "./constants";
import { getAuthToken } from "../features/auth/authStorage";


const DEFAULT_REQUEST_TIMEOUT_MS = 20000;


function resolveRequestTimeoutMs() {
  const configured = Number(import.meta.env.VITE_API_REQUEST_TIMEOUT_MS ?? DEFAULT_REQUEST_TIMEOUT_MS);
  return Number.isFinite(configured) && configured > 0 ? configured : DEFAULT_REQUEST_TIMEOUT_MS;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type RequestInitWithBody = Omit<RequestInit, "body"> & {
  body?: unknown;
};

async function request<T>(path: string, init?: RequestInitWithBody): Promise<T> {
  const authToken = getAuthToken();
  const { body, ...requestInit } = init ?? {};

  if (!API_BASE_URL && import.meta.env.PROD) {
    throw new ApiError("VITE_API_BASE_URL is not configured.", 500);
  }

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), resolveRequestTimeoutMs());

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...(requestInit.headers ?? {}),
      },
      ...requestInit,
      signal: controller.signal,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("The backend request timed out. Try again in a moment.", 504);
    }

    throw new ApiError(
      "Unable to reach the backend. Check that the API is live and cross-origin access is configured.",
      0,
    );
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (!response.ok) {
    let detail = "Request failed.";

    try {
      const payload = (await response.json()) as {
        detail?: string;
        error?: { message?: string };
      };
      if (payload?.error?.message) {
        detail = payload.error.message;
      } else if (payload?.detail) {
        detail = payload.detail;
      }
    } catch {
      detail = response.statusText || detail;
    }

    throw new ApiError(detail, response.status);
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
