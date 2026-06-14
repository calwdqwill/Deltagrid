import { Shell } from "@/components/layout/Shell";
import {
  formatSigned,
  KpiStrip,
  LineChart,
  SegmentedControl,
  SelectPill,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { getLiveFundingOverview } from "@/lib/terminal/live-data";

export const dynamic = "force-dynamic";

const fundingViews = [
  { view: "overview", label: "Overview", title: "Overview", href: "/funding" },
  { view: "history", label: "History", title: "Funding History", href: "/funding?view=history" },
  { view: "perp-dex", label: "Perp DEX", title: "Perp DEX Funding", href: "/funding?view=perp-dex" },
  { view: "arbitrage", label: "Arbitrage", title: "Funding Arbitrage", href: "/funding?view=arbitrage" },
  { view: "matrix", label: "Matrix", title: "Funding Matrix", href: "/funding?view=matrix" },
  { view: "predicted", label: "Predicted", title: "Predicted Funding", href: "/funding?view=predicted" },
  { view: "legs", label: "Legs", title: "Long / Short Legs", href: "/funding?view=legs" },
] as const;

type FundingView = (typeof fundingViews)[number]["view"];

function normalizeView(value?: string): FundingView {
  return fundingViews.some((item) => item.view === value) ? (value as FundingView) : "overview";
}

function pointLabel(timestamp: number): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return String(timestamp);
  return date.toISOString().slice(11, 16);
}

type FundingPageProps = {
  searchParams?: Promise<{ view?: string }>;
};

