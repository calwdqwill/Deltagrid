export const DEFAULT_REFRESH_INTERVAL = 60;
export const DEFAULT_MIN_SPREAD = 0.1;

export const SCANNER_TYPES = [
  { value: "all", labelKey: "tab_all" },
  { value: "cex-cex", labelKey: "tab_cex_cex" },
  { value: "dex-cex", labelKey: "tab_dex_cex" },
  { value: "spot-perp", labelKey: "tab_spot_perp" },
  { value: "favorites", labelKey: "tab_favorites" },
  { value: "pinned", labelKey: "tab_pinned" },
] as const;

export const REFRESH_INTERVALS = [
  { value: 30, label: "30s" },
  { value: 60, label: "1m" },
  { value: 120, label: "2m" },
  { value: 300, label: "5m" },
] as const;
