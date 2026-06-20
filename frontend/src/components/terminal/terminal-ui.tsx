import Link from "next/link";
import { ReactNode } from "react";
import { Activity, ArrowDownRight, ArrowUpRight, Circle, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { KpiMetric, MarketHeatmapItem, SeriesPoint } from "@/types/terminal";

const chartColors = ["#3B82F6", "#7C3AED", "#06B6D4", "#10B981", "#EC4899", "#F59E0B"];

export function formatCompactCurrency(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(2)}T`;
  if (abs >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `$${(value / 1_000).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

export function formatNumber(value: number): string {
  if (value >= 1000) return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
  if (value >= 10) return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
  return value.toLocaleString("en-US", { maximumFractionDigits: 4 });
}

export function formatSigned(value: number, suffix = "%"): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(Math.abs(value) < 1 ? 3 : 2)}${suffix}`;
}

function formatChartValue(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000_000) return `${(value / 1_000_000_000_000).toFixed(2)}T`;
  if (abs >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${(value / 1_000).toFixed(2)}K`;
  if (abs >= 10) return value.toFixed(2);
  if (abs >= 1) return value.toFixed(3);
  return value.toFixed(4);
}

export function toneText(tone?: string) {
  if (tone === "positive") return "text-emerald-400";
  if (tone === "negative") return "text-rose-400";
  if (tone === "warning") return "text-amber-300";
  return "text-slate-300";
}

export function toneBg(tone?: string) {
  if (tone === "positive") return "from-emerald-500/20 via-cyan-500/10 to-blue-500/10";
  if (tone === "negative") return "from-rose-500/24 via-fuchsia-500/12 to-indigo-500/10";
  if (tone === "warning") return "from-amber-500/24 via-orange-500/14 to-fuchsia-500/10";
  return "from-indigo-500/20 via-slate-700/28 to-slate-900/30";
}

export function TerminalPanel({
  title,
  caption,
  children,
  className,
  actions,
}: {
  title?: string;
  caption?: string;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
}) {
  return (
    <section
      className={cn(
        "rounded-lg border border-white/10 bg-[#0D1322]/88 shadow-[0_24px_80px_rgba(0,0,0,0.24)] backdrop-blur",
        className
      )}
    >
      {(title || caption || actions) && (
        <div className="flex min-h-12 items-center justify-between gap-3 border-b border-white/[0.08] px-4 py-3">
          <div>
            {title && <h2 className="text-sm font-semibold text-slate-100">{title}</h2>}
            {caption && <p className="mt-0.5 text-xs text-slate-500">{caption}</p>}
          </div>
          {actions}
        </div>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

export function KpiCard({ metric, featured = false }: { metric: KpiMetric; featured?: boolean }) {
  const Icon = metric.tone === "negative" ? ArrowDownRight : ArrowUpRight;
  return (
    <div
      className={cn(
        "relative min-h-28 overflow-hidden rounded-lg border border-white/10 bg-gradient-to-br p-4",
        toneBg(metric.tone),
        featured && "border-indigo-400/40 shadow-[0_0_40px_rgba(124,58,237,0.18)]"
      )}
    >
      <div className="relative z-10">
        <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-400">
          {metric.label}
        </div>
        <div className="mt-3 font-mono text-2xl font-semibold text-white">{metric.value}</div>
        <div className="mt-2 flex items-center gap-2 text-xs">
          {metric.delta && (
            <span className={cn("inline-flex items-center gap-1 font-medium", toneText(metric.tone))}>
              <Icon className="h-3.5 w-3.5" />
              {metric.delta}
            </span>
          )}
          {metric.caption && <span className="text-slate-500">{metric.caption}</span>}
        </div>
      </div>
      {metric.sparkline && (
        <Sparkline
          data={metric.sparkline}
          color={metric.tone === "negative" ? "#F43F5E" : metric.tone === "warning" ? "#F59E0B" : "#10B981"}
          className="absolute bottom-3 right-3 h-10 w-28 opacity-80"
        />
      )}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.10),transparent_38%)]" />
    </div>
  );
}

export function KpiStrip({ metrics }: { metrics: KpiMetric[] }) {
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-6">
      {metrics.map((metric, index) => (
        <KpiCard key={metric.label} metric={metric} featured={index === 0} />
      ))}
    </div>
  );
}

