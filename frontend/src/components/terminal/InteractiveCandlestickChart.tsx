"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  createChart,
  HistogramSeries,
  type CandlestickData,
  type HistogramData,
  type MouseEventParams,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";
import { InteractiveCandle } from "@/lib/terminal/live-streams";
import { formatCompactCurrency, formatNumber } from "@/components/terminal/terminal-ui";

interface TooltipState {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
}

function toChartTime(seconds: number): UTCTimestamp {
  return seconds as UTCTimestamp;
}

function formatTime(seconds: number): string {
  const date = new Date(seconds * 1000);
  if (Number.isNaN(date.getTime())) return String(seconds);
  return date.toISOString().replace("T", " ").slice(0, 16);
}

function formatPrice(value: number): string {
  return value >= 100 ? `$${formatNumber(value)}` : `$${value.toFixed(4)}`;
}

function latestTooltip(candles: InteractiveCandle[]): TooltipState | null {
  const last = candles[candles.length - 1];
  if (!last) return null;

  return {
    time: formatTime(last.time),
    open: last.open,
    high: last.high,
    low: last.low,
    close: last.close,
    volume: last.quoteVolume ?? last.volume,
  };
}

export function InteractiveCandlestickChart({
  candles,
  height = 520,
}: {
  candles: InteractiveCandle[];
  height?: number;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(() => latestTooltip(candles));
  const fallbackTooltip = useMemo(() => latestTooltip(candles), [candles]);
  const activeTooltip = tooltip ?? fallbackTooltip;

  useEffect(() => {
    setTooltip(latestTooltip(candles));
  }, [candles]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || candles.length === 0) return;

    const chart = createChart(container, {
      width: container.clientWidth,
      height,
      autoSize: false,
      layout: {
        background: { type: ColorType.Solid, color: "#0D1322" },
        textColor: "#94A3B8",
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: "rgba(148, 163, 184, 0.08)" },
        horzLines: { color: "rgba(148, 163, 184, 0.10)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: "rgba(34, 211, 238, 0.45)", labelBackgroundColor: "#155E75" },
        horzLine: { color: "rgba(34, 211, 238, 0.35)", labelBackgroundColor: "#155E75" },
      },
      rightPriceScale: {
        borderColor: "rgba(148, 163, 184, 0.18)",
        scaleMargins: { top: 0.08, bottom: 0.22 },
      },
      timeScale: {
        borderColor: "rgba(148, 163, 184, 0.18)",
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 4,
        barSpacing: candles.length > 3000 ? 2 : 5,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#10B981",
      downColor: "#F43F5E",
      borderUpColor: "#10B981",
      borderDownColor: "#F43F5E",
      wickUpColor: "#5EEAD4",
      wickDownColor: "#FDA4AF",
      priceLineColor: "#22D3EE",
      priceFormat: { type: "price", precision: 4, minMove: 0.0001 },
    });

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
      base: 0,
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
      borderVisible: false,
      visible: false,
    });

    const candleData: CandlestickData<UTCTimestamp>[] = candles.map((candle) => ({
      time: toChartTime(candle.time),
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));

    const volumeData: HistogramData<UTCTimestamp>[] = candles.map((candle) => ({
      time: toChartTime(candle.time),
      value: candle.quoteVolume ?? candle.volume ?? 0,
      color: candle.close >= candle.open ? "rgba(16, 185, 129, 0.35)" : "rgba(244, 63, 94, 0.34)",
    }));

    candleSeries.setData(candleData);
    volumeSeries.setData(volumeData);
    chart.timeScale().fitContent();

    const handleCrosshairMove = (param: MouseEventParams<Time>) => {
      if (!param.time || !param.point) {
        setTooltip(latestTooltip(candles));
        return;
      }

      const candle = param.seriesData.get(candleSeries) as CandlestickData<UTCTimestamp> | undefined;
      const volume = param.seriesData.get(volumeSeries) as HistogramData<UTCTimestamp> | undefined;
      if (!candle || typeof candle.time !== "number") {
        setTooltip(latestTooltip(candles));
        return;
      }

      setTooltip({
        time: formatTime(candle.time),
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: volume?.value ?? null,
      });
    };

    chart.subscribeCrosshairMove(handleCrosshairMove);

    const resizeObserver = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width;
      if (width) chart.applyOptions({ width });
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.unsubscribeCrosshairMove(handleCrosshairMove);
      chart.remove();
    };
  }, [candles, height]);

  if (!candles.length) {
    return (
      <div className="flex min-h-[360px] items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.02] text-xs text-slate-500">
        No candle data
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2 text-xs md:grid-cols-6">
        <div>
          <div className="text-slate-500">Time</div>
          <div className="font-mono text-slate-200">{activeTooltip?.time ?? "-"}</div>
        </div>
        <div>
          <div className="text-slate-500">Open</div>
          <div className="font-mono text-slate-200">{activeTooltip ? formatPrice(activeTooltip.open) : "-"}</div>
        </div>
        <div>
          <div className="text-slate-500">High</div>
          <div className="font-mono text-emerald-300">{activeTooltip ? formatPrice(activeTooltip.high) : "-"}</div>
        </div>
        <div>
          <div className="text-slate-500">Low</div>
          <div className="font-mono text-rose-300">{activeTooltip ? formatPrice(activeTooltip.low) : "-"}</div>
        </div>
        <div>
          <div className="text-slate-500">Close</div>
          <div className="font-mono text-cyan-200">{activeTooltip ? formatPrice(activeTooltip.close) : "-"}</div>
        </div>
        <div>
          <div className="text-slate-500">Volume</div>
          <div className="font-mono text-slate-200">
            {activeTooltip?.volume != null ? formatCompactCurrency(activeTooltip.volume) : "-"}
          </div>
        </div>
      </div>
      <div
        ref={containerRef}
        className="w-full overflow-hidden rounded-md border border-white/[0.06] bg-[#0D1322]"
        style={{ height }}
      />
    </div>
  );
}
