import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number): string {
  if (price >= 1000) {
    return price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  } else if (price >= 1) {
    return price.toLocaleString("en-US", { minimumFractionDigits: 4, maximumFractionDigits: 4 });
  } else if (price >= 0.01) {
    return price.toLocaleString("en-US", { minimumFractionDigits: 6, maximumFractionDigits: 6 });
  } else {
    return price.toLocaleString("en-US", { minimumFractionDigits: 8, maximumFractionDigits: 8 });
  }
}

export function formatPercent(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function formatVolume(value?: number): string {
  if (value === undefined || value === null) return "—";
  if (value >= 1_000_000_000) {
    return `$${(value / 1_000_000_000).toFixed(2)}B`;
  } else if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(2)}M`;
  } else if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(2)}K`;
  }
  return `$${value.toFixed(2)}`;
}

export function signalColor(signal: string): string {
  switch (signal) {
    case "STRONG":
      return "text-positive-dark bg-emerald-50";
    case "BUY_SELL":
      return "text-positive bg-green-50";
    case "MARGINAL":
      return "text-marginal-signal bg-amber-50";
    case "HOLD":
    default:
      return "text-secondary-text bg-gray-100";
  }
}

export function dataStatusLabel(status: string): string {
  switch (status) {
    case "live":
      return "Live";
    case "cached":
      return "Cached";
    case "stale":
      return "Stale";
    case "fallback":
      return "Fallback";
    case "partial":
      return "Partial";
    case "unavailable":
      return "Unavailable";
    default:
      return status;
  }
}
