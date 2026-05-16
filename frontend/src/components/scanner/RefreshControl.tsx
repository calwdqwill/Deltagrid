"use client";

import { RefreshCw } from "lucide-react";
import { useScannerStore } from "@/stores/scannerStore";
import { useLocale } from "@/hooks/useLocale";
import { cn } from "@/lib/utils";

interface RefreshControlProps {
  onRefresh: () => void;
  countdown: number;
}

export function RefreshControl({ onRefresh, countdown }: RefreshControlProps) {
  const { isLoading, data } = useScannerStore();
  const { t } = useLocale();

  return (
    <div className="flex items-center gap-3 text-sm text-secondary-text">
      {data?.meta.lastUpdated && (
        <span>
          {t.scanner.lastUpdated}: {new Date(data.meta.lastUpdated).toLocaleTimeString()}
        </span>
      )}
      <span>
        {t.scanner.nextUpdate}: {countdown}s
      </span>
      <button
        onClick={onRefresh}
        disabled={isLoading}
        className={cn(
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-white hover:bg-row-hover transition-colors",
          isLoading && "opacity-50 cursor-not-allowed"
        )}
      >
        <RefreshCw className={cn("w-3.5 h-3.5", isLoading && "animate-spin")} />
        {t.scanner.refresh}
      </button>
    </div>
  );
}
