"use client";

import { useState } from "react";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { useScannerStore } from "@/stores/scannerStore";
import { useLocale } from "@/hooks/useLocale";
import { ScannerRecord } from "@/types/scanner";
import { cn, formatPrice, formatPercent, formatVolume, signalColor } from "@/lib/utils";
import { ScannerRow } from "./ScannerRow";

type SortKey = keyof ScannerRecord | null;
type SortDir = "asc" | "desc";

interface ScannerTableProps {
  onOpenTrade?: (record: ScannerRecord) => void;
}

export function ScannerTable({ onOpenTrade }: ScannerTableProps) {
  const { filteredRecords, isLoading, isError, errorMessage, data } = useScannerStore();
  const { t } = useLocale();
  const [sortKey, setSortKey] = useState<SortKey>("netProfitPct");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const sorted = [...filteredRecords].sort((a, b) => {
    if (!sortKey) return 0;
    const aVal = a[sortKey as keyof ScannerRecord];
    const bVal = b[sortKey as keyof ScannerRecord];
    if (typeof aVal === "number" && typeof bVal === "number") {
      return sortDir === "asc" ? aVal - bVal : bVal - aVal;
    }
    if (typeof aVal === "string" && typeof bVal === "string") {
      return sortDir === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    if (typeof aVal === "boolean" && typeof bVal === "boolean") {
      return sortDir === "asc" ? (aVal ? 1 : -1) - (bVal ? 1 : -1) : (bVal ? 1 : -1) - (aVal ? 1 : -1);
    }
    return 0;
  });

  const columns: { key: SortKey; label: string; align?: "left" | "right"; width?: string }[] = [
    { key: "tokenName", label: t.scanner.columns.token, width: "w-48" },
    { key: "scannerType", label: t.scanner.columns.type, width: "w-28" },
    { key: "buyVenue", label: t.scanner.columns.buyAt, width: "w-32" },
    { key: "buyPrice", label: t.scanner.columns.buyPrice, align: "right", width: "w-32" },
    { key: "sellVenue", label: t.scanner.columns.sellAt, width: "w-32" },
    { key: "sellPrice", label: t.scanner.columns.sellPrice, align: "right", width: "w-32" },
    { key: "spreadPct", label: t.scanner.columns.spread, align: "right", width: "w-24" },
    { key: "netProfitPct", label: t.scanner.columns.netProfit, align: "right", width: "w-28" },
    { key: "volume24h", label: t.scanner.columns.volume24h, align: "right", width: "w-28" },
    { key: "signal", label: t.scanner.columns.signal, width: "w-28" },
    { key: null, label: t.scanner.columns.actions, width: "w-20" },
  ];

  if (isLoading && !data) {
    return (
      <div className="flex items-center justify-center h-64 text-secondary-text">
        {t.scanner.loading}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-64 text-negative">
        {t.scanner.error}: {errorMessage}
      </div>
    );
  }

  if (sorted.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-secondary-text">
        {t.scanner.empty}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-border shadow-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-gray-50/50">
              {columns.map((col) => (
                <th
                  key={col.label}
                  onClick={() => col.key && handleSort(col.key)}
                  className={cn(
                    "px-4 py-3 text-xs font-semibold uppercase tracking-wider text-secondary-text cursor-pointer select-none hover:text-primary-text transition-colors",
                    col.align === "right" && "text-right",
                    col.align !== "right" && "text-left",
                    col.width
                  )}
                >
                  <div className={cn("flex items-center gap-1", col.align === "right" && "justify-end")}>
                    {col.label}
                    {col.key && (
                      <span className="inline-flex">
                        {sortKey === col.key ? (
                          sortDir === "desc" ? (
                            <ArrowDown className="w-3.5 h-3.5 text-accent-blue" />
                          ) : (
                            <ArrowUp className="w-3.5 h-3.5 text-accent-blue" />
                          )
                        ) : (
                          <ArrowUpDown className="w-3.5 h-3.5 text-gray-300" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {sorted.map((record) => (
              <ScannerRow key={record.id} record={record} onOpenTrade={onOpenTrade} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
