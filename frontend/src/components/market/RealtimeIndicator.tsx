"use client";

import { useStreamStore } from "@/stores/streamStore";
import { cn } from "@/lib/utils";

interface RealtimeIndicatorProps {
  className?: string;
}

export function RealtimeIndicator({ className }: RealtimeIndicatorProps) {
  const connected = useStreamStore((s) => s.connected);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full",
        connected
          ? "bg-green-50 text-green-700"
          : "bg-gray-100 text-gray-500",
        className
      )}
      title={connected ? "Real-time stream connected" : "Real-time stream disconnected"}
    >
      <span
        className={cn(
          "w-1.5 h-1.5 rounded-full",
          connected ? "bg-green-500 animate-pulse" : "bg-gray-400"
        )}
      />
      {connected ? "Live" : "Disconnected"}
    </span>
  );
}
