import type { QualifiedTradeRow } from "../types/api";

export function formatNumber(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(1);
  }

  return value;
}

export function formatDuration(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "-";
  }

  return `${value.toFixed(2)}s`;
}

export function formatTradeLabel(trade: Pick<QualifiedTradeRow, "ticker" | "strategy_label" | "strategy_type">) {
  const strategy = trade.strategy_label ?? trade.strategy_type ?? "Trade";
  return `${trade.ticker} - ${strategy}`;
}

export function formatPageTitle(pathname: string) {
  if (pathname === "/") {
    return "Overview";
  }

  return pathname
    .replace(/^\//, "")
    .split("/")
    .map((segment) => segment.replace(/-/g, " "))
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" / ");
}
