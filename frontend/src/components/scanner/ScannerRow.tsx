"use client";

import { Star, Pin, TrendingUp, Zap } from "lucide-react";
import { useScannerStore } from "@/stores/scannerStore";
import { useUIStore } from "@/stores/uiStore";
import { useToggleFavorite, useTogglePinned } from "@/hooks/useScanner";
import { ScannerRecord } from "@/types/scanner";
import { cn, formatPrice, formatPercent, formatVolume, signalColor } from "@/lib/utils";
import { useLocale } from "@/hooks/useLocale";
import { useAuthStore } from "@/stores/authStore";

interface ScannerRowProps {
  record: ScannerRecord;
  onOpenTrade?: (record: ScannerRecord) => void;
}

export function ScannerRow({ record, onOpenTrade }: ScannerRowProps) {
  const { setSelectedRecordId } = useScannerStore();
  const { setDetailOpen } = useUIStore();
  const favMutation = useToggleFavorite();
  const pinMutation = useTogglePinned();
  const { t } = useLocale();
  const { isAuthenticated } = useAuthStore();

  const handleRowClick = () => {
    setSelectedRecordId(record.id);
    setDetailOpen(true);
  };

  const handleFavClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    favMutation.mutate(record.id);
  };

  const handlePinClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    pinMutation.mutate(record.id);
  };

  const trendSvg = () => {
    if (!record.trendSeries || record.trendSeries.length < 2) return null;
    const data = record.trendSeries;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const width = 60;
    const height = 20;
    const points = data
      .map((v, i) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - ((v - min) / range) * height;
        return `${x},${y}`;
      })
      .join(" ");

    const isPositive = record.spreadPct >= 0;
    return (
      <svg width={width} height={height} className="overflow-visible">
        <polyline
          points={points}
          fill="none"
          stroke={isPositive ? "#10B981" : "#EF4444"}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  };

  return (
    <tr
      onClick={handleRowClick}
      className={cn(
        "group cursor-pointer transition-colors hover:bg-row-hover",
        record.isPinned && "bg-blue-50/30"
      )}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          {record.iconUrl && (
            <img src={record.iconUrl} alt={record.symbol} className="w-8 h-8 rounded-full" />
          )}
          <div>
            <div className="font-semibold text-primary-text">{record.tokenName}</div>
            <div className="text-xs text-secondary-text">{record.pair}</div>
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-secondary-text">
          {record.scannerType}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-primary-text">{record.buyVenue}</td>
      <td className="px-4 py-3 text-sm text-primary-text text-right tabular-nums">
        {formatPrice(record.buyPrice)}
      </td>
      <td className="px-4 py-3 text-sm text-primary-text">{record.sellVenue}</td>
      <td className="px-4 py-3 text-sm text-primary-text text-right tabular-nums">
        {formatPrice(record.sellPrice)}
      </td>
      <td className="px-4 py-3 text-right">
        <span
          className={cn(
            "text-sm font-medium tabular-nums",
            record.spreadPct > 0 ? "text-positive" : "text-negative"
          )}
        >
          {formatPercent(record.spreadPct)}
        </span>
      </td>
      <td className="px-4 py-3 text-right">
        <span
          className={cn(
            "text-sm font-semibold tabular-nums",
            record.netProfitPct > 0 ? "text-positive" : "text-negative"
          )}
        >
          {formatPercent(record.netProfitPct)}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-secondary-text text-right tabular-nums">
        {formatVolume(record.volume24h)}
      </td>
      <td className="px-4 py-3">
        <span
          className={cn(
            "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold",
            signalColor(record.signal)
          )}
        >
          {t.signals[record.signal as keyof typeof t.signals] || record.signal}
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center justify-end gap-2">
          {trendSvg()}
          <button
            onClick={handleFavClick}
            className={cn(
              "p-1.5 rounded-md transition-colors",
              record.isFavorite
                ? "text-amber-500 hover:text-amber-600"
                : "text-gray-300 hover:text-amber-500 opacity-0 group-hover:opacity-100"
            )}
            title="Favorite"
          >
            <Star className={cn("w-4 h-4", record.isFavorite && "fill-current")} />
          </button>
          <button
            onClick={handlePinClick}
            className={cn(
              "p-1.5 rounded-md transition-colors",
              record.isPinned
                ? "text-accent-blue hover:text-accent-blue"
                : "text-gray-300 hover:text-accent-blue opacity-0 group-hover:opacity-100"
            )}
            title="Pin"
          >
            <Pin className={cn("w-4 h-4", record.isPinned && "fill-current")} />
          </button>
          {isAuthenticated && onOpenTrade && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onOpenTrade(record);
              }}
              className="rounded-md bg-blue-600 p-1.5 text-white opacity-0 transition-colors hover:bg-blue-700 group-hover:opacity-100"
              title="Open Trade"
            >
              <Zap className="h-4 w-4" />
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
