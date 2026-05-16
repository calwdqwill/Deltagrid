"use client";

import { useScannerStore } from "@/stores/scannerStore";
import { useLocale } from "@/hooks/useLocale";
import { usePreferenceStore } from "@/stores/preferenceStore";
import { cn } from "@/lib/utils";

export function ScannerTabs() {
  const { filters, setFilters } = useScannerStore();
  const { favorites, pinned } = usePreferenceStore();
  const { t } = useLocale();

  const tabs = [
    { value: "all", label: t.scanner.tabs.all },
    { value: "cex-cex", label: t.scanner.tabs.cexCex },
    { value: "dex-cex", label: t.scanner.tabs.dexCex },
    { value: "spot-perp", label: t.scanner.tabs.spotPerp },
    { value: "favorites", label: t.scanner.tabs.favorites, count: favorites.size },
    { value: "pinned", label: t.scanner.tabs.pinned, count: pinned.size },
  ];

  return (
    <div className="flex items-center gap-1 p-1 bg-white rounded-lg border border-border mb-4 w-fit">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          onClick={() => setFilters({ type: tab.value })}
          className={cn(
            "relative px-3.5 py-1.5 rounded-md text-sm font-medium transition-colors",
            filters.type === tab.value
              ? "bg-accent-blue text-white"
              : "text-secondary-text hover:text-primary-text hover:bg-row-hover"
          )}
        >
          {tab.label}
          {typeof tab.count === "number" && tab.count > 0 && (
            <span
              className={cn(
                "ml-1.5 px-1.5 py-0.5 rounded-full text-xs",
                filters.type === tab.value
                  ? "bg-white/20 text-white"
                  : "bg-gray-100 text-secondary-text"
              )}
            >
              {tab.count}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