export default async function FundingPage({ searchParams }: FundingPageProps) {
  const params = await searchParams;
  const activeView = normalizeView(params?.view);
  const activeTab = fundingViews.find((item) => item.view === activeView) ?? fundingViews[0];
  const live = await getLiveFundingOverview();
  const data = live.data;

  const fundingSeries = data.history.map((point) => ({ label: pointLabel(point.time), value: point.rate }));
  const showMatrix = activeView === "overview" || activeView === "matrix" || activeView === "perp-dex";
  const showHistory = activeView === "overview" || activeView === "history";
  const showArbitrage = activeView === "overview" || activeView === "arbitrage";
  const showLegs = activeView === "overview" || activeView === "legs";
  const showPredicted = activeView === "overview" || activeView === "predicted";

  const arbitrageRows = data.arbitrage.map((item) => [
    <span key="asset" className="font-semibold text-cyan-200">
      {item.asset}
    </span>,
    item.longLeg,
    item.shortLeg,
    <span key="edge" className="font-mono text-emerald-300">
      {formatSigned(item.fundingEdge)}
    </span>,
    <span key="apr" className="font-mono text-slate-100">
      {item.netApr.toFixed(1)}%
    </span>,
    <span key="liq" className="font-mono">
      {item.liquidityScore}
    </span>,
    <span key="risk" className="font-mono text-amber-300">
      {item.riskScore}
    </span>,
  ]);

  const legsRows = data.longShortLegs.map((leg) => [
    leg.asset,
    leg.venue,
    <span key="receive" className={leg.receiveSide === "short" ? "text-rose-300" : "text-emerald-300"}>
      {leg.receiveSide === "short" ? "Short perp receives" : "Long perp receives"}
    </span>,
    <span key="rate" className={toneText(leg.currentRate >= 0 ? "positive" : "negative")}>
      {formatSigned(leg.currentRate)}
    </span>,
    <span key="apr" className="font-mono text-slate-100">
      {leg.estimatedApr.toFixed(1)}%
    </span>,
  ]);

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Funding</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">{activeTab.title}</h1>
          </div>
          <div className="flex items-center gap-2">
            <SegmentedControl
              items={fundingViews.map((item) => ({ label: item.label, href: item.href }))}
              active={activeTab.label}
            />
            <StatusBadge label={live.statusLabel} tone={live.statusTone} />
          </div>
        </div>

        <KpiStrip metrics={data.kpis} />

        <TerminalPanel>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <SelectPill label="Assets" value={data.assets.length ? data.assets.join(" / ") : "No rows"} />
            <SelectPill label="Providers" value={data.venues.length ? data.venues.join(" / ") : "No rows"} />
            <SelectPill label="Storage" value="PostgreSQL" />
            <SelectPill label="Mode" value="Funding / legs / arb" />
            <SelectPill label="Prediction" value="Current baseline" />
          </div>
        </TerminalPanel>

        {(showMatrix || showHistory) && (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            {showMatrix && (
              <TerminalPanel title="Funding Matrix (8h)" caption={live.sourceCaption}>
                {data.matrix.length > 0 && data.venues.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full border-separate border-spacing-0 text-xs">
                      <thead>
                        <tr>
                          <th className="border-b border-white/[0.08] bg-white/[0.03] px-3 py-2 text-left text-slate-500">
                            Asset
                          </th>
                          {data.venues.map((venue) => (
                            <th
                              key={venue}
                              className="border-b border-white/[0.08] bg-white/[0.03] px-3 py-2 text-left text-amber-200"
                            >
                              {venue}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.matrix.map((row) => (
                          <tr key={row[0]?.asset}>
                            <td className="border-b border-white/[0.06] px-3 py-2.5 font-semibold text-slate-100">
                              {row[0]?.asset}
                            </td>
                            {row.map((cell) => {
                              const hasRate = Number.isFinite(cell.rate);
                              const positive = hasRate && cell.rate >= 0;
                              return (
                                <td
                                  key={`${cell.asset}-${cell.venue}`}
                                  className={`border-b border-white/[0.06] px-3 py-2.5 font-mono ${
                                    !hasRate
                                      ? "bg-white/[0.025] text-slate-500"
                                      : positive
                                        ? "bg-emerald-500/16 text-emerald-200"
                                        : "bg-rose-500/18 text-rose-200"
                                  }`}
                                >
                                  {hasRate ? formatSigned(cell.rate) : "No data"}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                    No funding rows in PostgreSQL yet.
                  </div>
                )}
              </TerminalPanel>
            )}

            {showHistory && (
              <TerminalPanel title="Funding History" caption={live.historyLabel}>
                <div className="h-[310px]">
                  {fundingSeries.length > 1 ? (
                    <LineChart
                      data={fundingSeries}
                      color="#10B981"
                      height={280}
                      valueFormatter={(value) => formatSigned(value)}
                      tooltipFormatter={(point) => `${live.historyLabel} ${point.label}: ${formatSigned(point.value)}`}
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center rounded-md border border-white/10 bg-white/[0.035] text-sm text-slate-400">
                      No funding history in PostgreSQL yet.
                    </div>
                  )}
                </div>
              </TerminalPanel>
            )}
          </div>
        )}

        {(showArbitrage || showLegs) && (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_0.72fr]">
            {showArbitrage && (
              <TerminalPanel
                title="Funding Arbitrage Opportunities"
                caption="Derived from current persisted funding spread, before fees and execution constraints"
              >
                {arbitrageRows.length > 0 ? (
                  <TerminalTable
                    columns={["Asset", "Long Leg", "Short Leg", "Funding Edge", "Net APR", "Liquidity Score", "Risk Score"]}
                    rows={arbitrageRows}
                  />
                ) : (
                  <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                    No funding opportunities can be derived yet.
                  </div>
                )}
              </TerminalPanel>
            )}

            {showLegs && (
              <TerminalPanel title="Long / Short Legs" caption="Where funding is received and hedged">
                {legsRows.length > 0 ? (
                  <TerminalTable columns={["Asset", "Venue", "Receive", "Rate", "Est APR"]} rows={legsRows} />
                ) : (
                  <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                    No funding legs can be derived yet.
                  </div>
                )}
              </TerminalPanel>
            )}
          </div>
        )}

        {showPredicted && (
          <TerminalPanel
            title="Predicted Funding (Next 8h)"
            caption="Prediction model is not enabled yet; current rate is shown as baseline"
          >
            {data.predicted.length > 0 ? (
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
                {data.predicted.map((point) => {
                  const displayedRate = point.predicted ?? point.rate;
                  const hasPrediction = point.predicted !== undefined;

                  return (
                    <div
                      key={`${point.asset}-${point.venue}`}
                      className="rounded-lg border border-white/10 bg-white/[0.035] p-3"
                    >
                      <div className="text-xs text-slate-500">{point.asset}</div>
                      <div className="mt-2 font-mono text-lg text-slate-100">{formatSigned(displayedRate)}</div>
                      <div className={toneText(hasPrediction && displayedRate >= point.rate ? "positive" : "neutral")}>
                        {hasPrediction ? (displayedRate >= point.rate ? "Up" : "Down") : "Current"}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                No current funding rows for prediction baseline.
              </div>
            )}
          </TerminalPanel>
        )}
      </div>
    </Shell>
  );
}
