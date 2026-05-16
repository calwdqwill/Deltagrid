"use client";

import { useScannerStore } from "@/stores/scannerStore";
import { useLocale } from "@/hooks/useLocale";
import { SearchBar } from "./SearchBar";
import { cn } from "@/lib/utils";

export function ScannerFilters() {
  const { filters, setFilters } = useScannerStore();
  const { t } = useLocale();

  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <SearchBar />

      <div className="flex items-center gap-2">
        <label className="text-sm text-secondary-text">{t.scanner.minSpread}</label>
        <input
          type="number"
          min={0}
          max={100}
          step={0.1}
          value={filters.minSpread}
          onChange={(e) => setFilters({ minSpread: parseFloat(e.target.value) || 0 })}
          className="w-20 px-3 py-2 rounded-lg border border-border bg-white text-sm text-primary-text focus:outline-none focus:ring-2 focus:ring-accent-blue/20"
        />
        <span className="text-sm text-secondary-text">%</span>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm text-secondary-text">{t.scanner.minVolume}</label>
        <input
          type="number"
          min={0}
          step={1000000}
          value={filters.minVolume || ""}
          onChange={(e) =>
            setFilters({ minVolume: e.target.value ? parseFloat(e.target.value) : undefined })
          }
          className="w-28 px-3 py-2 rounded-lg border border-border bg-white text-sm text-primary-text focus:outline-none focus:ring-2 focus:ring-accent-blue/20"
        />
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={filters.positiveNetOnly}
          onChange={(e) => setFilters({ positiveNetOnly: e.target.checked })}
          className="w-4 h-4 rounded border-border text-accent-blue focus:ring-accent-blue"
        />
        <span className="text-sm text-secondary-text">{t.scanner.positiveNetOnly}</span>
      </label>
    </div>
  );
}
