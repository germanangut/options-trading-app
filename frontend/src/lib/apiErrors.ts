import { ApiError } from "./apiClient";

type ApiFailureKind = "auth" | "provider" | "system";

type ApiFailureDescription = {
  kind: ApiFailureKind;
  message: string;
};

const PROVIDER_STATUS_CODES = new Set([0, 502, 503, 504]);
const providerMessagePattern = /alpaca|provider|timed out|timeout|upstream|gateway|temporar(?:ily)? unavailable/i;

export function describeApiError(
  error: unknown,
  operation: "load" | "run",
  subject: string,
): ApiFailureDescription {
  if (error instanceof ApiError) {
    if (error.status === 401 || error.status === 403) {
      return {
        kind: "auth",
        message: `Authentication is required to ${operation} ${subject}. Sign in again, then retry.`,
      };
    }

    if (error.status === 400) {
      return {
        kind: "system",
        message: `The request to ${operation} ${subject} was rejected. Review the current parameters and try again.`,
      };
    }

    if (PROVIDER_STATUS_CODES.has(error.status) || providerMessagePattern.test(error.message)) {
      return {
        kind: "provider",
        message: `The market-data provider did not respond cleanly while trying to ${operation} ${subject}. Retry in a moment.`,
      };
    }

    return {
      kind: "system",
      message: `The platform could not ${operation} ${subject}. Retry in a moment, and check backend health if it continues.`,
    };
  }

  return {
    kind: "system",
    message: `The platform could not ${operation} ${subject}. Retry in a moment, and check backend health if it continues.`,
  };
}