export function Sparkline({
  data,
  color = "#10B981",
  className,
}: {
  data: number[];
  color?: string;
  className?: string;
}) {
  const width = 120;
  const height = 42;
  if (!data.length) {
    return (
      <svg viewBox={`0 0 ${width} ${height}`} className={className} aria-hidden="true">
        <line x1="0" x2={width} y1={height / 2} y2={height / 2} stroke="rgba(148,163,184,0.28)" strokeWidth="2" />
      </svg>
    );
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const points = data
    .map((value, index) => {
      const x = (index / Math.max(data.length - 1, 1)) * width;
      const y = height - ((value - min) / span) * (height - 6) - 3;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className={className} aria-hidden="true">
      <polyline fill="none" stroke={color} strokeWidth="2.2" points={points} strokeLinecap="round" />
      <polyline
        fill="none"
        stroke={color}
        strokeOpacity="0.18"
        strokeWidth="7"
        points={points}
        strokeLinecap="round"
      />
    </svg>
  );
}

export function LineChart({
  data,
  color = "#F43F5E",
  height = 210,
  fill = true,
  valueFormatter = formatChartValue,
  tooltipFormatter,
}: {
  data: SeriesPoint[];
  color?: string;
  height?: number;
  fill?: boolean;
  valueFormatter?: (value: number) => string;
  tooltipFormatter?: (point: SeriesPoint) => string;
}) {
  const width = 720;
  const padding = { top: 18, right: 74, bottom: 30, left: 10 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  if (!data.length) {
    return (
      <div className="flex h-full min-h-[180px] items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.02] text-xs text-slate-500">
        No chart data
      </div>
    );
  }

  const values = data.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const last = data[data.length - 1];
  const axisTicks = [max, min + span * 0.66, min + span * 0.33, min];
  const xTicks = [
    data[0],
    data[Math.floor(data.length / 2)],
    data[data.length - 1],
  ].filter(Boolean);
  const points = data.map((point, index) => {
    const x = padding.left + (index / Math.max(data.length - 1, 1)) * plotWidth;
    const y = padding.top + plotHeight - ((point.value - min) / span) * plotHeight;
    return { x, y };
  });
  const polyline = points.map((point) => `${point.x},${point.y}`).join(" ");
  const area = `${padding.left},${padding.top + plotHeight} ${polyline} ${padding.left + plotWidth},${padding.top + plotHeight}`;
  const lastPoint = points[points.length - 1];

  return (
    <div className="flex h-full min-h-[180px] w-full flex-col">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="font-mono text-slate-300">Last {valueFormatter(last.value)}</span>
        <span className="font-mono text-slate-500">
          Range {valueFormatter(min)} - {valueFormatter(max)}
        </span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="min-h-0 w-full flex-1" role="img">
        <defs>
          <linearGradient id={`area-${color.replace("#", "")}`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.34" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        {axisTicks.map((tick, index) => {
          const y = padding.top + plotHeight - ((tick - min) / span) * plotHeight;
          return (
            <g key={`${tick}-${index}`}>
              <line x1={padding.left} x2={padding.left + plotWidth} y1={y} y2={y} stroke="rgba(148,163,184,0.12)" />
              <text x={width - 6} y={y + 4} textAnchor="end" className="fill-slate-500 text-[10px]">
                {valueFormatter(tick)}
              </text>
            </g>
          );
        })}
        {fill && <polygon points={area} fill={`url(#area-${color.replace("#", "")})`} />}
        <polyline fill="none" stroke={color} strokeWidth="2.5" points={polyline} strokeLinecap="round" />
        {points.map((point, index) => (
          <circle key={`${data[index].label}-${index}-hit`} cx={point.x} cy={point.y} r="9" fill="transparent" pointerEvents="all">
            <title>{tooltipFormatter ? tooltipFormatter(data[index]) : `${data[index].label}: ${valueFormatter(data[index].value)}`}</title>
          </circle>
        ))}
        {lastPoint && (
          <g>
            <circle cx={lastPoint.x} cy={lastPoint.y} r="4" fill={color} />
            <line x1={lastPoint.x} x2={padding.left + plotWidth} y1={lastPoint.y} y2={lastPoint.y} stroke={color} strokeOpacity="0.24" />
            <text x={padding.left + plotWidth + 6} y={lastPoint.y - 7} className="fill-slate-200 text-[10px]">
              {valueFormatter(last.value)}
            </text>
          </g>
        )}
        {xTicks.map((tick) => {
          const index = data.indexOf(tick);
          const x = padding.left + (index / Math.max(data.length - 1, 1)) * plotWidth;
          return (
            <text key={`${tick.label}-${index}`} x={x} y={height - 8} textAnchor={index === 0 ? "start" : index === data.length - 1 ? "end" : "middle"} className="fill-slate-500 text-[10px]">
              {tick.label}
            </text>
          );
        })}
      </svg>
    </div>
  );
}

export function BarChart({
  data,
  colors = chartColors,
  valueFormatter = formatChartValue,
}: {
  data: SeriesPoint[];
  colors?: string[];
  valueFormatter?: (value: number) => string;
}) {
  if (!data.length) {
    return (
      <div className="flex h-56 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.02] text-xs text-slate-500">
        No chart data
      </div>
    );
  }

  const max = Math.max(...data.map((point) => point.value), 1);
  const min = Math.min(...data.map((point) => point.value), 0);
  const labelStep = data.length > 90 ? 12 : data.length > 48 ? 6 : 1;
  return (
    <div className="flex h-56 flex-col">
      <div className="mb-2 flex justify-between text-xs">
        <span className="font-mono text-slate-300">Max {valueFormatter(max)}</span>
        <span className="font-mono text-slate-500">
          Range {valueFormatter(min)} - {valueFormatter(max)}
        </span>
      </div>
      <div className="flex min-h-0 flex-1 items-end gap-1.5">
        {data.map((point, index) => {
          const showLabel = index === 0 || index === data.length - 1 || index % labelStep === 0;
          return (
          <div key={point.label} className="flex h-full flex-1 flex-col items-center justify-end gap-2" title={`${point.label}: ${valueFormatter(point.value)}`}>
            <div
              className="w-full rounded-t-sm"
              style={{
                height: `${Math.max((point.value / max) * 100, 4)}%`,
                background: `linear-gradient(180deg, ${colors[index % colors.length]}, rgba(59,130,246,0.25))`,
              }}
            />
            <span className="h-3 text-[10px] text-slate-500">{showLabel ? point.label : ""}</span>
          </div>
          );
        })}
      </div>
    </div>
  );
}

export function DonutChart({ data, center }: { data: SeriesPoint[]; center: ReactNode }) {
  if (!data.length) {
    return (
      <div className="flex min-h-36 items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.02] text-xs text-slate-500">
        No segment data
      </div>
    );
  }

  const total = data.reduce((sum, point) => sum + point.value, 0) || 1;
  let offset = 25;
  const circles = data.map((point, index) => {
    const dash = (point.value / total) * 100;
    const circle = (
      <circle
        key={point.label}
        cx="50"
        cy="50"
        r="36"
        fill="transparent"
        stroke={chartColors[index % chartColors.length]}
        strokeWidth="12"
        strokeDasharray={`${dash} ${100 - dash}`}
        strokeDashoffset={offset}
      />
    );
    offset -= dash;
    return circle;
  });

  return (
    <div className="grid grid-cols-[140px_1fr] items-center gap-4">
      <div className="relative h-36 w-36">
        <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
          <circle cx="50" cy="50" r="36" fill="transparent" stroke="rgba(148,163,184,0.16)" strokeWidth="12" />
          {circles}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-center">{center}</div>
      </div>
      <div className="space-y-2">
        {data.map((point, index) => (
          <div key={point.label} className="flex items-center justify-between gap-3 text-xs">
            <span className="inline-flex items-center gap-2 text-slate-300">
              <Circle className="h-2.5 w-2.5 fill-current" style={{ color: chartColors[index % chartColors.length] }} />
              {point.label}
            </span>
            <span className="font-mono text-slate-400">{point.value.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function Heatmap({ items }: { items: MarketHeatmapItem[] }) {
  if (!items.length) {
    return (
      <div className="flex h-[270px] items-center justify-center rounded-md border border-white/[0.06] bg-white/[0.02] text-xs text-slate-500">
        No market data
      </div>
    );
  }

  return (
    <div className="grid auto-rows-[92px] grid-cols-2 gap-1 md:grid-cols-4 xl:grid-cols-6">
      {items.map((item, index) => {
        const isBig = index === 0 || index === 1;
        const isNegative = item.change24h < 0;
        return (
          <div
            key={item.symbol}
            className={cn(
              "flex min-w-0 flex-col justify-center overflow-hidden rounded-md border border-white/[0.08] p-3",
              isBig ? "col-span-2 row-span-2" : "col-span-1 row-span-1",
              isNegative
                ? "bg-gradient-to-br from-rose-500/42 to-rose-950/42"
                : "bg-gradient-to-br from-emerald-500/36 to-emerald-950/36"
            )}
          >
            <div className="flex items-center gap-2">
              {item.image ? (
                <img src={item.image} alt="" className={cn("rounded-full", isBig ? "h-8 w-8" : "h-5 w-5")} />
              ) : (
                <span className={cn("flex items-center justify-center rounded-full bg-white/12 font-bold text-white", isBig ? "h-8 w-8 text-sm" : "h-5 w-5 text-[9px]")}>
                  {item.symbol[0]}
                </span>
              )}
              <div className={cn("min-w-0 truncate font-semibold text-white", isBig ? "text-3xl" : "text-xs")}>
                {item.symbol}
              </div>
            </div>
            <div className={cn("mt-2 truncate font-mono font-semibold text-white", isBig ? "text-2xl" : "text-xs")}>
              {item.price >= 100 ? `$${formatNumber(item.price)}` : `$${item.price.toFixed(4)}`}
            </div>
            <div className={cn("mt-1 truncate font-mono", isBig ? "text-sm" : "text-xs", isNegative ? "text-rose-300" : "text-emerald-300")}>
              {formatSigned(item.change24h)}
            </div>
            {isBig && <div className="mt-1 truncate text-xs text-slate-300">{formatCompactCurrency(item.marketCap)}</div>}
          </div>
        );
      })}
    </div>
  );
}

export function TerminalTable({
  columns,
  rows,
  className,
}: {
  columns: string[];
  rows: ReactNode[][];
  className?: string;
}) {
  return (
    <div className={cn("max-w-full overflow-x-auto", className)} style={{ overflowX: "auto" }}>
      <table className="w-full border-separate border-spacing-0 text-left text-xs">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column}
                className="border-b border-white/[0.08] bg-white/[0.03] px-3 py-2.5 font-medium text-slate-500 first:rounded-tl-md last:rounded-tr-md"
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((row, rowIndex) => (
              <tr key={rowIndex} className="group">
                {row.map((cell, cellIndex) => (
                  <td
                    key={cellIndex}
                    className="border-b border-white/[0.06] px-3 py-2.5 text-slate-300 transition-colors group-hover:bg-white/[0.035]"
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length} className="border-b border-white/[0.06] px-3 py-6 text-center text-slate-500">
                No rows
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export function StatusBadge({
  label,
  tone = "neutral",
}: {
  label: string;
  tone?: "positive" | "negative" | "warning" | "neutral";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[11px] font-medium",
        tone === "positive" && "border-emerald-400/25 bg-emerald-400/10 text-emerald-300",
        tone === "negative" && "border-rose-400/25 bg-rose-400/10 text-rose-300",
        tone === "warning" && "border-amber-300/25 bg-amber-300/10 text-amber-200",
        tone === "neutral" && "border-white/10 bg-white/[0.04] text-slate-300"
      )}
    >
      <Activity className="h-3 w-3" />
      {label}
    </span>
  );
}

type SegmentedControlItem = string | { label: string; href?: string };

export function SegmentedControl({ items, active }: { items: SegmentedControlItem[]; active: string }) {
  return (
    <div className="flex flex-wrap gap-1 rounded-lg border border-white/10 bg-black/18 p-1">
      {items.map((item) => {
        const label = typeof item === "string" ? item : item.label;
        const className = cn(
          "inline-flex min-h-8 items-center rounded-md px-3 text-xs font-medium text-slate-400 transition-colors hover:text-slate-100",
          label === active && "bg-indigo-500/30 text-white shadow-[inset_0_-1px_0_rgba(129,140,248,0.8)]"
        );

        if (typeof item !== "string" && item.href) {
          return (
            <Link key={label} href={item.href} className={className} aria-current={label === active ? "page" : undefined}>
              {label}
            </Link>
          );
        }

        return (
          <button key={label} className={className} type="button">
            {label}
          </button>
        );
      })}
    </div>
  );
}

export function SelectPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-36 rounded-lg border border-white/10 bg-black/18 px-3 py-2">
      <div className="text-[10px] uppercase tracking-[0.08em] text-slate-500">{label}</div>
      <div className="mt-1 text-sm font-medium text-slate-100">{value}</div>
    </div>
  );
}

export function LinkButton({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-indigo-400/30 bg-indigo-500/14 px-3 text-xs font-semibold text-indigo-100 transition-colors hover:bg-indigo-500/24"
    >
      {children}
      <ExternalLink className="h-3.5 w-3.5" />
    </Link>
  );
}
