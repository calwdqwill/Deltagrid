import { Shell } from "@/components/layout/Shell";
import {
  formatCompactCurrency,
  formatNumber,
  KpiStrip,
  LinkButton,
  SegmentedControl,
  SelectPill,
  StatusBadge,
  TerminalPanel,
  TerminalTable,
  toneText,
} from "@/components/terminal/terminal-ui";
import { getLiveDataHealth } from "@/lib/terminal/live-data";
import {
  getLiveArbitrageScanner,
  getLiveAsterMarkets,
  getLiveCoinGlassPerpDexMarkets,
  getLiveDydxMarkets,
  getLiveGmxMarkets,
  getLiveHyperliquidMarkets,
  getLiveLighterMarkets,
  getLiveMarketMatrix,
  getLivePerpDexRouteConstraints,
  getLivePerpDexRouteModel,
  LiveArbitrageOpportunity,
  LivePerpDexRouteCostDiagnosticBlockerBreakdown,
  LivePerpDexRouteCostDiagnosticComponent,
  LivePerpDexRouteCostDiagnosticDepthPolicyChecklist,
  LivePerpDexRouteCostDiagnosticNextActionBreakdown,
  LivePerpDexRouteCostDiagnosticReadinessRollup,
  LivePerpDexRouteCostDiagnosticRequiredPolicyInputBreakdown,
  LivePerpDexRouteCostDiagnosticRequiredInputBreakdown,
  LivePerpDexRouteCostDiagnosticRouteReadyEvidenceChecklist,
  LivePerpDexRouteCostDiagnosticSafeUseBreakdown,
  LivePerpDexRouteCostDiagnosticSourceFieldBreakdown,
  LivePerpDexRouteCostDiagnosticSourceInputActionCoverage,
  LivePerpDexRouteCostDiagnosticVenueEvidenceStatus,
  LivePerpDexRouteCostDiagnosticVenueBreakdown,
  LivePerpDexGmxRateCarryInputCheck,
  LivePerpDexGmxRateCarryReadinessSummary,
  LivePerpDexGmxRateCarrySourceEvidenceCheck,
  LivePerpDexGmxRateCarrySourceEvidenceSummary,
  LivePerpDexGmxRateFixtureReadiness,
  LivePerpDexGmxRateHelperSourceFollowUpItem,
  LivePerpDexGmxRateHelperSourceFollowUpSummary,
  LivePerpDexGmxRateLiveHelperSourceReview,
  LivePerpDexGmxRateLiveHelperSourceSummary,
  LivePerpDexGmxRateMappingDecisionCheck,
  LivePerpDexGmxRateMappingBlockerBreakdown,
  LivePerpDexGmxRateMappingReview,
  LivePerpDexGmxRateMappingReviewItem,
  LivePerpDexGmxRateSemantics,
  LivePerpDexGmxRateSideAwareFixtureExpectation,
  LivePerpDexRouteConstraints,
  LivePerpDexRouteModel,
  LivePerpDexRouteModelRequiredInput,
  LivePerpDexVenueMarket,
  LivePerpDexVenueSnapshot,
  LiveMatrixRow,
  CORE_SYMBOLS_LABEL,
} from "@/lib/terminal/live-streams";
import { KpiMetric } from "@/types/terminal";

export const dynamic = "force-dynamic";

const perpDexViews = [
  { view: "overview", label: "Overview", title: "Intelligence Overview", href: "/perp-dex" },
  { view: "venues", label: "Venues", title: "Venues", href: "/perp-dex?view=venues" },
  { view: "open-interest", label: "Open Interest", title: "Open Interest", href: "/perp-dex?view=open-interest" },
  { view: "liquidity", label: "Liquidity", title: "Liquidity", href: "/perp-dex?view=liquidity" },
  { view: "opportunities", label: "Opportunities", title: "Opportunities", href: "/perp-dex?view=opportunities" },
] as const;

type PerpDexView = (typeof perpDexViews)[number]["view"];
type SourceStatusTone = "positive" | "warning" | "negative" | "neutral";

type PerpDexSourceStatusRow = {
  source: string;
  layer: string;
  status: string;
  tone: SourceStatusTone;
  rows: string;
  evidence: string;
  boundary: string;
  lastCheck: string;
};

function normalizeView(value?: string): PerpDexView {
  return perpDexViews.some((item) => item.view === value) ? (value as PerpDexView) : "overview";
}

function formatRows(value?: number): string {
  return (value ?? 0).toLocaleString("en-US");
}

function formatSyncTime(value: unknown): string {
  if (typeof value !== "string") return "No sync";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "No sync";
  return date.toLocaleString("en-US", { dateStyle: "short", timeStyle: "short" });
}

function sourceStatusTone(status: string): SourceStatusTone {
  if (["live", "passed", "research_only"].includes(status)) return "positive";
  if (["partial", "inputs_required", "research_enrichment", "diagnostic_only"].includes(status)) return "warning";
  if (["unavailable", "failed"].includes(status)) return "negative";
  return "neutral";
}

function sourceStatusLabel(status: string): string {
  if (status === "passed") return "Passed";
  return policyStatusLabel(status);
}

function venueSnapshotSourceRow(snapshot: LivePerpDexVenueSnapshot, layer: string, boundary: string): PerpDexSourceStatusRow {
  return {
    source: snapshot.venue_name,
    layer,
    status: snapshot.status,
    tone: sourceStatusTone(snapshot.status),
    rows: snapshot.markets.length ? `${snapshot.markets.length} rows` : "No rows",
    evidence: snapshot.normalization_status
      ? policyStatusLabel(snapshot.normalization_status)
      : snapshot.source.replaceAll("_", " "),
    boundary,
    lastCheck: formatSyncTime(snapshot.fetched_at),
  };
}

function buildPerpDexSourceStatusRows(
  snapshots: LivePerpDexVenueSnapshot[],
  coinglass: LivePerpDexVenueSnapshot,
  routePolicy: LivePerpDexRouteConstraints,
  routeModel: LivePerpDexRouteModel
): PerpDexSourceStatusRow[] {
  const normalizedSnapshots = snapshots.filter((snapshot) => snapshot.venue_id !== "gmx");
  const normalizedLive = normalizedSnapshots.filter((snapshot) => snapshot.status === "live" && snapshot.markets.length > 0).length;
  const normalizedRows = normalizedSnapshots.reduce((sum, snapshot) => sum + snapshot.markets.length, 0);
  const gmxSnapshot = snapshots.find((snapshot) => snapshot.venue_id === "gmx");

  const rows: PerpDexSourceStatusRow[] = [
    {
      source: "Direct Venues",
      layer: "Runtime snapshots",
      status: normalizedLive > 0 ? "live" : "unavailable",
      tone: normalizedLive > 0 ? "positive" : "negative",
      rows: `${normalizedRows} rows`,
      evidence: `${normalizedLive}/${normalizedSnapshots.length} normalized live`,
      boundary: "Read-only market context; no venue ranking",
      lastCheck: "Current render",
    },
    ...normalizedSnapshots.map((snapshot) =>
      venueSnapshotSourceRow(snapshot, "Direct public API", "Display-only venue rows; no execution path")
    ),
  ];

  if (gmxSnapshot) {
    rows.push(venueSnapshotSourceRow(gmxSnapshot, "Raw fixed-point API", "GMX diagnostics only; no liquidity ranking"));
  }

  rows.push(
    {
      source: "CoinGlass PerpDEX",
      layer: "Research enrichment",
      status: coinglass.markets.length > 0 ? "research_enrichment" : coinglass.status,
      tone: coinglass.markets.length > 0 ? "warning" : sourceStatusTone(coinglass.status),
      rows: coinglass.markets.length ? `${coinglass.markets.length} rows` : "No rows",
      evidence: coinglass.coverage_summary
        ? `${coinglass.coverage_summary.exchanges_with_matches}/${coinglass.coverage_summary.requested_exchanges.length} venues matched`
        : "No coverage summary",
      boundary: "Screening hints only; not route input",
      lastCheck: formatSyncTime(coinglass.fetched_at),
    },
    {
      source: "Route Policy",
      layer: "Backend contract",
      status: routePolicy.status,
      tone: sourceStatusTone(routePolicy.status),
      rows: `${routePolicy.capabilities.length} capabilities`,
      evidence: `${routePolicy.blockers.length} blockers`,
      boundary: routePolicy.ui_policy.may_rank_by_liquidity ? "Ranking unexpectedly enabled" : "Ranking and execution blocked",
      lastCheck: "Current render",
    },
    {
      source: "Route Model",
      layer: "Backend contract",
      status: routeModel.status,
      tone: sourceStatusTone(routeModel.status),
      rows: `${routeModel.venue_readiness.length} venue checks`,
      evidence: `${routeModel.required_inputs.length} required inputs`,
      boundary: routeModel.output_policy.may_estimate_cost_bps ? "Cost bps unexpectedly enabled" : "Numeric total bps blocked",
      lastCheck: "Current render",
    },
    {
      source: "Release Smoke",
      layer: "Preview runway",
      status: "passed",
      tone: "positive",
      rows: "health / policy / direct / CoinGlass",
      evidence: "release-smoke checklist passed",
      boundary: "Read-only safety gates confirmed",
      lastCheck: "2026-06-18",
    }
  );

  return rows;
}

function sourceStatusCells(row: PerpDexSourceStatusRow) {
  return [
    <span key="source" className="font-semibold text-cyan-200">
      {row.source}
    </span>,
    row.layer,
    <span key="status" className={toneText(row.tone)}>
      {sourceStatusLabel(row.status)}
    </span>,
    <span key="rows" className="font-mono text-slate-100">
      {row.rows}
    </span>,
    row.evidence,
    row.boundary,
    row.lastCheck,
  ];
}

function lastSyncTime(lastSync: Record<string, unknown> | null): string {
  return formatSyncTime(lastSync?.last_sync_at);
}

function formatMaybePrice(value: number | null): string {
  if (value === null) return "No data";
  return value >= 100 ? `$${formatNumber(value)}` : `$${value.toFixed(4)}`;
}

function formatMaybeBps(value: number | null | undefined): string {
  if (value === null || value === undefined) return "No data";
  return `${value.toFixed(3)} bps`;
}

function formatMaybeCompactCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return "No data";
  return formatCompactCurrency(value);
}

function formatMaybePercent(value: number | null, digits = 3): string {
  if (value === null) return "No data";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

function formatMaybeRatio(value: number | null | undefined): string {
  if (value === null || value === undefined) return "No data";
  return value.toFixed(3);
}

function percentTone(value: number | null) {
  if (value === null) return "warning";
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

function readinessTone(row: LiveMatrixRow) {
  const readyFields = [row.perpPrice, row.fundingPct, row.openInterestUsd, row.longAccountRatio].filter(
    (value) => value !== null
  ).length;

  if (readyFields >= 3) return "positive";
  if (readyFields >= 1) return "warning";
  return "negative";
}

function readinessLabel(row: LiveMatrixRow): string {
  const tone = readinessTone(row);
  if (tone === "positive") return "Ready";
  if (tone === "warning") return "Partial";
  return "Missing";
}

function perpUniverseCells(row: LiveMatrixRow) {
  const statusTone = readinessTone(row);

  return [
    <span key="asset" className="font-semibold text-white">
      {row.asset}
    </span>,
    <span key="perp" className="font-mono text-slate-100">
      {formatMaybePrice(row.perpPrice)}
    </span>,
    <span key="funding" className={toneText(percentTone(row.fundingPct))}>
      {formatMaybePercent(row.fundingPct)}
    </span>,
    <span key="oi" className="font-mono text-slate-100">
      {row.openInterestUsd === null ? "No data" : formatCompactCurrency(row.openInterestUsd)}
    </span>,
    <span key="basis" className={toneText(percentTone(row.basisPct))}>
      {formatMaybePercent(row.basisPct)}
    </span>,
    <span key="long" className={toneText(row.longAccountRatio === null ? "warning" : row.longAccountRatio >= 50 ? "positive" : "negative")}>
      {formatMaybePercent(row.longAccountRatio, 2)}
    </span>,
    <span key="status" className={toneText(statusTone)}>
      {readinessLabel(row)}
    </span>,
  ];
}

function opportunityCells(opportunity: LiveArbitrageOpportunity) {
  return [
    <span key="asset" className="font-semibold text-white">
      {opportunity.asset}
    </span>,
    opportunity.type.replaceAll("_", " "),
    opportunity.longLeg,
    opportunity.shortLeg,
    <span key="edge" className={toneText("positive")}>
      {formatMaybePercent(opportunity.edgePct)}
    </span>,
    <span key="funding" className={toneText(percentTone(opportunity.fundingPct))}>
      {formatMaybePercent(opportunity.fundingPct)}
    </span>,
    <span key="oi" className="font-mono text-slate-100">
      {opportunity.openInterestUsd === null ? "No data" : formatCompactCurrency(opportunity.openInterestUsd)}
    </span>,
    <span key="risk" className={toneText(opportunity.riskNote === "Data-backed" ? "positive" : "warning")}>
      {opportunity.riskNote}
    </span>,
  ];
}

function venueMarketMode(market: LivePerpDexVenueMarket): string {
  if (market.normalization_status === "raw_fixed_point") {
    if (market.token_amount_scale_status === "pool_amounts_scaled") return "Raw + Pool Units";
    return market.scale_validation_status === "token_decimals_resolved" ? "Raw + Decimals" : "Raw";
  }
  return "Normalized";
}

function venueMarketStatus(market: LivePerpDexVenueMarket): string {
  if (market.normalization_status === "raw_fixed_point") return "Raw";
  if (market.status === "live") return "Live";
  return "Partial";
}

function venueMarketCells(market: LivePerpDexVenueMarket) {
  const isRaw = market.normalization_status === "raw_fixed_point";

  return [
    <span key="venue" className="font-semibold text-cyan-200">
      {market.venue_name}
    </span>,
    <span key="market" className="font-semibold text-white">
      {market.market}
    </span>,
    <span key="mark" className="font-mono text-slate-100">
      {formatMaybePrice(market.mark_price ?? market.mid_price)}
    </span>,
    <span key="funding" className={toneText(percentTone(market.funding_pct))}>
      {formatMaybePercent(market.funding_pct, 4)}
    </span>,
    <span key="oi" className="font-mono text-slate-100">
      {market.open_interest_usd === null ? "No data" : formatCompactCurrency(market.open_interest_usd)}
    </span>,
    <span key="volume" className="font-mono text-slate-100">
      {market.volume_24h_usd === null ? "No data" : formatCompactCurrency(market.volume_24h_usd)}
    </span>,
    <span key="leverage" className="font-mono text-slate-100">
      {market.max_leverage ? `${market.max_leverage}x` : "No data"}
    </span>,
    <span key="mode" className={toneText(isRaw ? "warning" : "positive")}>
      {venueMarketMode(market)}
    </span>,
    <span key="status" className={toneText(market.status === "live" && !isRaw ? "positive" : "warning")}>
      {venueMarketStatus(market)}
    </span>,
  ];
}

function depthStatusTone(status?: string | null) {
  if (!status) return "warning";
  if (status.includes("missing") || status.includes("empty")) return "negative";
  return "warning";
}

function depthDiagnosticCells(market: LivePerpDexVenueMarket) {
  return [
    <span key="venue" className="font-semibold text-cyan-200">
      {market.venue_name}
    </span>,
    <span key="market" className="font-semibold text-white">
      {market.market}
    </span>,
    <span key="depth" className={toneText(depthStatusTone(market.orderbook_depth_status))}>
      {policyStatusLabel(market.orderbook_depth_status ?? "missing_depth")}
    </span>,
    <span key="bidask" className="font-mono text-slate-100">
      {formatMaybePrice(market.best_bid_price ?? null)} / {formatMaybePrice(market.best_ask_price ?? null)}
    </span>,
    <span key="spread" className="font-mono text-slate-100">
      {formatMaybeBps(market.top_of_book_spread_bps)}
    </span>,
    <span key="bid-depth" className="font-mono text-slate-100">
      {formatMaybeCompactCurrency(market.bid_depth_top_orders_usd)}
    </span>,
    <span key="ask-depth" className="font-mono text-slate-100">
      {formatMaybeCompactCurrency(market.ask_depth_top_orders_usd)}
    </span>,
    market.orderbook_depth_safe_use ?? "Display-only depth diagnostics",
  ];
}

function coinGlassMarketCells(market: LivePerpDexVenueMarket) {
  const liquidationUsd =
    market.liquidation_usd_24h ??
    (market.long_liquidation_usd_24h !== undefined &&
    market.long_liquidation_usd_24h !== null &&
    market.short_liquidation_usd_24h !== undefined &&
    market.short_liquidation_usd_24h !== null
      ? market.long_liquidation_usd_24h + market.short_liquidation_usd_24h
      : null);

  return [
    <span key="venue" className="font-semibold text-cyan-200">
      {market.venue_name}
    </span>,
    <span key="symbol" className="font-semibold text-white">
      {market.symbol}
    </span>,
    <span key="price" className="font-mono text-slate-100">
      {formatMaybePrice(market.mark_price)}
    </span>,
    <span key="funding" className={toneText(percentTone(market.funding_pct))}>
      {formatMaybePercent(market.funding_pct, 4)}
    </span>,
    <span key="oi" className="font-mono text-slate-100">
      {market.open_interest_usd === null ? "No data" : formatCompactCurrency(market.open_interest_usd)}
    </span>,
    <span key="ls" className="font-mono text-slate-100">
      {formatMaybeRatio(market.long_short_ratio_1h ?? market.long_short_ratio_24h)}
    </span>,
    <span key="liq" className="font-mono text-slate-100">
      {liquidationUsd === null ? "No data" : formatCompactCurrency(liquidationUsd)}
    </span>,
    <span key="status" className={toneText("warning")}>
      Research
    </span>,
  ];
}

function policyStatusLabel(status: string): string {
  if (status === "live") return "Live";
  if (status === "unavailable") return "Unavailable";
  if (status === "research_only") return "Research Only";
  if (status === "raw_fixed_point") return "Raw Fixed-point";
  if (status === "lighter_public_market_details") return "Lighter Public Data";
  if (status === "aster_public_futures_market_data") return "Aster Public Data";
  if (status === "coinglass_coin_market_enrichment") return "CoinGlass Enrichment";
  if (status === "partial_ready") return "Partial Ready";
  if (status === "partial_ready_display_only") return "Display Only";
  if (status === "partial_ready_top_orders_only") return "Top Orders Only";
  if (status === "partial_ready_depth_ladder_display_only") return "Depth Display Only";
  if (status === "partial_ready_one_sided_depth_ladder_display_only") return "One-sided Depth";
  if (status === "partial_ready_published_defaults_only") return "Published Defaults";
  if (status === "source_fields_available_unit_unconfirmed") return "Source Fields";
  if (status === "blocked_for_numeric_total") return "Numeric Total Blocked";
  if (status === "not_modeled") return "Not Modeled";
  if (status === "missing_depth") return "Missing Depth";
  if (status === "research_enrichment") return "Research Enrichment";
  if (status === "inputs_required") return "Inputs Required";
  if (status === "input_required") return "Input Required";
  if (status === "diagnostic_only") return "Diagnostic Only";
  if (status === "blocked") return "Blocked";
  if (status === "screening_ready") return "Screening Ready";
  if (status === "request_failed") return "Request Failed";
  if (status === "partial") return "Partial";
  if (status === "empty") return "Empty";
  if (status === "route_gate_only") return "Route Gate Only";
  if (status === "display_context_only") return "Display Context";
  if (status === "boundary_notice") return "Boundary Notice";
  if (status === "staleness_policy_required") return "Staleness Policy Required";
  if (status === "policy_input_required") return "Policy Input Required";
  if (status === "action_required") return "Action Required";
  if (status === "evidence_required") return "Evidence Required";
  if (status === "venue_evidence_required") return "Venue Evidence Required";
  if (status === "cross_venue_evidence_required") return "Cross-venue Evidence Required";
  if (status === "mapping_review_required") return "Mapping Review Required";
  if (status === "source_inputs_missing") return "Source Inputs Missing";
  if (status === "blocked_for_carry_conversion") return "Carry Conversion Blocked";
  if (status === "blocked_for_diagnostic_carry_bps") return "Diagnostic Carry Blocked";
  if (status === "manual_approval_required") return "Manual Approval Required";
  if (status === "source_relation_guardrail_added") return "Source Guardrail Added";
  if (status === "offline_guardrail_added") return "Offline Guardrail Added";
  if (status === "live_smoke_observed") return "Live Smoke Observed";
  if (status === "relation_ambiguous") return "Relation Ambiguous";
  if (status === "fixture_required") return "Fixture Required";
  return status;
}

function policyStatusTone(status: string) {
  if (status === "partial_ready" || status.startsWith("partial_ready") || status.startsWith("source_fields")) return "warning";
  if (
    status === "inputs_required" ||
    status === "input_required" ||
    status === "diagnostic_only" ||
    status === "research_enrichment" ||
    status === "route_gate_only" ||
    status === "display_context_only" ||
    status === "boundary_notice" ||
    status === "staleness_policy_required" ||
    status === "policy_input_required" ||
    status === "action_required" ||
    status === "evidence_required" ||
    status === "venue_evidence_required" ||
    status === "cross_venue_evidence_required" ||
    status === "mapping_review_required" ||
    status === "source_inputs_missing" ||
    status === "blocked_for_carry_conversion" ||
    status === "blocked_for_diagnostic_carry_bps" ||
    status === "manual_approval_required" ||
    status === "source_relation_guardrail_added" ||
    status === "offline_guardrail_added" ||
    status === "live_smoke_observed" ||
    status === "relation_ambiguous" ||
    status === "fixture_required"
  )
    return "warning";
  if (status === "blocked") return "negative";
  return "neutral";
}

function coverageStatusTone(status: string) {
  if (status === "screening_ready") return "positive";
  if (status === "request_failed") return "negative";
  return "warning";
}

function routeModelList(items: string[]): string {
  return items.length ? items.join(", ") : "None";
}

function routeModelValues(values?: Record<string, string | number | boolean>): string {
  if (!values) return "None";
  const entries = Object.entries(values);
  if (!entries.length) return "None";
  return entries.map(([key, value]) => `${key}: ${value}`).join(", ");
}

function routeDiagnosticVenueLabel(venueId: string): string {
  if (venueId === "lighter") return "Lighter";
  if (venueId === "aster") return "Aster";
  if (venueId === "all") return "Cross-venue";
  if (venueId === "unknown") return "Unknown";
  return venueId.replaceAll("_", " ");
}

function buildRouteDiagnosticVenueBreakdown(
  components: LivePerpDexRouteCostDiagnosticComponent[]
): LivePerpDexRouteCostDiagnosticVenueBreakdown[] {
  const groups = new Map<string, LivePerpDexRouteCostDiagnosticComponent[]>();
  components.forEach((component) => {
    const venueId = component.venue_id || "unknown";
    groups.set(venueId, [...(groups.get(venueId) ?? []), component]);
  });

  return Array.from(groups.entries()).map(([venueId, venueComponents]) => {
    const displayComponents = venueComponents.filter((component) => component.may_emit_component_bps);
    const blockedComponents = venueComponents.filter((component) => !component.may_emit_component_bps);
    const sourcedComponents = venueComponents.filter((component) => component.source_fields.length > 0);

    return {
      venue_id: venueId,
      venue_label: routeDiagnosticVenueLabel(venueId),
      component_count: venueComponents.length,
      display_only_component_count: displayComponents.length,
      blocked_numeric_component_count: blockedComponents.length,
      sourced_component_count: sourcedComponents.length,
      component_ids: venueComponents.map((component) => component.id),
      display_component_ids: displayComponents.map((component) => component.id),
      blocked_numeric_component_ids: blockedComponents.map((component) => component.id),
      sourced_component_ids: sourcedComponents.map((component) => component.id),
      numeric_total_status: "blocked",
      safe_use: "Venue-level component readiness only; do not rank routes or estimate executable cost",
    };
  });
}

function buildRouteDiagnosticBlockerBreakdown(
  components: LivePerpDexRouteCostDiagnosticComponent[]
): LivePerpDexRouteCostDiagnosticBlockerBreakdown[] {
  const groups = new Map<string, LivePerpDexRouteCostDiagnosticComponent[]>();
  components.forEach((component) => {
    component.blocked_by.forEach((blocker) => {
      groups.set(blocker, [...(groups.get(blocker) ?? []), component]);
    });
  });

  return Array.from(groups.entries()).map(([blocker, blockerComponents]) => {
    const venueIds: string[] = [];
    blockerComponents.forEach((component) => {
      const venueId = component.venue_id || "unknown";
      if (!venueIds.includes(venueId)) venueIds.push(venueId);
    });
    const displayComponents = blockerComponents.filter((component) => component.may_emit_component_bps);
    const blockedComponents = blockerComponents.filter((component) => !component.may_emit_component_bps);

    return {
      blocker,
      component_count: blockerComponents.length,
      component_ids: blockerComponents.map((component) => component.id),
      venue_ids: venueIds,
      display_component_ids: displayComponents.map((component) => component.id),
      blocked_numeric_component_ids: blockedComponents.map((component) => component.id),
      numeric_total_status: "blocked",
      safe_use: "Blocker visibility only; source required inputs before estimating route cost",
    };
  });
}

function buildRouteDiagnosticRequiredInputBreakdown(
  requiredInputs: LivePerpDexRouteModelRequiredInput[],
  components: LivePerpDexRouteCostDiagnosticComponent[]
): LivePerpDexRouteCostDiagnosticRequiredInputBreakdown[] {
  const groups = new Map<string, LivePerpDexRouteCostDiagnosticComponent[]>();
  components.forEach((component) => {
    (component.required_input_ids ?? []).forEach((inputId) => {
      groups.set(inputId, [...(groups.get(inputId) ?? []), component]);
    });
  });
  const nextActions: Record<string, string> = {
    venue_fee_schedule: "Confirm venue fee units, account tier and maker/taker side before fee bps can be calculated",
    order_intent: "Define side, notional, size unit and intent before applying fee, depth or carry diagnostics",
    depth_or_impact_model: "Source order-size-aware depth aggregation, liquidity caps and slippage math before impact bps",
    carry_horizon: "Define holding period, position notional and rate sign convention before carry bps",
    risk_limits: "Define max notional, leverage, liquidation buffer and kill-switch gates before route allowance",
  };

  return requiredInputs.map((input) => {
    const inputComponents = groups.get(input.id) ?? [];
    const displayComponents = inputComponents.filter((component) => component.may_emit_component_bps);
    const blockedComponents = inputComponents.filter((component) => !component.may_emit_component_bps);
    const sourcedComponents = inputComponents.filter((component) => component.source_fields.length > 0);
    const venueIds: string[] = [];
    inputComponents.forEach((component) => {
      const venueId = component.venue_id || "unknown";
      if (!venueIds.includes(venueId)) venueIds.push(venueId);
    });

    return {
      input_id: input.id,
      input_label: input.label,
      status: inputComponents.length === 0 ? "route_gate_only" : sourcedComponents.length > 0 ? "partial_ready_display_only" : "input_required",
      reason: input.reason,
      component_count: inputComponents.length,
      component_ids: inputComponents.map((component) => component.id),
      venue_ids: venueIds,
      display_component_ids: displayComponents.map((component) => component.id),
      blocked_numeric_component_ids: blockedComponents.map((component) => component.id),
      sourced_component_ids: sourcedComponents.map((component) => component.id),
      numeric_total_status: "blocked",
      safe_use: "Required-input readiness only; do not estimate route cost or rank venues",
      next_action: nextActions[input.id] ?? "Source this required input before numeric route cost",
    };
  });
}

function buildRouteDiagnosticSourceFieldBreakdown(
  components: LivePerpDexRouteCostDiagnosticComponent[]
): LivePerpDexRouteCostDiagnosticSourceFieldBreakdown[] {
  const groups = new Map<string, LivePerpDexRouteCostDiagnosticComponent[]>();
  components.forEach((component) => {
    component.source_fields.forEach((sourceField) => {
      groups.set(sourceField, [...(groups.get(sourceField) ?? []), component]);
    });
  });

  return Array.from(groups.entries()).map(([sourceField, fieldComponents]) => {
    const venueIds: string[] = [];
    const requiredInputIds: string[] = [];
    fieldComponents.forEach((component) => {
      const venueId = component.venue_id || "unknown";
      if (!venueIds.includes(venueId)) venueIds.push(venueId);
      (component.required_input_ids ?? []).forEach((inputId) => {
        if (!requiredInputIds.includes(inputId)) requiredInputIds.push(inputId);
      });
    });
    const displayComponents = fieldComponents.filter((component) => component.may_emit_component_bps);
    const blockedComponents = fieldComponents.filter((component) => !component.may_emit_component_bps);

    return {
      source_field: sourceField,
      status: "display_context_only",
      component_count: fieldComponents.length,
      component_ids: fieldComponents.map((component) => component.id),
      venue_ids: venueIds,
      required_input_ids: requiredInputIds,
      display_component_ids: displayComponents.map((component) => component.id),
      blocked_numeric_component_ids: blockedComponents.map((component) => component.id),
      numeric_total_status: "blocked",
      safe_use: "Source-field visibility only; do not treat sourced display fields as route-cost inputs",
    };
  });
}

function buildRouteDiagnosticSafeUseBreakdown(
  components: LivePerpDexRouteCostDiagnosticComponent[]
): LivePerpDexRouteCostDiagnosticSafeUseBreakdown[] {
  const groups = new Map<string, LivePerpDexRouteCostDiagnosticComponent[]>();
  components.forEach((component) => {
    groups.set(component.safe_use, [...(groups.get(component.safe_use) ?? []), component]);
  });

  return Array.from(groups.entries()).map(([safeUse, safeUseComponents]) => {
    const venueIds: string[] = [];
    const requiredInputIds: string[] = [];
    safeUseComponents.forEach((component) => {
      const venueId = component.venue_id || "unknown";
      if (!venueIds.includes(venueId)) venueIds.push(venueId);
      (component.required_input_ids ?? []).forEach((inputId) => {
        if (!requiredInputIds.includes(inputId)) requiredInputIds.push(inputId);
      });
    });
    const displayComponents = safeUseComponents.filter((component) => component.may_emit_component_bps);
    const blockedComponents = safeUseComponents.filter((component) => !component.may_emit_component_bps);

    return {
      safe_use: safeUse,
      status: "boundary_notice",
      component_count: safeUseComponents.length,
      component_ids: safeUseComponents.map((component) => component.id),
      venue_ids: venueIds,
      required_input_ids: requiredInputIds,
      display_component_ids: displayComponents.map((component) => component.id),
      blocked_numeric_component_ids: blockedComponents.map((component) => component.id),
      numeric_total_status: "blocked",
      next_action: "Keep this boundary visible until required route-cost inputs are sourced and tested",
    };
  });
}

function buildRouteDiagnosticReadinessRollup(
  components: LivePerpDexRouteCostDiagnosticComponent[]
): LivePerpDexRouteCostDiagnosticReadinessRollup[] {
  const definitions = [
    {
      category_id: "fees",
      category_label: "Fees",
      required_input_ids: ["venue_fee_schedule", "order_intent"],
      component_ids: ["lighter_fee_fields", "aster_published_fee_schedule"],
      next_action: "Confirm fee units, account tier and maker/taker side before fee bps",
    },
    {
      category_id: "depth_slippage",
      category_label: "Depth / Slippage",
      required_input_ids: ["order_intent", "depth_or_impact_model"],
      component_ids: [
        "lighter_top_order_depth",
        "aster_top_of_book_spread",
        "aster_depth_ladder",
        "slippage_price_impact",
      ],
      next_action: "Source order-size-aware depth aggregation, liquidity caps and stale-depth policy before slippage bps",
    },
    {
      category_id: "carry",
      category_label: "Carry",
      required_input_ids: ["order_intent", "carry_horizon"],
      component_ids: ["funding_borrow_carry"],
      next_action: "Define holding period, notional and rate sign convention before carry bps",
    },
    {
      category_id: "risk_limits",
      category_label: "Risk Limits",
      required_input_ids: ["risk_limits"],
      component_ids: [],
      next_action: "Source risk gates before route allowance or execution boundary changes",
    },
  ];

  return definitions.map((definition) => {
    const rollupComponents = components.filter((component) => definition.component_ids.includes(component.id));
    const displayComponents = rollupComponents.filter((component) => component.may_emit_component_bps);
    const blockedComponents = rollupComponents.filter((component) => !component.may_emit_component_bps);
    const sourcedComponents = rollupComponents.filter((component) => component.source_fields.length > 0);

    return {
      category_id: definition.category_id,
      category_label: definition.category_label,
      status: rollupComponents.length === 0 ? "route_gate_only" : sourcedComponents.length > 0 ? "partial_ready_display_only" : "input_required",
      required_input_ids: definition.required_input_ids,
      component_count: rollupComponents.length,
      sourced_component_count: sourcedComponents.length,
      display_component_ids: displayComponents.map((component) => component.id),
      blocked_numeric_component_ids: blockedComponents.map((component) => component.id),
      numeric_total_status: "blocked",
      safe_use: "Compact readiness only; do not rank venues, estimate route cost or submit orders",
      next_action: definition.next_action,
    };
  });
}

function buildRouteDiagnosticDepthPolicyChecklist(
  components: LivePerpDexRouteCostDiagnosticComponent[]
): LivePerpDexRouteCostDiagnosticDepthPolicyChecklist[] {
  const componentsById = new Map(components.map((component) => [component.id, component]));
  const requiredPolicyInputs = [
    "depth_snapshot_timestamp",
    "max_depth_age_ms",
    "stale_depth_action",
    "order_size_usd",
    "side",
    "depth_aggregation_policy",
    "liquidity_cap",
  ];
  const definitions = [
    {
      policy_id: "lighter_top_order_depth_staleness",
      venue_id: "lighter",
      venue_label: "Lighter",
      component_id: "lighter_top_order_depth",
      depth_scope: "top resting orders",
      source_endpoint: "orderBookOrders",
      next_action: "Add timestamp freshness, stale-depth policy and order-size aggregation before Lighter slippage bps",
    },
    {
      policy_id: "aster_top_of_book_staleness",
      venue_id: "aster",
      venue_label: "Aster",
      component_id: "aster_top_of_book_spread",
      depth_scope: "top-of-book ticker",
      source_endpoint: "ticker/bookTicker",
      next_action: "Add freshness policy and depth-source precedence before Aster top-of-book can inform slippage",
    },
    {
      policy_id: "aster_depth_ladder_staleness",
      venue_id: "aster",
      venue_label: "Aster",
      component_id: "aster_depth_ladder",
      depth_scope: "public depth ladder",
      source_endpoint: "fapi/v3/depth",
      next_action: "Add timestamp freshness, stale-depth policy and order-size ladder aggregation before Aster slippage bps",
    },
  ];

  return definitions.map((definition) => {
    const component = componentsById.get(definition.component_id);

    return {
      ...definition,
      status: "staleness_policy_required",
      source_fields: component?.source_fields ?? [],
      required_policy_inputs: requiredPolicyInputs,
      blocked_by: ["no_depth_snapshot_timestamp", "no_max_depth_age_ms", "no_stale_depth_action", "no_order_size_context"],
      may_emit_slippage_bps: false,
      numeric_total_status: "blocked",
      safe_use: "Depth/staleness policy checklist only; do not estimate slippage, route cost or ranking",
    };
  });
}

function buildRouteDiagnosticNextActionBreakdown(
  requiredInputBreakdown: LivePerpDexRouteCostDiagnosticRequiredInputBreakdown[],
  readinessRollup: LivePerpDexRouteCostDiagnosticReadinessRollup[],
  depthPolicyChecklist: LivePerpDexRouteCostDiagnosticDepthPolicyChecklist[]
): LivePerpDexRouteCostDiagnosticNextActionBreakdown[] {
  const groups = new Map<string, LivePerpDexRouteCostDiagnosticNextActionBreakdown>();
  const appendUnique = (items: string[], value: string) => {
    if (value && !items.includes(value)) items.push(value);
  };
  const appendMany = (items: string[], values: string[]) => {
    values.forEach((value) => appendUnique(items, value));
  };
  const source = (nextAction: string, sourceType: string, sourceId: string) => {
    const current =
      groups.get(nextAction) ??
      {
        action_id: `next_action_${groups.size + 1}`,
        next_action: nextAction,
        status: "action_required",
        source_count: 0,
        source_types: [],
        source_ids: [],
        required_input_ids: [],
        required_policy_inputs: [],
        component_ids: [],
        venue_ids: [],
        policy_ids: [],
        rollup_category_ids: [],
        numeric_total_status: "blocked",
        safe_use: "Next-action planning only; do not estimate route cost, rank routes or submit orders",
      };
    current.source_count += 1;
    appendUnique(current.source_types, sourceType);
    appendUnique(current.source_ids, sourceId);
    groups.set(nextAction, current);
    return current;
  };

  requiredInputBreakdown.forEach((item) => {
    const group = source(item.next_action, "required_input", item.input_id);
    appendUnique(group.required_input_ids, item.input_id);
    appendMany(group.component_ids, item.component_ids);
    appendMany(group.venue_ids, item.venue_ids);
  });
  readinessRollup.forEach((item) => {
    const group = source(item.next_action, "readiness_rollup", item.category_id);
    appendMany(group.required_input_ids, item.required_input_ids);
    appendMany(group.component_ids, [...item.display_component_ids, ...item.blocked_numeric_component_ids]);
    appendUnique(group.rollup_category_ids, item.category_id);
  });
  depthPolicyChecklist.forEach((item) => {
    const group = source(item.next_action, "depth_staleness_policy", item.policy_id);
    appendMany(group.required_policy_inputs, item.required_policy_inputs);
    appendUnique(group.component_ids, item.component_id);
    appendUnique(group.venue_ids, item.venue_id);
    appendUnique(group.policy_ids, item.policy_id);
  });

  return Array.from(groups.values());
}

function buildRouteDiagnosticRequiredPolicyInputBreakdown(
  depthPolicyChecklist: LivePerpDexRouteCostDiagnosticDepthPolicyChecklist[]
): LivePerpDexRouteCostDiagnosticRequiredPolicyInputBreakdown[] {
  const requiredPolicyInputs = [
    "depth_snapshot_timestamp",
    "max_depth_age_ms",
    "stale_depth_action",
    "order_size_usd",
    "side",
    "depth_aggregation_policy",
    "liquidity_cap",
  ];
  const nextActions: Record<string, string> = {
    depth_snapshot_timestamp: "Source per-venue depth snapshot timestamps before freshness checks",
    max_depth_age_ms: "Define maximum allowed depth age by venue and endpoint before stale-depth handling",
    stale_depth_action: "Define whether stale depth is hidden, warned or blocks slippage diagnostics",
    order_size_usd: "Define order notional before depth aggregation can be evaluated",
    side: "Define buy/sell side before choosing bid or ask depth",
    depth_aggregation_policy: "Define order-size-aware depth aggregation before slippage diagnostics",
    liquidity_cap: "Define liquidity caps before any depth-derived route signal",
  };
  const appendUnique = (items: string[], value: string) => {
    if (value && !items.includes(value)) items.push(value);
  };

  return requiredPolicyInputs.map((inputId) => {
    const policies = depthPolicyChecklist.filter((policy) => policy.required_policy_inputs.includes(inputId));
    const policyIds: string[] = [];
    const componentIds: string[] = [];
    const venueIds: string[] = [];
    const sourceEndpoints: string[] = [];
    const blockedBy: string[] = [];
    policies.forEach((policy) => {
      appendUnique(policyIds, policy.policy_id);
      appendUnique(componentIds, policy.component_id);
      appendUnique(venueIds, policy.venue_id);
      appendUnique(sourceEndpoints, policy.source_endpoint);
      policy.blocked_by.forEach((blocker) => appendUnique(blockedBy, blocker));
    });

    return {
      input_id: inputId,
      input_label: inputId.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()),
      status: "policy_input_required",
      policy_count: policies.length,
      policy_ids: policyIds,
      component_ids: componentIds,
      venue_ids: venueIds,
      source_endpoints: sourceEndpoints,
      blocked_by: blockedBy,
      may_emit_slippage_bps: false,
      numeric_total_status: "blocked",
      safe_use: "Policy-input readiness only; do not estimate slippage, route cost or ranking",
      next_action: nextActions[inputId] ?? "Source this policy input before slippage diagnostics",
    };
  });
}

function buildRouteDiagnosticSourceInputActionCoverage(
  sourceFieldBreakdown: LivePerpDexRouteCostDiagnosticSourceFieldBreakdown[],
  nextActionBreakdown: LivePerpDexRouteCostDiagnosticNextActionBreakdown[]
): LivePerpDexRouteCostDiagnosticSourceInputActionCoverage[] {
  const appendUnique = (items: string[], value: string) => {
    if (value && !items.includes(value)) items.push(value);
  };
  const appendMany = (items: string[], values: string[]) => {
    values.forEach((value) => appendUnique(items, value));
  };

  return sourceFieldBreakdown.map((field, index) => {
    const matchedActions = nextActionBreakdown.filter((action) =>
      action.required_input_ids.some((inputId) => field.required_input_ids.includes(inputId)) ||
      action.component_ids.some((componentId) => field.component_ids.includes(componentId))
    );
    const nextActionIds: string[] = [];
    const nextActions: string[] = [];
    const sourceTypes: string[] = [];
    matchedActions.forEach((action) => {
      appendUnique(nextActionIds, action.action_id);
      appendUnique(nextActions, action.next_action);
      appendMany(sourceTypes, action.source_types);
    });

    return {
      coverage_id: `source_field_${index + 1}`,
      source_field: field.source_field,
      status: "display_context_only",
      component_count: field.component_count,
      component_ids: field.component_ids,
      venue_ids: field.venue_ids,
      required_input_count: field.required_input_ids.length,
      required_input_ids: field.required_input_ids,
      next_action_count: nextActions.length,
      next_action_ids: nextActionIds,
      next_actions: nextActions,
      source_types: sourceTypes,
      display_component_ids: field.display_component_ids,
      blocked_numeric_component_ids: field.blocked_numeric_component_ids,
      numeric_total_status: "blocked",
      safe_use: "Source-input-action coverage only; display source fields do not close route-ready inputs or ranking",
      next_action: "Complete mapped next actions before treating this source field as route-ready input",
    };
  });
}

function buildRouteDiagnosticRouteReadyEvidenceChecklist(
  sourceFieldBreakdown: LivePerpDexRouteCostDiagnosticSourceFieldBreakdown[],
  depthPolicyChecklist: LivePerpDexRouteCostDiagnosticDepthPolicyChecklist[]
): LivePerpDexRouteCostDiagnosticRouteReadyEvidenceChecklist[] {
  const depthPolicyIds = depthPolicyChecklist.map((policy) => policy.policy_id);
  const sourceFieldsForComponents = (componentIds: string[]) => {
    const sourceFields: string[] = [];
    sourceFieldBreakdown.forEach((field) => {
      if (!field.component_ids.some((componentId) => componentIds.includes(componentId))) return;
      if (!sourceFields.includes(field.source_field)) sourceFields.push(field.source_field);
    });
    return sourceFields;
  };
  const definitions = [
    {
      gate_id: "fee_schedule_evidence",
      gate_label: "Fee Schedule Evidence",
      required_input_ids: ["venue_fee_schedule"],
      required_policy_inputs: [],
      component_ids: ["lighter_fee_fields", "aster_published_fee_schedule"],
      policy_ids: [],
      blocked_outputs: ["fee_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"],
      next_action: "Confirm account fee tier, fee units and maker/taker side before fee bps",
    },
    {
      gate_id: "order_intent_evidence",
      gate_label: "Order Intent Evidence",
      required_input_ids: ["order_intent"],
      required_policy_inputs: ["order_size_usd", "side"],
      component_ids: [
        "lighter_fee_fields",
        "lighter_top_order_depth",
        "aster_top_of_book_spread",
        "aster_depth_ladder",
        "slippage_price_impact",
        "funding_borrow_carry",
      ],
      policy_ids: depthPolicyIds,
      blocked_outputs: ["fee_bps", "slippage_bps", "carry_bps", "estimated_cost_bps", "route_allowed"],
      next_action: "Define order size, side, notional and intent before route-cost evidence can be evaluated",
    },
    {
      gate_id: "depth_freshness_evidence",
      gate_label: "Depth Freshness Evidence",
      required_input_ids: ["depth_or_impact_model"],
      required_policy_inputs: ["depth_snapshot_timestamp", "max_depth_age_ms", "stale_depth_action"],
      component_ids: ["lighter_top_order_depth", "aster_top_of_book_spread", "aster_depth_ladder"],
      policy_ids: depthPolicyIds,
      blocked_outputs: ["slippage_bps", "estimated_cost_bps", "route_allowed"],
      next_action: "Source depth timestamps, maximum age policy and stale-depth handling before slippage bps",
    },
    {
      gate_id: "depth_aggregation_evidence",
      gate_label: "Depth Aggregation Evidence",
      required_input_ids: ["depth_or_impact_model"],
      required_policy_inputs: ["order_size_usd", "side", "depth_aggregation_policy", "liquidity_cap"],
      component_ids: [
        "lighter_top_order_depth",
        "aster_top_of_book_spread",
        "aster_depth_ladder",
        "slippage_price_impact",
      ],
      policy_ids: depthPolicyIds,
      blocked_outputs: ["slippage_bps", "estimated_cost_bps", "route_allowed"],
      next_action: "Define order-size-aware aggregation, side selection and liquidity caps before slippage bps",
    },
    {
      gate_id: "carry_semantics_evidence",
      gate_label: "Carry Semantics Evidence",
      required_input_ids: ["carry_horizon"],
      required_policy_inputs: [],
      component_ids: ["funding_borrow_carry"],
      policy_ids: [],
      blocked_outputs: ["carry_bps", "estimated_cost_bps", "net_edge_bps"],
      next_action: "Define holding period, notional and funding/borrowing sign convention before carry bps",
    },
    {
      gate_id: "risk_limits_evidence",
      gate_label: "Risk Limits Evidence",
      required_input_ids: ["risk_limits"],
      required_policy_inputs: [],
      component_ids: [],
      policy_ids: [],
      blocked_outputs: ["route_allowed", "may_submit_orders"],
      next_action: "Source risk gates before route allowance or execution boundary changes",
    },
  ];

  return definitions.map((definition) => {
    const sourceFieldIds = sourceFieldsForComponents(definition.component_ids);
    return {
      ...definition,
      status: "evidence_required",
      source_field_ids: sourceFieldIds,
      evidence_count: sourceFieldIds.length,
      numeric_total_status: "blocked",
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: "Route-ready evidence checklist only; do not estimate route cost, rank routes or submit orders",
    };
  });
}

function buildRouteDiagnosticVenueEvidenceStatus(
  routeReadyEvidenceChecklist: LivePerpDexRouteCostDiagnosticRouteReadyEvidenceChecklist[],
  sourceFieldBreakdown: LivePerpDexRouteCostDiagnosticSourceFieldBreakdown[],
  gmxRateSemantics?: LivePerpDexGmxRateSemantics
): LivePerpDexRouteCostDiagnosticVenueEvidenceStatus[] {
  const evidenceByGate = new Map(routeReadyEvidenceChecklist.map((gate) => [gate.gate_id, gate]));
  const appendUnique = (items: string[], value: string) => {
    if (value && !items.includes(value)) items.push(value);
  };
  const appendMany = (items: string[], values: string[]) => {
    values.forEach((value) => appendUnique(items, value));
  };
  const evidenceValues = (gateIds: string[], key: keyof LivePerpDexRouteCostDiagnosticRouteReadyEvidenceChecklist) => {
    const values: string[] = [];
    gateIds.forEach((gateId) => {
      const gate = evidenceByGate.get(gateId);
      const gateValues = gate?.[key];
      if (Array.isArray(gateValues)) appendMany(values, gateValues);
    });
    return values;
  };
  const sourceFieldsForComponents = (componentIds: string[]) => {
    const sourceFields: string[] = [];
    sourceFieldBreakdown.forEach((field) => {
      if (!field.component_ids.some((componentId) => componentIds.includes(componentId))) return;
      appendUnique(sourceFields, field.source_field);
    });
    return sourceFields;
  };
  const gmxMappingReview = gmxRateSemantics?.mapping_review;
  const gmxDiagnosticFieldIds = gmxMappingReview?.diagnostic_fields ?? [
    "rate_semantics_status",
    "rate_relation_diagnostics",
    "rate_relation_summary",
    "rate_source_fields_status",
    "rate_source_fields_summary",
  ];
  const gmxFixtureCoverageIds = gmxRateSemantics?.fixture_coverage?.map((item) => item.id) ?? [
    "net_rate_relation_raw_fields",
    "live_nonzero_borrowing_raw_sum_relation_observed",
    "live_zero_borrowing_relation_ambiguity",
    "live_shape_offline_fixture",
  ];
  const definitions = [
    {
      venue_id: "lighter",
      venue_label: "Lighter",
      venue_scope: "direct_venue",
      status: "venue_evidence_required",
      venue_gate_ids: [
        "fee_schedule_evidence",
        "order_intent_evidence",
        "depth_freshness_evidence",
        "depth_aggregation_evidence",
      ],
      cross_venue_gate_ids: ["carry_semantics_evidence", "risk_limits_evidence"],
      component_ids: ["lighter_fee_fields", "lighter_top_order_depth"],
      policy_ids: ["lighter_top_order_depth_staleness"],
      diagnostic_field_ids: [],
      fixture_coverage_ids: [],
      next_action: "Source Lighter account fee tier, order intent and depth policy before route-ready Lighter costing",
    },
    {
      venue_id: "aster",
      venue_label: "Aster",
      venue_scope: "direct_venue",
      status: "venue_evidence_required",
      venue_gate_ids: [
        "fee_schedule_evidence",
        "order_intent_evidence",
        "depth_freshness_evidence",
        "depth_aggregation_evidence",
      ],
      cross_venue_gate_ids: ["carry_semantics_evidence", "risk_limits_evidence"],
      component_ids: ["aster_published_fee_schedule", "aster_top_of_book_spread", "aster_depth_ladder"],
      policy_ids: ["aster_top_of_book_staleness", "aster_depth_ladder_staleness"],
      diagnostic_field_ids: [],
      fixture_coverage_ids: [],
      next_action: "Source Aster account fee tier, order intent, depth aggregation and stale-depth policy before route-ready Aster costing",
    },
    {
      venue_id: "gmx",
      venue_label: "GMX",
      venue_scope: "raw_mapping_review",
      status: "mapping_review_required",
      venue_gate_ids: ["gmx_rate_mapping_review"],
      cross_venue_gate_ids: ["order_intent_evidence", "carry_semantics_evidence", "risk_limits_evidence"],
      component_ids: [],
      policy_ids: [],
      diagnostic_field_ids: gmxDiagnosticFieldIds,
      fixture_coverage_ids: gmxFixtureCoverageIds,
      next_action: gmxRateSemantics?.next_action ?? "Map live GMX rate semantics before carry bps",
    },
    {
      venue_id: "cross_venue",
      venue_label: "Cross-venue",
      venue_scope: "cross_venue",
      status: "cross_venue_evidence_required",
      venue_gate_ids: ["carry_semantics_evidence", "risk_limits_evidence"],
      cross_venue_gate_ids: [],
      component_ids: ["funding_borrow_carry"],
      policy_ids: [],
      diagnostic_field_ids: [],
      fixture_coverage_ids: [],
      next_action: "Define carry horizon, risk limits and execution boundary before any route allowance",
    },
  ];

  return definitions.map((definition) => {
    const gateIds = [...definition.venue_gate_ids, ...definition.cross_venue_gate_ids];
    const requiredInputIds = evidenceValues(gateIds, "required_input_ids");
    const requiredPolicyInputs = evidenceValues(gateIds, "required_policy_inputs");
    const blockedOutputs = evidenceValues(gateIds, "blocked_outputs");
    const sourceFieldIds = sourceFieldsForComponents(definition.component_ids);
    if (definition.venue_id === "gmx") {
      appendMany(requiredInputIds, ["order_intent", "carry_horizon", "risk_limits"]);
      appendMany(blockedOutputs, ["carry_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"]);
    }
    return {
      ...definition,
      required_input_ids: requiredInputIds,
      required_policy_inputs: requiredPolicyInputs,
      source_field_ids: sourceFieldIds,
      blocked_outputs: blockedOutputs,
      evidence_count: sourceFieldIds.length + definition.diagnostic_field_ids.length + definition.fixture_coverage_ids.length,
      numeric_total_status: "blocked",
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: "Venue evidence status only; do not estimate route cost, rank routes or submit orders",
    };
  });
}

function buildGmxRateMappingReview(
  gmxRateSemantics?: LivePerpDexGmxRateSemantics
): LivePerpDexGmxRateMappingReview | null {
  if (!gmxRateSemantics) return null;
  const mappingReview = gmxRateSemantics.mapping_review;
  const diagnosticFieldIds = mappingReview?.diagnostic_fields ?? [
    "rate_semantics_status",
    "rate_relation_diagnostics",
    "rate_relation_summary",
    "rate_source_fields_status",
    "rate_source_fields_summary",
  ];
  const sourceInputsRequired = mappingReview?.source_inputs_required ?? [
    "fundingFactorPerSecond",
    "borrowingFactorPerSecondForLongs",
    "borrowingFactorPerSecondForShorts",
    "longsPayShorts",
  ];
  const fixtureCoverageIds = gmxRateSemantics.fixture_coverage?.map((item) => item.id) ?? [];
  const blockedBy = gmxRateSemantics.blocked_for_numeric_carry ?? [];
  const blockedOutputs = ["carry_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"];
  const safeUse = "GMX rate mapping review only; no percent, bps, annualized or carry-cost conversion";
  const sideAwareFixtureExpectations: LivePerpDexGmxRateSideAwareFixtureExpectation[] = [
    {
      expectation_id: "long_position_pays_when_longs_pay_shorts_true",
      case_id: "longs_pay_shorts_direction",
      case_label: "Long pays when longsPayShorts=true",
      status: "fixture_required",
      position_side: "long",
      longs_pay_shorts: true,
      expected_funding_direction: "pay",
      required_source_inputs: ["fundingFactorPerSecond", "longsPayShorts"],
      fixture_coverage_ids: [],
      blocked_by: ["side-aware funding sign tests", "live /markets/info source helper inputs unavailable"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      safe_use: safeUse,
      next_action: "Add fixture where long side pays funding when longsPayShorts is true",
    },
    {
      expectation_id: "short_position_receives_when_longs_pay_shorts_true",
      case_id: "longs_pay_shorts_direction",
      case_label: "Short receives when longsPayShorts=true",
      status: "fixture_required",
      position_side: "short",
      longs_pay_shorts: true,
      expected_funding_direction: "receive",
      required_source_inputs: ["fundingFactorPerSecond", "longsPayShorts"],
      fixture_coverage_ids: [],
      blocked_by: ["side-aware funding sign tests", "live /markets/info source helper inputs unavailable"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      safe_use: safeUse,
      next_action: "Add fixture where short side receives funding when longsPayShorts is true",
    },
    {
      expectation_id: "short_position_pays_when_longs_pay_shorts_false",
      case_id: "longs_pay_shorts_direction",
      case_label: "Short pays when longsPayShorts=false",
      status: "fixture_required",
      position_side: "short",
      longs_pay_shorts: false,
      expected_funding_direction: "pay",
      required_source_inputs: ["fundingFactorPerSecond", "longsPayShorts"],
      fixture_coverage_ids: [],
      blocked_by: ["side-aware funding sign tests", "live /markets/info source helper inputs unavailable"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      safe_use: safeUse,
      next_action: "Add fixture where short side pays funding when longsPayShorts is false",
    },
    {
      expectation_id: "long_position_receives_when_longs_pay_shorts_false",
      case_id: "longs_pay_shorts_direction",
      case_label: "Long receives when longsPayShorts=false",
      status: "fixture_required",
      position_side: "long",
      longs_pay_shorts: false,
      expected_funding_direction: "receive",
      required_source_inputs: ["fundingFactorPerSecond", "longsPayShorts"],
      fixture_coverage_ids: [],
      blocked_by: ["side-aware funding sign tests", "live /markets/info source helper inputs unavailable"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      safe_use: safeUse,
      next_action: "Add fixture where long side receives funding when longsPayShorts is false",
    },
  ];
  const sideAwareExpectationIds = sideAwareFixtureExpectations.map((item) => item.expectation_id);
  const reviewItems: LivePerpDexGmxRateMappingReviewItem[] = [
    {
      review_id: "source_relation_guardrail",
      review_label: "Source Relation Guardrail",
      status: "source_relation_guardrail_added",
      evidence_count: mappingReview?.source_confirmed?.length ?? 0,
      diagnostic_field_ids: ["rate_relation_summary"],
      source_inputs_required: [],
      fixture_coverage_ids: ["net_rate_relation_raw_fields"],
      blocked_by: ["live /markets/info nonzero borrowing rate mapping review"],
      blocked_outputs: blockedOutputs,
      safe_use: safeUse,
      next_action: "Keep source relation guardrail while mapping live /markets/info fields",
    },
    {
      review_id: "live_nonzero_borrowing_mapping",
      review_label: "Live Nonzero Borrowing Mapping",
      status: "mapping_review_required",
      evidence_count: mappingReview?.live_observed?.length ?? 0,
      diagnostic_field_ids: ["rate_relation_summary", "rate_relation_diagnostics"],
      source_inputs_required: sourceInputsRequired,
      fixture_coverage_ids: [
        "live_nonzero_borrowing_raw_sum_relation_observed",
        "live_zero_borrowing_relation_ambiguity",
        "live_shape_offline_fixture",
      ],
      blocked_by: [
        "live /markets/info nonzero borrowing rate mapping review",
        "broader live fixture coverage across market states",
      ],
      blocked_outputs: blockedOutputs,
      safe_use: safeUse,
      next_action: "Reconcile live funding+borrowing observation with source helper relation before carry bps",
    },
    {
      review_id: "source_helper_inputs",
      review_label: "Source Helper Inputs",
      status: "source_inputs_missing",
      evidence_count: 0,
      diagnostic_field_ids: ["rate_source_fields_status", "rate_source_fields_summary"],
      source_inputs_required: sourceInputsRequired,
      fixture_coverage_ids: [],
      blocked_by: ["live /markets/info source helper inputs unavailable"],
      blocked_outputs: blockedOutputs,
      safe_use: safeUse,
      next_action: "Source helper inputs or fixtures for fundingFactorPerSecond, borrowing factors and longsPayShorts",
    },
    {
      review_id: "carry_conversion_boundary",
      review_label: "Carry Conversion Boundary",
      status: "blocked_for_carry_conversion",
      evidence_count: fixtureCoverageIds.length,
      diagnostic_field_ids: diagnosticFieldIds,
      source_inputs_required: sourceInputsRequired,
      fixture_coverage_ids: fixtureCoverageIds,
      blocked_by: blockedBy,
      blocked_outputs: blockedOutputs,
      safe_use: safeUse,
      next_action: "Complete mapping review, side-aware fixtures, holding period and notional before carry conversion",
    },
  ];
  const appendUnique = (items: string[], value: string) => {
    if (value && !items.includes(value)) items.push(value);
  };
  const slugId = (value: string) =>
    value.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "unknown";
  const blockerGroups = new Map<string, LivePerpDexGmxRateMappingBlockerBreakdown>();
  reviewItems.forEach((item) => {
    item.blocked_by.forEach((blocker) => {
      const blockerId = slugId(blocker);
      const group =
        blockerGroups.get(blockerId) ??
        {
          blocker_id: blockerId,
          blocker,
          review_count: 0,
          review_ids: [],
          review_statuses: [],
          source_inputs_required: [],
          fixture_coverage_ids: [],
          blocked_outputs: [],
          may_emit_carry_bps: false,
          may_estimate_cost_bps: false,
          may_rank_routes: false,
          may_submit_orders: false,
          safe_use: safeUse,
          next_action: "Clear this blocker before GMX carry conversion or route-cost diagnostics",
        };
      appendUnique(group.review_ids, item.review_id);
      appendUnique(group.review_statuses, item.status);
      item.source_inputs_required.forEach((sourceInput) => appendUnique(group.source_inputs_required, sourceInput));
      item.fixture_coverage_ids.forEach((fixtureId) => appendUnique(group.fixture_coverage_ids, fixtureId));
      item.blocked_outputs.forEach((outputId) => appendUnique(group.blocked_outputs, outputId));
      group.review_count = group.review_ids.length;
      blockerGroups.set(blockerId, group);
    });
  });
  const fixtureById = new Map((gmxRateSemantics.fixture_coverage ?? []).map((item) => [item.id, item]));
  const fixtureEvidenceCount = (fixtureIds: string[]) =>
    fixtureIds.filter((fixtureId) => fixtureById.has(fixtureId)).length;
  const fixtureReadinessMatrix: LivePerpDexGmxRateFixtureReadiness[] = [
    {
      case_id: "source_relation_raw_fields",
      case_label: "Source Relation Raw Fields",
      status: fixtureById.get("net_rate_relation_raw_fields")?.status ?? "source_relation_guardrail_added",
      evidence_count: fixtureEvidenceCount(["net_rate_relation_raw_fields"]),
      diagnostic_field_ids: ["rate_relation_summary"],
      source_inputs_required: [],
      fixture_coverage_ids: ["net_rate_relation_raw_fields"],
      blocked_by: ["live /markets/info nonzero borrowing rate mapping review"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      safe_use: safeUse,
      next_action: "Keep source relation fixture, but do not use it as live mapping confirmation",
    },
    {
      case_id: "live_nonzero_borrowing_relation",
      case_label: "Live Nonzero Borrowing Relation",
      status: "mapping_review_required",
      evidence_count: fixtureEvidenceCount([
        "live_nonzero_borrowing_raw_sum_relation_observed",
        "live_shape_offline_fixture",
      ]),
      diagnostic_field_ids: ["rate_relation_summary", "rate_relation_diagnostics"],
      source_inputs_required: sourceInputsRequired,
      fixture_coverage_ids: ["live_nonzero_borrowing_raw_sum_relation_observed", "live_shape_offline_fixture"],
      blocked_by: [
        "live /markets/info nonzero borrowing rate mapping review",
        "broader live fixture coverage across market states",
      ],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      safe_use: safeUse,
      next_action: "Reconcile observed funding+borrowing relation with source helper semantics",
    },
    {
      case_id: "live_zero_borrowing_ambiguity",
      case_label: "Live Zero Borrowing Ambiguity",
      status: "relation_ambiguous",
      evidence_count: fixtureEvidenceCount(["live_zero_borrowing_relation_ambiguity"]),
      diagnostic_field_ids: ["rate_relation_summary", "rate_relation_diagnostics"],
      source_inputs_required: sourceInputsRequired,
      fixture_coverage_ids: ["live_zero_borrowing_relation_ambiguity"],
      blocked_by: [
        "live /markets/info nonzero borrowing rate mapping review",
        "broader live fixture coverage across market states",
      ],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      safe_use: safeUse,
      next_action: "Do not treat zero-borrowing matches as source relation proof",
    },
    {
      case_id: "longs_pay_shorts_direction",
      case_label: "longsPayShorts Direction",
      status: "fixture_required",
      evidence_count: 0,
      diagnostic_field_ids: ["rate_source_fields_status", "rate_source_fields_summary"],
      source_inputs_required: ["fundingFactorPerSecond", "longsPayShorts"],
      fixture_coverage_ids: [],
      expectation_ids: sideAwareExpectationIds,
      expectation_notes: [
        "long position pays funding when longsPayShorts=true",
        "short position receives funding when longsPayShorts=true",
        "short position pays funding when longsPayShorts=false",
        "long position receives funding when longsPayShorts=false",
      ],
      blocked_by: ["side-aware funding sign tests", "live /markets/info source helper inputs unavailable"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      safe_use: safeUse,
      next_action: "Add side-aware fixtures for paying/receiving direction before carry bps",
    },
    {
      case_id: "source_helper_inputs_presence",
      case_label: "Source Helper Inputs Presence",
      status: "source_inputs_missing",
      evidence_count: 0,
      diagnostic_field_ids: ["rate_source_fields_status", "rate_source_fields_summary"],
      source_inputs_required: sourceInputsRequired,
      fixture_coverage_ids: [],
      blocked_by: ["live /markets/info source helper inputs unavailable"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      safe_use: safeUse,
      next_action: "Source helper inputs or equivalent fixtures before GMX carry conversion",
    },
  ];
  const mappingDecisionChecklist: LivePerpDexGmxRateMappingDecisionCheck[] = [
    {
      check_id: "source_helper_inputs_available",
      check_label: "Source Helper Inputs Available",
      status: "source_inputs_missing",
      required_source_inputs: sourceInputsRequired,
      required_fixture_case_ids: ["source_helper_inputs_presence"],
      required_expectation_ids: [],
      required_review_ids: ["source_helper_inputs"],
      manual_approval_required: true,
      manual_approval_id: "gmx_source_helper_input_review",
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Confirm source helper inputs or equivalent fixtures before diagnostic carry bps",
    },
    {
      check_id: "nonzero_borrowing_relation_reviewed",
      check_label: "Nonzero Borrowing Relation Reviewed",
      status: "mapping_review_required",
      required_source_inputs: sourceInputsRequired,
      required_fixture_case_ids: ["live_nonzero_borrowing_relation", "live_zero_borrowing_ambiguity"],
      required_expectation_ids: [],
      required_review_ids: ["live_nonzero_borrowing_mapping"],
      manual_approval_required: true,
      manual_approval_id: "gmx_live_nonzero_borrowing_mapping_review",
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Resolve live funding+borrowing observation against source helper semantics",
    },
    {
      check_id: "side_aware_direction_fixtures",
      check_label: "Side-aware Direction Fixtures",
      status: "fixture_required",
      required_source_inputs: ["fundingFactorPerSecond", "longsPayShorts"],
      required_fixture_case_ids: ["longs_pay_shorts_direction"],
      required_expectation_ids: sideAwareExpectationIds,
      required_review_ids: ["carry_conversion_boundary"],
      manual_approval_required: true,
      manual_approval_id: "gmx_side_aware_sign_review",
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Cover long/short paying and receiving fixtures before any carry conversion",
    },
    {
      check_id: "carry_inputs_defined",
      check_label: "Carry Inputs Defined",
      status: "input_required",
      required_source_inputs: [],
      required_fixture_case_ids: ["source_relation_raw_fields", "longs_pay_shorts_direction"],
      required_expectation_ids: sideAwareExpectationIds,
      required_review_ids: ["carry_conversion_boundary"],
      manual_approval_required: true,
      manual_approval_id: "gmx_carry_horizon_notional_review",
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Define holding_period_hours, position_notional_usd and sign convention before carry bps",
    },
    {
      check_id: "display_unit_decision_recorded",
      check_label: "Display Unit Decision Recorded",
      status: "policy_input_required",
      required_source_inputs: [],
      required_fixture_case_ids: [],
      required_expectation_ids: [],
      required_review_ids: ["carry_conversion_boundary"],
      manual_approval_required: true,
      manual_approval_id: "gmx_hourly_vs_annualized_display_decision",
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Record whether diagnostics display hourly or annualized units before showing any bps",
    },
  ];
  const mappingDecisionManualApprovalIds = mappingDecisionChecklist
    .filter((item) => item.manual_approval_required)
    .map((item) => item.manual_approval_id);
  const carryInputChecklist: LivePerpDexGmxRateCarryInputCheck[] = [
    {
      input_id: "holding_period_hours",
      input_label: "Holding Period Hours",
      status: "input_required",
      input_type: "runtime_input",
      required_source_inputs: [],
      required_fixture_case_ids: ["source_relation_raw_fields", "longs_pay_shorts_direction"],
      required_expectation_ids: sideAwareExpectationIds,
      required_decision_check_ids: ["carry_inputs_defined"],
      manual_approval_required: true,
      manual_approval_id: "gmx_carry_horizon_notional_review",
      blocked_by: ["holding_period_hours input"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Define holding_period_hours before diagnostic GMX carry bps",
    },
    {
      input_id: "position_notional_usd",
      input_label: "Position Notional USD",
      status: "input_required",
      input_type: "runtime_input",
      required_source_inputs: [],
      required_fixture_case_ids: ["source_relation_raw_fields", "longs_pay_shorts_direction"],
      required_expectation_ids: sideAwareExpectationIds,
      required_decision_check_ids: ["carry_inputs_defined"],
      manual_approval_required: true,
      manual_approval_id: "gmx_carry_horizon_notional_review",
      blocked_by: ["position_notional_usd input"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Define position_notional_usd before diagnostic GMX carry bps",
    },
    {
      input_id: "rate_sign_convention",
      input_label: "Rate Sign Convention",
      status: "fixture_required",
      input_type: "mapping_policy",
      required_source_inputs: ["fundingFactorPerSecond", "longsPayShorts"],
      required_fixture_case_ids: [
        "live_nonzero_borrowing_relation",
        "live_zero_borrowing_ambiguity",
        "longs_pay_shorts_direction",
      ],
      required_expectation_ids: sideAwareExpectationIds,
      required_decision_check_ids: [
        "nonzero_borrowing_relation_reviewed",
        "side_aware_direction_fixtures",
        "carry_inputs_defined",
      ],
      manual_approval_required: true,
      manual_approval_id: "gmx_side_aware_sign_review",
      blocked_by: [
        "side-aware funding sign tests",
        "live /markets/info nonzero borrowing rate mapping review",
        "live /markets/info source helper inputs unavailable",
      ],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Confirm side-aware pay/receive sign convention before diagnostic carry bps",
    },
    {
      input_id: "source_helper_inputs",
      input_label: "Source Helper Inputs",
      status: "source_inputs_missing",
      input_type: "source_fields",
      required_source_inputs: sourceInputsRequired,
      required_fixture_case_ids: ["source_helper_inputs_presence"],
      required_expectation_ids: [],
      required_decision_check_ids: ["source_helper_inputs_available"],
      manual_approval_required: true,
      manual_approval_id: "gmx_source_helper_input_review",
      blocked_by: ["live /markets/info source helper inputs unavailable"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Source GMX helper inputs or equivalent fixtures before diagnostic carry bps",
    },
    {
      input_id: "display_unit_decision",
      input_label: "Display Unit Decision",
      status: "policy_input_required",
      input_type: "display_policy",
      required_source_inputs: [],
      required_fixture_case_ids: [],
      required_expectation_ids: [],
      required_decision_check_ids: ["display_unit_decision_recorded"],
      manual_approval_required: true,
      manual_approval_id: "gmx_hourly_vs_annualized_display_decision",
      blocked_by: ["production decision on hourly vs annualized display"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Record hourly vs annualized display policy before any diagnostic carry bps",
    },
  ];
  const carryRequiredSourceInputs: string[] = [];
  const carryRequiredFixtureCaseIds: string[] = [];
  const carryRequiredExpectationIds: string[] = [];
  const carryRequiredDecisionCheckIds: string[] = [];
  carryInputChecklist.forEach((item) => {
    item.required_source_inputs.forEach((sourceInput) => appendUnique(carryRequiredSourceInputs, sourceInput));
    item.required_fixture_case_ids.forEach((caseId) => appendUnique(carryRequiredFixtureCaseIds, caseId));
    item.required_expectation_ids.forEach((expectationId) => appendUnique(carryRequiredExpectationIds, expectationId));
    item.required_decision_check_ids.forEach((checkId) => appendUnique(carryRequiredDecisionCheckIds, checkId));
  });
  const carryReadinessSummary: LivePerpDexGmxRateCarryReadinessSummary = {
    status: "blocked_for_diagnostic_carry_bps",
    input_count: carryInputChecklist.length,
    blocked_input_count: carryInputChecklist.length,
    manual_approval_count: mappingDecisionManualApprovalIds.length,
    required_source_inputs: carryRequiredSourceInputs,
    required_fixture_case_ids: carryRequiredFixtureCaseIds,
    required_expectation_ids: carryRequiredExpectationIds,
    required_decision_check_ids: carryRequiredDecisionCheckIds,
    required_manual_approval_ids: mappingDecisionManualApprovalIds,
    blocked_outputs: blockedOutputs,
    may_emit_carry_bps: false,
    may_estimate_cost_bps: false,
    may_rank_routes: false,
    may_submit_orders: false,
    safe_use: safeUse,
    next_action: "Clear carry inputs, fixtures, source helper fields and manual approvals before diagnostic GMX carry bps",
  };
  const carrySourceEvidenceChecklist: LivePerpDexGmxRateCarrySourceEvidenceCheck[] = [
    {
      evidence_id: "holding_period_runtime_input",
      evidence_label: "Holding Period Runtime Input",
      evidence_type: "runtime_input",
      status: "input_required",
      related_input_ids: ["holding_period_hours"],
      required_source_inputs: [],
      required_fixture_case_ids: ["source_relation_raw_fields", "longs_pay_shorts_direction"],
      required_expectation_ids: sideAwareExpectationIds,
      required_decision_check_ids: ["carry_inputs_defined"],
      required_manual_approval_ids: ["gmx_carry_horizon_notional_review"],
      blocked_by: ["holding_period_hours input"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Record holding_period_hours as an explicit runtime input before diagnostic GMX carry bps",
    },
    {
      evidence_id: "position_notional_runtime_input",
      evidence_label: "Position Notional Runtime Input",
      evidence_type: "runtime_input",
      status: "input_required",
      related_input_ids: ["position_notional_usd"],
      required_source_inputs: [],
      required_fixture_case_ids: ["source_relation_raw_fields", "longs_pay_shorts_direction"],
      required_expectation_ids: sideAwareExpectationIds,
      required_decision_check_ids: ["carry_inputs_defined"],
      required_manual_approval_ids: ["gmx_carry_horizon_notional_review"],
      blocked_by: ["position_notional_usd input"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Record position_notional_usd as an explicit runtime input before diagnostic GMX carry bps",
    },
    {
      evidence_id: "side_aware_sign_fixture_evidence",
      evidence_label: "Side-aware Sign Fixture Evidence",
      evidence_type: "fixture_case",
      status: "fixture_required",
      related_input_ids: ["rate_sign_convention"],
      required_source_inputs: ["fundingFactorPerSecond", "longsPayShorts"],
      required_fixture_case_ids: [
        "live_nonzero_borrowing_relation",
        "live_zero_borrowing_ambiguity",
        "longs_pay_shorts_direction",
      ],
      required_expectation_ids: sideAwareExpectationIds,
      required_decision_check_ids: ["nonzero_borrowing_relation_reviewed", "side_aware_direction_fixtures"],
      required_manual_approval_ids: ["gmx_side_aware_sign_review"],
      blocked_by: [
        "side-aware funding sign tests",
        "live /markets/info nonzero borrowing rate mapping review",
        "live /markets/info source helper inputs unavailable",
      ],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Attach side-aware longsPayShorts fixture evidence before diagnostic carry bps",
    },
    {
      evidence_id: "source_helper_field_evidence",
      evidence_label: "Source Helper Field Evidence",
      evidence_type: "source_field",
      status: "source_inputs_missing",
      related_input_ids: ["source_helper_inputs", "rate_sign_convention"],
      required_source_inputs: sourceInputsRequired,
      required_fixture_case_ids: ["source_helper_inputs_presence"],
      required_expectation_ids: [],
      required_decision_check_ids: ["source_helper_inputs_available", "nonzero_borrowing_relation_reviewed"],
      required_manual_approval_ids: ["gmx_source_helper_input_review", "gmx_live_nonzero_borrowing_mapping_review"],
      blocked_by: [
        "live /markets/info source helper inputs unavailable",
        "live /markets/info nonzero borrowing rate mapping review",
      ],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Collect source helper fields or equivalent fixtures before diagnostic carry bps",
    },
    {
      evidence_id: "display_unit_policy_evidence",
      evidence_label: "Display Unit Policy Evidence",
      evidence_type: "policy_decision",
      status: "policy_input_required",
      related_input_ids: ["display_unit_decision"],
      required_source_inputs: [],
      required_fixture_case_ids: [],
      required_expectation_ids: [],
      required_decision_check_ids: ["display_unit_decision_recorded"],
      required_manual_approval_ids: ["gmx_hourly_vs_annualized_display_decision"],
      blocked_by: ["production decision on hourly vs annualized display"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Record hourly vs annualized display policy before any diagnostic carry bps",
    },
    {
      evidence_id: "carry_manual_approval_evidence",
      evidence_label: "Carry Manual Approval Evidence",
      evidence_type: "manual_approval",
      status: "manual_approval_required",
      related_input_ids: [
        "holding_period_hours",
        "position_notional_usd",
        "rate_sign_convention",
        "source_helper_inputs",
        "display_unit_decision",
      ],
      required_source_inputs: sourceInputsRequired,
      required_fixture_case_ids: carryRequiredFixtureCaseIds,
      required_expectation_ids: sideAwareExpectationIds,
      required_decision_check_ids: carryRequiredDecisionCheckIds,
      required_manual_approval_ids: mappingDecisionManualApprovalIds,
      blocked_by: ["manual GMX carry approval gate"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Complete manual carry approvals after source and fixture evidence is attached",
    },
  ];
  const carrySourceEvidenceIds: string[] = [];
  const carrySourceEvidenceTypeIds: string[] = [];
  const carrySourceEvidenceInputIds: string[] = [];
  const carrySourceEvidenceSourceInputs: string[] = [];
  const carrySourceEvidenceFixtureCaseIds: string[] = [];
  const carrySourceEvidenceExpectationIds: string[] = [];
  const carrySourceEvidenceDecisionCheckIds: string[] = [];
  let carrySourceEvidenceManualApprovalIds: string[] = [];
  carrySourceEvidenceChecklist.forEach((item) => {
    appendUnique(carrySourceEvidenceIds, item.evidence_id);
    appendUnique(carrySourceEvidenceTypeIds, item.evidence_type);
    item.related_input_ids.forEach((inputId) => appendUnique(carrySourceEvidenceInputIds, inputId));
    item.required_source_inputs.forEach((sourceInput) => appendUnique(carrySourceEvidenceSourceInputs, sourceInput));
    item.required_fixture_case_ids.forEach((caseId) => appendUnique(carrySourceEvidenceFixtureCaseIds, caseId));
    item.required_expectation_ids.forEach((expectationId) => appendUnique(carrySourceEvidenceExpectationIds, expectationId));
    item.required_decision_check_ids.forEach((checkId) => appendUnique(carrySourceEvidenceDecisionCheckIds, checkId));
    item.required_manual_approval_ids.forEach((approvalId) => appendUnique(carrySourceEvidenceManualApprovalIds, approvalId));
  });
  carrySourceEvidenceManualApprovalIds = mappingDecisionManualApprovalIds.filter((approvalId) =>
    carrySourceEvidenceManualApprovalIds.includes(approvalId)
  );
  const carrySourceEvidenceSummary: LivePerpDexGmxRateCarrySourceEvidenceSummary = {
    status: "evidence_required",
    evidence_count: carrySourceEvidenceChecklist.length,
    blocked_evidence_count: carrySourceEvidenceChecklist.length,
    evidence_ids: carrySourceEvidenceIds,
    evidence_type_ids: carrySourceEvidenceTypeIds,
    input_ids: carrySourceEvidenceInputIds,
    required_source_inputs: carrySourceEvidenceSourceInputs,
    required_fixture_case_ids: carrySourceEvidenceFixtureCaseIds,
    required_expectation_ids: carrySourceEvidenceExpectationIds,
    required_decision_check_ids: carrySourceEvidenceDecisionCheckIds,
    required_manual_approval_ids: carrySourceEvidenceManualApprovalIds,
    blocked_outputs: blockedOutputs,
    may_emit_carry_bps: false,
    may_estimate_cost_bps: false,
    may_rank_routes: false,
    may_submit_orders: false,
    safe_use: safeUse,
    next_action: "Attach source, fixture, runtime and manual approval evidence before diagnostic GMX carry bps",
  };
  const liveRateOutputFields = [
    "fundingRateLong",
    "fundingRateShort",
    "borrowingRateLong",
    "borrowingRateShort",
    "netRateLong",
    "netRateShort",
  ];
  const liveHelperSourceChecklist: LivePerpDexGmxRateLiveHelperSourceReview[] = [
    {
      review_id: "live_rate_output_fields_available",
      review_label: "Live Rate Output Fields Available",
      status: "raw_outputs_available",
      source_scope: "live_markets_info_rate_outputs",
      evidence_count: mappingReview?.live_observed?.length ?? 0,
      observed_source_fields: liveRateOutputFields,
      required_source_inputs: [],
      present_source_inputs: [],
      missing_source_inputs: sourceInputsRequired,
      diagnostic_field_ids: ["rate_relation_summary", "rate_relation_diagnostics"],
      fixture_case_ids: ["live_nonzero_borrowing_relation", "live_zero_borrowing_ambiguity"],
      expectation_ids: [],
      manual_approval_required: true,
      manual_approval_id: "gmx_live_nonzero_borrowing_mapping_review",
      blocked_by: [
        "live /markets/info helper source fields unavailable",
        "live /markets/info nonzero borrowing rate mapping review",
      ],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Keep raw ticker rate outputs as evidence only until helper inputs are sourced",
    },
    {
      review_id: "nonzero_borrowing_relation_evidence",
      review_label: "Nonzero Borrowing Relation Evidence",
      status: "mapping_review_required",
      source_scope: "live_markets_info_relation_evidence",
      evidence_count: fixtureEvidenceCount(["live_nonzero_borrowing_raw_sum_relation_observed", "live_shape_offline_fixture"]),
      observed_source_fields: liveRateOutputFields,
      required_source_inputs: sourceInputsRequired,
      present_source_inputs: [],
      missing_source_inputs: sourceInputsRequired,
      diagnostic_field_ids: ["rate_relation_summary", "rate_relation_diagnostics"],
      fixture_case_ids: ["live_nonzero_borrowing_relation", "live_zero_borrowing_ambiguity"],
      expectation_ids: [],
      manual_approval_required: true,
      manual_approval_id: "gmx_live_nonzero_borrowing_mapping_review",
      blocked_by: [
        "live /markets/info nonzero borrowing rate mapping review",
        "broader live fixture coverage across market states",
      ],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Reconcile observed funding+borrowing relation against source helper semantics",
    },
    {
      review_id: "helper_source_fields_presence",
      review_label: "Helper Source Fields Presence",
      status: "source_inputs_missing",
      source_scope: "live_markets_info_helper_inputs",
      evidence_count: 0,
      observed_source_fields: [],
      required_source_inputs: sourceInputsRequired,
      present_source_inputs: [],
      missing_source_inputs: sourceInputsRequired,
      diagnostic_field_ids: ["rate_source_fields_status", "rate_source_fields_summary"],
      fixture_case_ids: ["source_helper_inputs_presence"],
      expectation_ids: [],
      manual_approval_required: true,
      manual_approval_id: "gmx_source_helper_input_review",
      blocked_by: ["live /markets/info source helper inputs unavailable"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Source helper inputs or equivalent fixture artifacts before carry conversion",
    },
    {
      review_id: "side_direction_helper_fields",
      review_label: "Side Direction Helper Fields",
      status: "fixture_required",
      source_scope: "longs_pay_shorts_direction",
      evidence_count: 0,
      observed_source_fields: [],
      required_source_inputs: ["fundingFactorPerSecond", "longsPayShorts"],
      present_source_inputs: [],
      missing_source_inputs: ["fundingFactorPerSecond", "longsPayShorts"],
      diagnostic_field_ids: ["rate_source_fields_status", "rate_source_fields_summary"],
      fixture_case_ids: ["longs_pay_shorts_direction"],
      expectation_ids: sideAwareExpectationIds,
      manual_approval_required: true,
      manual_approval_id: "gmx_side_aware_sign_review",
      blocked_by: ["side-aware funding sign tests", "live /markets/info source helper inputs unavailable"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Cover long/short paying and receiving direction before carry bps",
    },
    {
      review_id: "manual_live_helper_mapping_review",
      review_label: "Manual Live Helper Mapping Review",
      status: "manual_approval_required",
      source_scope: "manual_review_gate",
      evidence_count: 0,
      observed_source_fields: liveRateOutputFields,
      required_source_inputs: sourceInputsRequired,
      present_source_inputs: [],
      missing_source_inputs: sourceInputsRequired,
      diagnostic_field_ids: diagnosticFieldIds,
      fixture_case_ids: [
        "live_nonzero_borrowing_relation",
        "live_zero_borrowing_ambiguity",
        "longs_pay_shorts_direction",
        "source_helper_inputs_presence",
      ],
      expectation_ids: sideAwareExpectationIds,
      manual_approval_required: true,
      manual_approval_id: "gmx_live_helper_source_review",
      blocked_by: [
        "manual GMX live helper source review",
        "live /markets/info source helper inputs unavailable",
        "side-aware funding sign tests",
      ],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Approve live helper/source mapping only after source fields, fixtures and side direction evidence are attached",
    },
  ];
  const liveHelperReviewIds: string[] = [];
  const liveHelperReviewStatuses: string[] = [];
  const liveHelperObservedSourceFields: string[] = [];
  const liveHelperRequiredSourceInputs: string[] = [];
  const liveHelperPresentSourceInputs: string[] = [];
  const liveHelperMissingSourceInputs: string[] = [];
  const liveHelperDiagnosticFieldIds: string[] = [];
  const liveHelperFixtureCaseIds: string[] = [];
  const liveHelperExpectationIds: string[] = [];
  const liveHelperManualApprovalIds: string[] = [];
  liveHelperSourceChecklist.forEach((item) => {
    appendUnique(liveHelperReviewIds, item.review_id);
    appendUnique(liveHelperReviewStatuses, item.status);
    item.observed_source_fields.forEach((fieldId) => appendUnique(liveHelperObservedSourceFields, fieldId));
    item.required_source_inputs.forEach((sourceInput) => appendUnique(liveHelperRequiredSourceInputs, sourceInput));
    item.present_source_inputs.forEach((sourceInput) => appendUnique(liveHelperPresentSourceInputs, sourceInput));
    item.missing_source_inputs.forEach((sourceInput) => appendUnique(liveHelperMissingSourceInputs, sourceInput));
    item.diagnostic_field_ids.forEach((fieldId) => appendUnique(liveHelperDiagnosticFieldIds, fieldId));
    item.fixture_case_ids.forEach((caseId) => appendUnique(liveHelperFixtureCaseIds, caseId));
    item.expectation_ids.forEach((expectationId) => appendUnique(liveHelperExpectationIds, expectationId));
    if (item.manual_approval_required) appendUnique(liveHelperManualApprovalIds, item.manual_approval_id);
  });
  const liveHelperSourceSummary: LivePerpDexGmxRateLiveHelperSourceSummary = {
    status: "helper_source_review_required",
    review_count: liveHelperSourceChecklist.length,
    blocked_review_count: liveHelperSourceChecklist.length,
    review_ids: liveHelperReviewIds,
    review_statuses: liveHelperReviewStatuses,
    observed_source_fields: liveHelperObservedSourceFields,
    required_source_inputs: liveHelperRequiredSourceInputs,
    present_source_inputs: liveHelperPresentSourceInputs,
    missing_source_inputs: liveHelperMissingSourceInputs,
    diagnostic_field_ids: liveHelperDiagnosticFieldIds,
    fixture_case_ids: liveHelperFixtureCaseIds,
    expectation_ids: liveHelperExpectationIds,
    manual_approval_ids: liveHelperManualApprovalIds,
    blocked_outputs: blockedOutputs,
    may_emit_carry_bps: false,
    may_estimate_cost_bps: false,
    may_rank_routes: false,
    may_submit_orders: false,
    safe_use: safeUse,
    next_action: "Complete live helper/source review before diagnostic GMX carry bps",
  };
  const helperSourceFollowUpChecklist: LivePerpDexGmxRateHelperSourceFollowUpItem[] = [
    {
      follow_up_id: "source_helper_inputs_missing",
      follow_up_label: "Source Helper Inputs Missing",
      follow_up_type: "missing_source_input",
      status: "source_inputs_missing",
      related_input_ids: ["source_helper_inputs", "rate_sign_convention"],
      related_review_ids: ["helper_source_fields_presence", "manual_live_helper_mapping_review"],
      missing_source_inputs: sourceInputsRequired,
      required_fixture_case_ids: ["source_helper_inputs_presence"],
      required_expectation_ids: [],
      required_decision_check_ids: ["source_helper_inputs_available"],
      blocking_manual_approval_ids: ["gmx_source_helper_input_review", "gmx_live_helper_source_review"],
      blocked_by: ["live /markets/info source helper inputs unavailable", "manual GMX live helper source review"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Source missing helper inputs or equivalent fixtures before GMX carry conversion",
    },
    {
      follow_up_id: "live_nonzero_mapping_approval",
      follow_up_label: "Live Nonzero Mapping Approval",
      follow_up_type: "manual_approval",
      status: "mapping_review_required",
      related_input_ids: ["source_helper_inputs", "rate_sign_convention"],
      related_review_ids: ["live_rate_output_fields_available", "nonzero_borrowing_relation_evidence"],
      missing_source_inputs: sourceInputsRequired,
      required_fixture_case_ids: ["live_nonzero_borrowing_relation", "live_zero_borrowing_ambiguity"],
      required_expectation_ids: [],
      required_decision_check_ids: ["nonzero_borrowing_relation_reviewed", "source_helper_inputs_available"],
      blocking_manual_approval_ids: ["gmx_live_nonzero_borrowing_mapping_review"],
      blocked_by: [
        "live /markets/info nonzero borrowing rate mapping review",
        "live /markets/info source helper inputs unavailable",
      ],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Resolve live funding+borrowing mapping before any carry conversion",
    },
    {
      follow_up_id: "side_direction_approval",
      follow_up_label: "Side Direction Approval",
      follow_up_type: "fixture_manual_approval",
      status: "fixture_required",
      related_input_ids: ["rate_sign_convention"],
      related_review_ids: ["side_direction_helper_fields"],
      missing_source_inputs: ["fundingFactorPerSecond", "longsPayShorts"],
      required_fixture_case_ids: ["longs_pay_shorts_direction"],
      required_expectation_ids: sideAwareExpectationIds,
      required_decision_check_ids: ["side_aware_direction_fixtures"],
      blocking_manual_approval_ids: ["gmx_side_aware_sign_review"],
      blocked_by: ["side-aware funding sign tests", "live /markets/info source helper inputs unavailable"],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Approve side-aware long/short funding direction only after fixtures exist",
    },
    {
      follow_up_id: "carry_runtime_policy_approvals",
      follow_up_label: "Carry Runtime And Policy Approvals",
      follow_up_type: "carry_boundary_approval",
      status: "manual_approval_required",
      related_input_ids: ["holding_period_hours", "position_notional_usd", "display_unit_decision"],
      related_review_ids: ["carry_conversion_boundary"],
      missing_source_inputs: [],
      required_fixture_case_ids: ["source_relation_raw_fields", "longs_pay_shorts_direction"],
      required_expectation_ids: sideAwareExpectationIds,
      required_decision_check_ids: ["carry_inputs_defined", "display_unit_decision_recorded"],
      blocking_manual_approval_ids: [
        "gmx_carry_horizon_notional_review",
        "gmx_hourly_vs_annualized_display_decision",
      ],
      blocked_by: [
        "holding_period_hours input",
        "position_notional_usd input",
        "production decision on hourly vs annualized display",
      ],
      blocked_outputs: blockedOutputs,
      may_emit_carry_bps: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
      safe_use: safeUse,
      next_action: "Record runtime carry inputs and display policy before carry conversion",
    },
  ];
  const helperSourceFollowUpIds: string[] = [];
  const helperSourceFollowUpStatuses: string[] = [];
  const helperSourceFollowUpInputIds: string[] = [];
  const helperSourceFollowUpReviewIds: string[] = [];
  const helperSourceFollowUpMissingInputs: string[] = [];
  const helperSourceFollowUpFixtureCaseIds: string[] = [];
  const helperSourceFollowUpExpectationIds: string[] = [];
  const helperSourceFollowUpDecisionCheckIds: string[] = [];
  const helperSourceFollowUpManualApprovalIds: string[] = [];
  helperSourceFollowUpChecklist.forEach((item) => {
    appendUnique(helperSourceFollowUpIds, item.follow_up_id);
    appendUnique(helperSourceFollowUpStatuses, item.status);
    item.related_input_ids.forEach((inputId) => appendUnique(helperSourceFollowUpInputIds, inputId));
    item.related_review_ids.forEach((reviewId) => appendUnique(helperSourceFollowUpReviewIds, reviewId));
    item.missing_source_inputs.forEach((sourceInput) => appendUnique(helperSourceFollowUpMissingInputs, sourceInput));
    item.required_fixture_case_ids.forEach((caseId) => appendUnique(helperSourceFollowUpFixtureCaseIds, caseId));
    item.required_expectation_ids.forEach((expectationId) => appendUnique(helperSourceFollowUpExpectationIds, expectationId));
    item.required_decision_check_ids.forEach((checkId) => appendUnique(helperSourceFollowUpDecisionCheckIds, checkId));
    item.blocking_manual_approval_ids.forEach((approvalId) => appendUnique(helperSourceFollowUpManualApprovalIds, approvalId));
  });
  const helperSourceFollowUpSummary: LivePerpDexGmxRateHelperSourceFollowUpSummary = {
    status: "follow_up_required",
    follow_up_count: helperSourceFollowUpChecklist.length,
    blocked_follow_up_count: helperSourceFollowUpChecklist.length,
    follow_up_ids: helperSourceFollowUpIds,
    follow_up_statuses: helperSourceFollowUpStatuses,
    related_input_ids: helperSourceFollowUpInputIds,
    related_review_ids: helperSourceFollowUpReviewIds,
    missing_source_inputs: helperSourceFollowUpMissingInputs,
    required_fixture_case_ids: helperSourceFollowUpFixtureCaseIds,
    required_expectation_ids: helperSourceFollowUpExpectationIds,
    required_decision_check_ids: helperSourceFollowUpDecisionCheckIds,
    blocking_manual_approval_ids: helperSourceFollowUpManualApprovalIds,
    blocked_outputs: blockedOutputs,
    may_emit_carry_bps: false,
    may_estimate_cost_bps: false,
    may_rank_routes: false,
    may_submit_orders: false,
    safe_use: safeUse,
    next_action: "Close helper/source follow-up rows before any GMX carry conversion",
  };
  return {
    status: "mapping_review_required",
    read_only: true,
    source_relation_status: "source_relation_guardrail_added",
    live_mapping_status: mappingReview?.status ?? "source_vs_live_mapping_unresolved",
    source_confirmed_count: mappingReview?.source_confirmed?.length ?? 0,
    live_observed_count: mappingReview?.live_observed?.length ?? 0,
    fixture_coverage_count: fixtureCoverageIds.length,
    diagnostic_field_ids: diagnosticFieldIds,
    source_inputs_required: sourceInputsRequired,
    fixture_coverage_ids: fixtureCoverageIds,
    blocked_outputs: blockedOutputs,
    may_emit_carry_bps: false,
    may_estimate_cost_bps: false,
    may_rank_routes: false,
    may_submit_orders: false,
    safe_use: safeUse,
    next_action: gmxRateSemantics.next_action ?? "Map live GMX rate semantics before carry bps",
    review_items: reviewItems,
    blocker_breakdown: Array.from(blockerGroups.values()),
    fixture_readiness_matrix: fixtureReadinessMatrix,
    side_aware_fixture_expectations: sideAwareFixtureExpectations,
    mapping_decision_checklist: mappingDecisionChecklist,
    carry_readiness_summary: carryReadinessSummary,
    carry_input_checklist: carryInputChecklist,
    carry_source_evidence_summary: carrySourceEvidenceSummary,
    carry_source_evidence_checklist: carrySourceEvidenceChecklist,
    live_helper_source_summary: liveHelperSourceSummary,
    live_helper_source_checklist: liveHelperSourceChecklist,
    helper_source_follow_up_summary: helperSourceFollowUpSummary,
    helper_source_follow_up_checklist: helperSourceFollowUpChecklist,
  };
}

function outputPolicyLabel(value?: boolean): string {
  if (typeof value !== "boolean") return "Unknown";
  return value ? "Allowed" : "Blocked";
}

function outputPolicyTone(value: boolean | undefined, expectedValue: boolean) {
  if (value === expectedValue) return "positive";
  if (typeof value === "boolean") return "negative";
  return "warning";
}

function guardrailValueLabel(value: string | boolean | undefined): string {
  if (typeof value === "boolean") return value ? "True" : "False";
  if (typeof value === "string" && value.length > 0) return policyStatusLabel(value);
  return "Unknown";
}

function guardrailTone(value: string | boolean | undefined, expectedValue: string | boolean) {
  if (value === expectedValue) return "positive";
  if (typeof value === "string" || typeof value === "boolean") return "negative";
  return "warning";
}

type PerpDexPageProps = {
  searchParams?: Promise<{ view?: string }>;
};

export default async function PerpDexPage({ searchParams }: PerpDexPageProps) {
  const params = await searchParams;
  const activeView = normalizeView(params?.view);
  const activeTab = perpDexViews.find((item) => item.view === activeView) ?? perpDexViews[0];
  const [health, matrix, scanner, hyperliquid, dydx, lighter, aster, gmx, coinglassPerpDex, routePolicy, routeModel] = await Promise.all([
    getLiveDataHealth(),
    getLiveMarketMatrix(),
    getLiveArbitrageScanner(),
    getLiveHyperliquidMarkets(),
    getLiveDydxMarkets(),
    getLiveLighterMarkets(),
    getLiveAsterMarkets(),
    getLiveGmxMarkets(),
    getLiveCoinGlassPerpDexMarkets(),
    getLivePerpDexRouteConstraints(),
    getLivePerpDexRouteModel(),
  ]);
  const rowCounts = health?.row_counts ?? {};
  const providers = Object.values(health?.providers ?? {});
  const healthyProviders = providers.filter((provider) => provider.healthy).length;
  const hyperliquidRows = hyperliquid.markets.length;
  const hyperliquidLive = hyperliquid.status === "live" && hyperliquidRows > 0;
  const dydxRows = dydx.markets.length;
  const dydxLive = dydx.status === "live" && dydxRows > 0;
  const lighterRows = lighter.markets.length;
  const lighterLive = lighter.status === "live" && lighterRows > 0;
  const asterRows = aster.markets.length;
  const asterLive = aster.status === "live" && asterRows > 0;
  const gmxRows = gmx.markets.length;
  const gmxRaw = gmx.status === "partial" && gmxRows > 0;
  const coinglassPerpDexRows = coinglassPerpDex.markets.length;
  const sourceStatusRows = buildPerpDexSourceStatusRows(
    [hyperliquid, dydx, lighter, aster, gmx],
    coinglassPerpDex,
    routePolicy,
    routeModel
  );
  const visibleVenueLabels = [
    hyperliquidRows > 0 ? "Hyperliquid" : null,
    dydxRows > 0 ? "dYdX" : null,
    lighterRows > 0 ? "Lighter" : null,
    asterRows > 0 ? "Aster" : null,
    gmxRaw ? "GMX raw" : null,
    coinglassPerpDexRows > 0 ? "CoinGlass research" : null,
  ].filter((label): label is string => Boolean(label));
  const dexMarkets = [...hyperliquid.markets, ...dydx.markets, ...lighter.markets, ...aster.markets, ...gmx.markets].sort((left, right) =>
    `${left.venue_name}:${left.symbol}`.localeCompare(`${right.venue_name}:${right.symbol}`)
  );
  const depthDiagnosticRows = dexMarkets
    .filter((market) => Boolean(market.orderbook_depth_status))
    .map(depthDiagnosticCells);
  const coinglassMarkets = coinglassPerpDex.markets.sort((left, right) =>
    `${left.venue_name}:${left.symbol}`.localeCompare(`${right.venue_name}:${right.symbol}`)
  );
  const coinglassCoverageRows = Object.entries(coinglassPerpDex.coverage_summary?.by_exchange ?? {}).map(
    ([venue, coverage]) => [
      <span key="venue" className="font-semibold text-cyan-200">
        {venue}
      </span>,
      <span key="status" className={toneText(coverageStatusTone(coverage.status))}>
        {policyStatusLabel(coverage.status)}
      </span>,
      <span key="rows" className="font-mono text-slate-100">
        {coverage.matched_rows}/{coverage.requested_rows}
      </span>,
      routeModelList(coverage.matched_symbols),
      routeModelList(coverage.available_field_groups),
      coverage.next_action,
    ]
  );
  const liveDexVenues = [hyperliquidLive, dydxLive, lighterLive, asterLive].filter(Boolean).length;
  const directVenueRows = dexMarkets.length;
  const livePerpRows = matrix.rows.filter(
    (row) => row.perpPrice !== null || row.fundingPct !== null || row.openInterestUsd !== null
  ).length;
  const largestOi = matrix.rows.reduce<LiveMatrixRow | null>((best, row) => {
    if (row.openInterestUsd === null) return best;
    if (!best || row.openInterestUsd > (best.openInterestUsd ?? 0)) return row;
    return best;
  }, null);
  const largestEdge = scanner.opportunities[0] ?? null;

  const kpis: KpiMetric[] = [
    {
      label: "Perp Inputs",
      value: `${livePerpRows}/${matrix.rows.length}`,
      caption: `${CORE_SYMBOLS_LABEL} live streams`,
      tone: livePerpRows === matrix.rows.length ? "positive" : "warning",
    },
    {
      label: "DEX Venue Data",
      value: directVenueRows ? `${directVenueRows} rows` : "Pending",
      caption: directVenueRows
        ? `${liveDexVenues}/4 normalized live${gmxRaw ? ", GMX raw" : ""}`
        : "Direct venue adapters",
      tone: liveDexVenues ? "positive" : "warning",
    },
    {
      label: "CG PerpDEX",
      value: coinglassPerpDexRows ? `${coinglassPerpDexRows} rows` : "Pending",
      caption:
        coinglassPerpDex.requested_exchanges && coinglassPerpDex.requested_exchanges.length
          ? coinglassPerpDex.requested_exchanges.join(" / ")
          : "CoinGlass research",
      tone: coinglassPerpDexRows ? "positive" : "warning",
    },
    {
      label: "Largest OI",
      value: largestOi ? largestOi.asset : "No data",
      caption: largestOi ? formatCompactCurrency(largestOi.openInterestUsd ?? 0) : "Open interest",
      tone: largestOi ? "positive" : "warning",
    },
    {
      label: "Funding Rows",
      value: formatRows(rowCounts.funding_rates),
      caption: "OKX/CoinGlass",
      tone: (rowCounts.funding_rates ?? 0) > 0 ? "positive" : "warning",
    },
    {
      label: "Liquidation Rows",
      value: formatRows(rowCounts.liquidations),
      caption: "CoinGlass aggregated",
      tone: (rowCounts.liquidations ?? 0) > 0 ? "positive" : "warning",
    },
    {
      label: "Largest Edge",
      value: largestEdge ? `${largestEdge.asset} ${formatMaybePercent(largestEdge.edgePct)}` : "No data",
      caption: "Basis/funding candidate",
      tone: largestEdge ? "positive" : "warning",
    },
  ];

  const providerRows = providers.map((provider) => [
    provider.provider_name,
    <span key="status" className={toneText(provider.healthy ? "positive" : "warning")}>
      {provider.status}
    </span>,
    lastSyncTime(provider.last_sync),
    provider.last_error_message ?? "-",
  ]);

  const dataCoverageRows = [
    ["OHLCV", rowCounts.ohlcv, "OKX 1m candles"],
    ["Funding", rowCounts.funding_rates, "OKX + CoinGlass"],
    ["Open Interest", rowCounts.open_interest, "OKX preferred, CoinGlass fallback"],
    ["Liquidations", rowCounts.liquidations, "CoinGlass aggregated history"],
    ["Long/Short", rowCounts.long_short_ratio, "OKX account ratio"],
    ["Basis", rowCounts.basis_premium, "CoinGecko spot + OKX perp"],
  ].map(([stream, count, source]) => [
    stream,
    <span key="rows" className="font-mono text-slate-100">
      {formatRows(typeof count === "number" ? count : 0)}
    </span>,
    source,
    <span key="status" className={toneText(typeof count === "number" && count > 0 ? "positive" : "warning")}>
      {typeof count === "number" && count > 0 ? "Live" : "Empty"}
    </span>,
  ]);

  const adapterRows = [
    ["OKX USDT Swap", "Live", "Primary OHLCV, funding, OI, long/short"],
    ["Binance USD-M", "Degraded", "Restricted on current VPS region"],
    ["CoinGlass", "Live", "Funding/OI snapshots and aggregated liquidations"],
    [
      "CoinGlass PerpDEX",
      coinglassPerpDexRows ? "Research" : coinglassPerpDex.status === "unavailable" ? "Unavailable" : "Pending",
      coinglassPerpDexRows
        ? "Third-party DEX-like futures coin-market enrichment"
        : "Perp DEX enrichment pending",
    ],
    ["CoinGecko", "Live", "Spot price and basis context"],
    [
      "Hyperliquid",
      hyperliquidLive ? "Live" : hyperliquid.status === "unavailable" ? "Unavailable" : "Pending",
      hyperliquidLive ? "Direct public market snapshot" : "Direct public market snapshot pending",
    ],
    [
      "dYdX",
      dydxLive ? "Live" : dydx.status === "unavailable" ? "Unavailable" : "Pending",
      dydxLive ? "dYdX Indexer public market snapshot" : "dYdX Indexer snapshot pending",
    ],
    [
      "Lighter",
      lighterLive ? "Live" : lighter.status === "unavailable" ? "Unavailable" : "Pending",
      lighterLive ? "Public market details + funding snapshot" : "Lighter public market snapshot pending",
    ],
    [
      "Aster",
      asterLive ? "Live" : aster.status === "unavailable" ? "Unavailable" : "Pending",
      asterLive ? "Public futures market data snapshot" : "Aster public market snapshot pending",
    ],
    [
      "GMX",
      gmxRaw ? "Raw" : gmx.status === "unavailable" ? "Unavailable" : "Pending",
      gmxRaw ? "Arbitrum markets/info raw fixed-point snapshot with token pool diagnostics" : "GMX raw snapshot pending",
    ],
  ].map(([venue, status, note]) => [
    venue,
    <span key="status" className={toneText(status === "Live" ? "positive" : "warning")}>
      {status}
    </span>,
    note,
  ]);

  const routePolicyRows = routePolicy.capabilities.map((capability) => [
    capability.label,
    <span key="status" className={toneText(policyStatusTone(capability.status))}>
      {policyStatusLabel(capability.status)}
    </span>,
    capability.scope,
    capability.next_action,
  ]);
  const routeBlockerRows = routePolicy.blockers.map((blocker) => [
    blocker.scope,
    <span key="blocker" className={toneText("negative")}>
      {blocker.id.replaceAll("_", " ")}
    </span>,
    blocker.reason,
    routeModelList(blocker.missing_inputs ?? []),
    routeModelList(blocker.blocked_by ?? []),
    blocker.safe_use ?? "Keep route scoring disabled",
    blocker.next_action,
  ]);
  const routeSafetyGuardrailRows =
    routePolicy.status === "unavailable" || routeModel.status === "unavailable"
      ? []
      : [
          {
            scope: "Policy",
            guardrail: "Research-only status",
            value: routePolicy.status,
            expectedValue: "research_only",
            reason: "Route constraints must stay research-only until route scoring is validated",
          },
          {
            scope: "Policy",
            guardrail: "Execution disabled",
            value: routePolicy.execution_enabled,
            expectedValue: false,
            reason: "No order submission path is wired",
          },
          {
            scope: "Policy",
            guardrail: "Liquidity ranking disabled",
            value: routePolicy.ui_policy.may_rank_by_liquidity,
            expectedValue: false,
            reason: "Direct venue depth/cost inputs are not route-ready",
          },
          {
            scope: "Policy",
            guardrail: "Order submission disabled",
            value: routePolicy.ui_policy.may_submit_orders,
            expectedValue: false,
            reason: "Execution connector, risk gates and confirmation flow are missing",
          },
          {
            scope: "Model",
            guardrail: "Model read-only",
            value: routeModel.read_only,
            expectedValue: true,
            reason: "Route model can show diagnostics only",
          },
          {
            scope: "Model",
            guardrail: "Route ranking disabled",
            value: routeModel.ranking_enabled,
            expectedValue: false,
            reason: "Numeric route cost and liquidity cap model are not validated",
          },
          {
            scope: "Model",
            guardrail: "Production signal disabled",
            value: routeModel.production_signal_enabled,
            expectedValue: false,
            reason: "Current outputs are research/display diagnostics",
          },
          {
            scope: "Diagnostics",
            guardrail: "Numeric total bps disabled",
            value: routeModel.diagnostic_cost_estimate_v0?.may_emit_numeric_total_bps,
            expectedValue: false,
            reason: "Component diagnostics must not be summed into route cost",
          },
        ].map((row) => [
          row.scope,
          row.guardrail,
          <span key="actual" className={toneText(guardrailTone(row.value, row.expectedValue))}>
            {guardrailValueLabel(row.value)}
          </span>,
          guardrailValueLabel(row.expectedValue),
          row.reason,
        ]);
  const routeModelOutputPolicyRows =
    routeModel.status === "unavailable"
      ? []
      : [
          {
            capability: "Input Checklist",
            value: routeModel.output_policy.may_show_checklist,
            expectedValue: true,
            safeUse: "Show required and missing inputs only",
          },
          {
            capability: "Formula Skeleton",
            value: routeModel.output_policy.may_show_formula_skeleton,
            expectedValue: true,
            safeUse: "Show formula shape without numeric route total",
          },
          {
            capability: "Diagnostic Components",
            value: routeModel.output_policy.may_show_diagnostic_cost_components,
            expectedValue: true,
            safeUse: "Show sourced component readiness only",
          },
          {
            capability: "Numeric Cost Bps",
            value: routeModel.output_policy.may_estimate_cost_bps,
            expectedValue: false,
            safeUse: "Blocked until fee, depth, carry and order intent inputs are sourced",
          },
          {
            capability: "Route Ranking",
            value: routeModel.output_policy.may_rank_routes,
            expectedValue: false,
            safeUse: "Blocked until route cost and liquidity model are validated",
          },
          {
            capability: "Order Submission",
            value: routeModel.output_policy.may_submit_orders,
            expectedValue: false,
            safeUse: "Blocked until execution connector, risk gates and confirmation flow exist",
          },
        ].map((row) => [
          row.capability,
          <span key="status" className={toneText(outputPolicyTone(row.value, row.expectedValue))}>
            {outputPolicyLabel(row.value)}
          </span>,
          outputPolicyLabel(row.expectedValue),
          row.safeUse,
        ]);
  const routeModelBlockerRows = routeModel.blockers.map((blocker) => [
    <span key="blocker" className={toneText("negative")}>
      {blocker.id.replaceAll("_", " ")}
    </span>,
    blocker.reason,
    routeModelList(blocker.missing_inputs ?? []),
    routeModelList(blocker.blocked_by ?? []),
    blocker.safe_use ?? "Keep route model read-only",
  ]);
  const routeRequiredInputRows = routeModel.required_inputs.map((input) => [
    <span key="input" className="font-semibold text-cyan-200">
      {input.label}
    </span>,
    <span key="status" className={toneText("warning")}>
      Required
    </span>,
    input.id.replaceAll("_", " "),
    input.reason,
  ]);

  const routeModelComponentRows = routeModel.model_components.map((component) => [
    component.label,
    <span key="status" className={toneText(policyStatusTone(component.status))}>
      {policyStatusLabel(component.status)}
    </span>,
    routeModelList(component.required_inputs),
    component.blocked_reason,
  ]);

  const routeModelVenueRows = routeModel.venue_readiness.map((venue) => [
    venue.venue_name,
    <span key="status" className={toneText(policyStatusTone(venue.status))}>
      {policyStatusLabel(venue.status)}
    </span>,
    venue.source_semantics ?? "No source semantics available",
    routeModelList(venue.available_inputs),
    routeModelList(venue.missing_inputs),
    venue.safe_use,
  ]);

  const routeFormulaRows = Object.entries(routeModel.formula_skeleton).map(([name, formula]) => [
    name.replaceAll("_", " "),
    <span key="formula" className="font-mono text-slate-100">
      {formula}
    </span>,
  ]);
  const diagnosticComponents = routeModel.diagnostic_cost_estimate_v0?.components ?? [];
  const displayOnlyDiagnosticComponents = diagnosticComponents.filter((component) => component.may_emit_component_bps);
  const blockedDiagnosticComponents = diagnosticComponents.filter((component) => !component.may_emit_component_bps);
  const sourcedDiagnosticComponents = diagnosticComponents.filter((component) => component.source_fields.length > 0);
  const diagnosticComponentSummary = routeModel.diagnostic_cost_estimate_v0?.summary;
  const diagnosticComponentCount = diagnosticComponentSummary?.component_count ?? diagnosticComponents.length;
  const displayOnlyDiagnosticComponentCount =
    diagnosticComponentSummary?.display_only_component_count ?? displayOnlyDiagnosticComponents.length;
  const blockedDiagnosticComponentCount =
    diagnosticComponentSummary?.blocked_numeric_component_count ?? blockedDiagnosticComponents.length;
  const sourcedDiagnosticComponentCount = diagnosticComponentSummary?.sourced_component_count ?? sourcedDiagnosticComponents.length;
  const diagnosticSummaryStatus =
    diagnosticComponentSummary?.status ?? routeModel.diagnostic_cost_estimate_v0?.status ?? "unavailable";
  const diagnosticSummarySafeUse =
    diagnosticComponentSummary?.safe_use ?? routeModel.diagnostic_cost_estimate_v0?.safe_use ?? "Component readiness only";
  const diagnosticSummaryNextAction =
    diagnosticComponentSummary?.next_action ??
    routeModel.diagnostic_cost_estimate_v0?.next_action ??
    "Source required cost inputs before total bps";
  const mayEmitNumericTotalBps =
    diagnosticComponentSummary?.may_emit_numeric_total_bps ??
    routeModel.diagnostic_cost_estimate_v0?.may_emit_numeric_total_bps ??
    false;
  const diagnosticVenueBreakdown =
    diagnosticComponentSummary?.venue_breakdown?.length
      ? diagnosticComponentSummary.venue_breakdown
      : buildRouteDiagnosticVenueBreakdown(diagnosticComponents);
  const diagnosticBlockerBreakdown =
    diagnosticComponentSummary?.blocker_breakdown?.length
      ? diagnosticComponentSummary.blocker_breakdown
      : buildRouteDiagnosticBlockerBreakdown(diagnosticComponents);
  const diagnosticRequiredInputBreakdown =
    diagnosticComponentSummary?.required_input_breakdown?.length
      ? diagnosticComponentSummary.required_input_breakdown
      : buildRouteDiagnosticRequiredInputBreakdown(routeModel.required_inputs, diagnosticComponents);
  const diagnosticSourceFieldBreakdown =
    diagnosticComponentSummary?.source_field_breakdown?.length
      ? diagnosticComponentSummary.source_field_breakdown
      : buildRouteDiagnosticSourceFieldBreakdown(diagnosticComponents);
  const diagnosticSafeUseBreakdown =
    diagnosticComponentSummary?.safe_use_breakdown?.length
      ? diagnosticComponentSummary.safe_use_breakdown
      : buildRouteDiagnosticSafeUseBreakdown(diagnosticComponents);
  const diagnosticReadinessRollup =
    diagnosticComponentSummary?.readiness_rollup?.length
      ? diagnosticComponentSummary.readiness_rollup
      : buildRouteDiagnosticReadinessRollup(diagnosticComponents);
  const diagnosticDepthPolicyChecklist =
    diagnosticComponentSummary?.depth_staleness_policy_checklist?.length
      ? diagnosticComponentSummary.depth_staleness_policy_checklist
      : buildRouteDiagnosticDepthPolicyChecklist(diagnosticComponents);
  const diagnosticRequiredPolicyInputBreakdown =
    diagnosticComponentSummary?.required_policy_input_breakdown?.length
      ? diagnosticComponentSummary.required_policy_input_breakdown
      : buildRouteDiagnosticRequiredPolicyInputBreakdown(diagnosticDepthPolicyChecklist);
  const diagnosticNextActionBreakdown =
    diagnosticComponentSummary?.next_action_breakdown?.length
      ? diagnosticComponentSummary.next_action_breakdown
      : buildRouteDiagnosticNextActionBreakdown(
          diagnosticRequiredInputBreakdown,
          diagnosticReadinessRollup,
          diagnosticDepthPolicyChecklist
        );
  const diagnosticSourceInputActionCoverage =
    diagnosticComponentSummary?.source_input_action_coverage?.length
      ? diagnosticComponentSummary.source_input_action_coverage
      : buildRouteDiagnosticSourceInputActionCoverage(diagnosticSourceFieldBreakdown, diagnosticNextActionBreakdown);
  const diagnosticRouteReadyEvidenceChecklist =
    diagnosticComponentSummary?.route_ready_evidence_checklist?.length
      ? diagnosticComponentSummary.route_ready_evidence_checklist
      : buildRouteDiagnosticRouteReadyEvidenceChecklist(diagnosticSourceFieldBreakdown, diagnosticDepthPolicyChecklist);
  const diagnosticVenueEvidenceStatus =
    diagnosticComponentSummary?.venue_evidence_status?.length
      ? diagnosticComponentSummary.venue_evidence_status
      : buildRouteDiagnosticVenueEvidenceStatus(
          diagnosticRouteReadyEvidenceChecklist,
          diagnosticSourceFieldBreakdown,
          routeModel.gmx_rate_semantics
        );
  const fallbackGmxRateMappingReview = buildGmxRateMappingReview(routeModel.gmx_rate_semantics);
  const gmxRateMappingReview = routeModel.gmx_rate_mapping_review_v0 ?? fallbackGmxRateMappingReview;
  const gmxRateMappingBlockerBreakdown =
    gmxRateMappingReview?.blocker_breakdown?.length
      ? gmxRateMappingReview.blocker_breakdown
      : fallbackGmxRateMappingReview?.blocker_breakdown ?? [];
  const gmxRateFixtureReadinessMatrix =
    gmxRateMappingReview?.fixture_readiness_matrix?.length
      ? gmxRateMappingReview.fixture_readiness_matrix
      : fallbackGmxRateMappingReview?.fixture_readiness_matrix ?? [];
  const gmxRateSideAwareFixtureExpectations =
    gmxRateMappingReview?.side_aware_fixture_expectations?.length
      ? gmxRateMappingReview.side_aware_fixture_expectations
      : fallbackGmxRateMappingReview?.side_aware_fixture_expectations ?? [];
  const gmxRateMappingDecisionChecklist =
    gmxRateMappingReview?.mapping_decision_checklist?.length
      ? gmxRateMappingReview.mapping_decision_checklist
      : fallbackGmxRateMappingReview?.mapping_decision_checklist ?? [];
  const gmxRateCarryReadinessSummary =
    gmxRateMappingReview?.carry_readiness_summary ?? fallbackGmxRateMappingReview?.carry_readiness_summary ?? null;
  const gmxRateCarryInputChecklist =
    gmxRateMappingReview?.carry_input_checklist?.length
      ? gmxRateMappingReview.carry_input_checklist
      : fallbackGmxRateMappingReview?.carry_input_checklist ?? [];
  const gmxRateCarrySourceEvidenceSummary =
    gmxRateMappingReview?.carry_source_evidence_summary ?? fallbackGmxRateMappingReview?.carry_source_evidence_summary ?? null;
  const gmxRateCarrySourceEvidenceChecklist =
    gmxRateMappingReview?.carry_source_evidence_checklist?.length
      ? gmxRateMappingReview.carry_source_evidence_checklist
      : fallbackGmxRateMappingReview?.carry_source_evidence_checklist ?? [];
  const gmxRateLiveHelperSourceSummary =
    gmxRateMappingReview?.live_helper_source_summary ?? fallbackGmxRateMappingReview?.live_helper_source_summary ?? null;
  const gmxRateLiveHelperSourceChecklist =
    gmxRateMappingReview?.live_helper_source_checklist?.length
      ? gmxRateMappingReview.live_helper_source_checklist
      : fallbackGmxRateMappingReview?.live_helper_source_checklist ?? [];
  const gmxRateHelperSourceFollowUpSummary =
    gmxRateMappingReview?.helper_source_follow_up_summary ??
    fallbackGmxRateMappingReview?.helper_source_follow_up_summary ??
    null;
  const gmxRateHelperSourceFollowUpChecklist =
    gmxRateMappingReview?.helper_source_follow_up_checklist?.length
      ? gmxRateMappingReview.helper_source_follow_up_checklist
      : fallbackGmxRateMappingReview?.helper_source_follow_up_checklist ?? [];
  const routeDiagnosticComponentSummaryRows =
    routeModel.status === "unavailable"
      ? []
      : [
          [
            "Diagnostic Components",
            <span key="value" className="font-mono text-slate-100">
              {diagnosticComponentCount}
            </span>,
            <span key="boundary" className={toneText(policyStatusTone(diagnosticSummaryStatus))}>
              {policyStatusLabel(diagnosticSummaryStatus)}
            </span>,
            diagnosticSummarySafeUse,
          ],
          [
            "Display-only Component Outputs",
            <span key="value" className={toneText(displayOnlyDiagnosticComponentCount > 0 ? "warning" : "neutral")}>
              {displayOnlyDiagnosticComponentCount}
            </span>,
            <span key="boundary" className={toneText("warning")}>
              Component Display Only
            </span>,
            "May show sourced component diagnostics, but not sum route cost",
          ],
          [
            "Blocked Numeric Components",
            <span key="value" className={toneText(blockedDiagnosticComponentCount > 0 ? "positive" : "negative")}>
              {blockedDiagnosticComponentCount}
            </span>,
            <span key="boundary" className={toneText("positive")}>
              Numeric Bps Blocked
            </span>,
            "No account-level fee, slippage or carry bps without required inputs",
          ],
          [
            "Components With Source Fields",
            <span key="value" className="font-mono text-slate-100">
              {sourcedDiagnosticComponentCount}/{diagnosticComponentCount}
            </span>,
            <span key="boundary" className={toneText("warning")}>
              Source Context Only
            </span>,
            "Source fields can explain readiness, not production route scoring",
          ],
          [
            "Numeric Total Bps",
            <span
              key="value"
              className={toneText(mayEmitNumericTotalBps === false ? "positive" : "negative")}
            >
              {mayEmitNumericTotalBps ? "Allowed" : "Blocked"}
            </span>,
            <span key="boundary" className={toneText("positive")}>
              Total Disabled
            </span>,
            diagnosticSummaryNextAction,
          ],
        ];
  const routeDiagnosticVenueBreakdownRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticVenueBreakdown.map((venue) => [
          <span key="venue" className="font-semibold text-cyan-200">
            {venue.venue_label || routeDiagnosticVenueLabel(venue.venue_id)}
          </span>,
          <span key="components" className="font-mono text-slate-100">
            {venue.component_count}
          </span>,
          <span key="display" className={toneText(venue.display_only_component_count > 0 ? "warning" : "neutral")}>
            {venue.display_only_component_count}
          </span>,
          <span key="blocked" className={toneText(venue.blocked_numeric_component_count > 0 ? "positive" : "negative")}>
            {venue.blocked_numeric_component_count}
          </span>,
          <span key="sourced" className="font-mono text-slate-100">
            {venue.sourced_component_count}/{venue.component_count}
          </span>,
          routeModelList(venue.component_ids),
          routeModelList(venue.blocked_numeric_component_ids),
          venue.safe_use,
        ]);
  const routeDiagnosticReadinessRollupRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticReadinessRollup.map((item) => [
          <span key="category" className="font-semibold text-cyan-200">
            {item.category_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          routeModelList(item.required_input_ids),
          <span key="components" className="font-mono text-slate-100">
            {item.component_count}
          </span>,
          <span key="sourced" className="font-mono text-slate-100">
            {item.sourced_component_count}/{item.component_count}
          </span>,
          routeModelList(item.display_component_ids),
          routeModelList(item.blocked_numeric_component_ids),
          item.next_action,
        ]);
  const routeDiagnosticDepthPolicyRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticDepthPolicyChecklist.map((item) => [
          <span key="venue" className="font-semibold text-cyan-200">
            {item.venue_label}
          </span>,
          item.depth_scope,
          item.source_endpoint,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          routeModelList(item.source_fields),
          routeModelList(item.required_policy_inputs),
          routeModelList(item.blocked_by),
          <span key="slippage" className={toneText(item.may_emit_slippage_bps ? "negative" : "positive")}>
            {item.may_emit_slippage_bps ? "Allowed" : "Blocked"}
          </span>,
          item.next_action,
        ]);
  const routeDiagnosticRequiredPolicyInputRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticRequiredPolicyInputBreakdown.map((item) => [
          <span key="input" className="font-semibold text-cyan-200">
            {item.input_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          <span key="policies" className="font-mono text-slate-100">
            {item.policy_count}
          </span>,
          routeModelList(item.policy_ids),
          routeModelList(item.component_ids),
          routeModelList(item.venue_ids),
          routeModelList(item.source_endpoints),
          routeModelList(item.blocked_by),
          <span key="slippage" className={toneText(item.may_emit_slippage_bps ? "negative" : "positive")}>
            {item.may_emit_slippage_bps ? "Allowed" : "Blocked"}
          </span>,
          item.next_action,
        ]);
  const routeDiagnosticNextActionRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticNextActionBreakdown.map((item) => [
          item.next_action,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          <span key="sources" className="font-mono text-slate-100">
            {item.source_count}
          </span>,
          routeModelList(item.source_types),
          routeModelList(item.required_input_ids),
          routeModelList(item.required_policy_inputs),
          routeModelList(item.component_ids),
          routeModelList(item.venue_ids),
          <span key="total" className={toneText(item.numeric_total_status === "blocked" ? "positive" : "negative")}>
            {policyStatusLabel(item.numeric_total_status)}
          </span>,
          item.safe_use,
        ]);
  const routeDiagnosticBlockerBreakdownRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticBlockerBreakdown.map((blocker) => [
          <span key="blocker" className="font-semibold text-cyan-200">
            {blocker.blocker}
          </span>,
          <span key="components" className="font-mono text-slate-100">
            {blocker.component_count}
          </span>,
          routeModelList(blocker.venue_ids),
          routeModelList(blocker.component_ids),
          routeModelList(blocker.display_component_ids),
          routeModelList(blocker.blocked_numeric_component_ids),
          <span key="status" className={toneText(blocker.numeric_total_status === "blocked" ? "positive" : "negative")}>
            {policyStatusLabel(blocker.numeric_total_status)}
          </span>,
          blocker.safe_use,
        ]);
  const routeDiagnosticRequiredInputBreakdownRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticRequiredInputBreakdown.map((input) => [
          <span key="input" className="font-semibold text-cyan-200">
            {input.input_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(input.status))}>
            {policyStatusLabel(input.status)}
          </span>,
          <span key="components" className="font-mono text-slate-100">
            {input.component_count}
          </span>,
          routeModelList(input.venue_ids),
          routeModelList(input.component_ids),
          routeModelList(input.display_component_ids),
          routeModelList(input.blocked_numeric_component_ids),
          input.next_action,
        ]);
  const routeDiagnosticSourceFieldBreakdownRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticSourceFieldBreakdown.map((field) => [
          <span key="field" className="font-semibold text-cyan-200">
            {field.source_field}
          </span>,
          <span key="status" className={toneText(policyStatusTone(field.status))}>
            {policyStatusLabel(field.status)}
          </span>,
          <span key="components" className="font-mono text-slate-100">
            {field.component_count}
          </span>,
          routeModelList(field.venue_ids),
          routeModelList(field.required_input_ids),
          routeModelList(field.component_ids),
          routeModelList(field.blocked_numeric_component_ids),
          field.safe_use,
        ]);
  const routeDiagnosticSourceInputActionCoverageRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticSourceInputActionCoverage.map((field) => [
          <span key="field" className="font-semibold text-cyan-200">
            {field.source_field}
          </span>,
          <span key="status" className={toneText(policyStatusTone(field.status))}>
            {policyStatusLabel(field.status)}
          </span>,
          <span key="components" className="font-mono text-slate-100">
            {field.component_count}
          </span>,
          routeModelList(field.venue_ids),
          routeModelList(field.required_input_ids),
          routeModelList(field.next_actions),
          routeModelList(field.blocked_numeric_component_ids),
          <span key="total" className={toneText(policyStatusTone(field.numeric_total_status))}>
            {policyStatusLabel(field.numeric_total_status)}
          </span>,
          field.safe_use,
        ]);
  const routeDiagnosticRouteReadyEvidenceRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticRouteReadyEvidenceChecklist.map((gate) => [
          <span key="gate" className="font-semibold text-cyan-200">
            {gate.gate_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(gate.status))}>
            {policyStatusLabel(gate.status)}
          </span>,
          <span key="evidence" className="font-mono text-slate-100">
            {gate.evidence_count}
          </span>,
          routeModelList(gate.required_input_ids),
          routeModelList(gate.required_policy_inputs),
          routeModelList(gate.source_field_ids),
          routeModelList(gate.blocked_outputs),
          <span key="flags" className={toneText("positive")}>
            {[
              gate.may_estimate_cost_bps ? "Cost Allowed" : "Cost Blocked",
              gate.may_rank_routes ? "Rank Allowed" : "Rank Blocked",
              gate.may_submit_orders ? "Exec Allowed" : "Exec Blocked",
            ].join(" / ")}
          </span>,
          gate.next_action,
        ]);
  const routeDiagnosticVenueEvidenceRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticVenueEvidenceStatus.map((venue) => [
          <span key="venue" className="font-semibold text-cyan-200">
            {venue.venue_label}
          </span>,
          venue.venue_scope,
          <span key="status" className={toneText(policyStatusTone(venue.status))}>
            {policyStatusLabel(venue.status)}
          </span>,
          <span key="evidence" className="font-mono text-slate-100">
            {venue.evidence_count}
          </span>,
          routeModelList(venue.venue_gate_ids),
          routeModelList(venue.cross_venue_gate_ids),
          routeModelList(venue.required_input_ids),
          routeModelList(venue.required_policy_inputs),
          routeModelList([...venue.source_field_ids, ...venue.diagnostic_field_ids, ...venue.fixture_coverage_ids]),
          routeModelList(venue.blocked_outputs),
          <span key="flags" className={toneText("positive")}>
            {[
              venue.may_estimate_cost_bps ? "Cost Allowed" : "Cost Blocked",
              venue.may_rank_routes ? "Rank Allowed" : "Rank Blocked",
              venue.may_submit_orders ? "Exec Allowed" : "Exec Blocked",
            ].join(" / ")}
          </span>,
          venue.next_action,
        ]);
  const gmxRateMappingReviewRows =
    routeModel.status === "unavailable" || !gmxRateMappingReview
      ? []
      : gmxRateMappingReview.review_items.map((item) => [
          <span key="review" className="font-semibold text-cyan-200">
            {item.review_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          <span key="evidence" className="font-mono text-slate-100">
            {item.evidence_count}
          </span>,
          routeModelList(item.diagnostic_field_ids),
          routeModelList(item.source_inputs_required),
          routeModelList(item.fixture_coverage_ids),
          routeModelList(item.blocked_by),
          <span key="flags" className={toneText("positive")}>
            {[
              gmxRateMappingReview.may_emit_carry_bps ? "Carry Allowed" : "Carry Blocked",
              gmxRateMappingReview.may_estimate_cost_bps ? "Cost Allowed" : "Cost Blocked",
              gmxRateMappingReview.may_rank_routes ? "Rank Allowed" : "Rank Blocked",
              gmxRateMappingReview.may_submit_orders ? "Exec Allowed" : "Exec Blocked",
            ].join(" / ")}
          </span>,
          item.next_action,
        ]);
  const gmxRateMappingBlockerRows =
    routeModel.status === "unavailable" || !gmxRateMappingReview
      ? []
      : gmxRateMappingBlockerBreakdown.map((blocker) => [
          <span key="blocker" className="font-semibold text-cyan-200">
            {blocker.blocker}
          </span>,
          <span key="reviews" className="font-mono text-slate-100">
            {blocker.review_count}
          </span>,
          routeModelList(blocker.review_ids),
          routeModelList(blocker.review_statuses.map((status) => policyStatusLabel(status))),
          routeModelList(blocker.source_inputs_required),
          routeModelList(blocker.fixture_coverage_ids),
          routeModelList(blocker.blocked_outputs),
          <span key="flags" className={toneText("positive")}>
            {[
              blocker.may_emit_carry_bps ? "Carry Allowed" : "Carry Blocked",
              blocker.may_estimate_cost_bps ? "Cost Allowed" : "Cost Blocked",
              blocker.may_rank_routes ? "Rank Allowed" : "Rank Blocked",
              blocker.may_submit_orders ? "Exec Allowed" : "Exec Blocked",
            ].join(" / ")}
          </span>,
          blocker.next_action,
        ]);
  const gmxRateFixtureReadinessRows =
    routeModel.status === "unavailable" || !gmxRateMappingReview
      ? []
      : gmxRateFixtureReadinessMatrix.map((item) => [
          <span key="case" className="font-semibold text-cyan-200">
            {item.case_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          <span key="evidence" className="font-mono text-slate-100">
            {item.evidence_count}
          </span>,
          routeModelList(item.source_inputs_required),
          routeModelList(item.diagnostic_field_ids),
          routeModelList(item.fixture_coverage_ids),
          routeModelList(item.blocked_by),
          <span key="carry" className={toneText(item.may_emit_carry_bps ? "negative" : "positive")}>
            {item.may_emit_carry_bps ? "Carry Allowed" : "Carry Blocked"}
          </span>,
          routeModelList(item.expectation_notes ?? []),
          item.next_action,
        ]);
  const gmxRateSideAwareFixtureExpectationRows =
    routeModel.status === "unavailable" || !gmxRateMappingReview
      ? []
      : gmxRateSideAwareFixtureExpectations.map((item) => [
          <span key="case" className="font-semibold text-cyan-200">
            {item.case_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          item.position_side,
          item.longs_pay_shorts ? "true" : "false",
          item.expected_funding_direction,
          routeModelList(item.required_source_inputs),
          routeModelList(item.fixture_coverage_ids),
          routeModelList(item.blocked_by),
          <span key="carry" className={toneText(item.may_emit_carry_bps ? "negative" : "positive")}>
            {item.may_emit_carry_bps ? "Carry Allowed" : "Carry Blocked"}
          </span>,
          item.next_action,
        ]);
  const gmxRateMappingDecisionRows =
    routeModel.status === "unavailable" || !gmxRateMappingReview
      ? []
      : gmxRateMappingDecisionChecklist.map((item) => [
          <span key="check" className="font-semibold text-cyan-200">
            {item.check_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          routeModelList(item.required_source_inputs),
          routeModelList(item.required_fixture_case_ids),
          routeModelList(item.required_expectation_ids),
          routeModelList(item.required_review_ids),
          item.manual_approval_required ? item.manual_approval_id : "None",
          routeModelList(item.blocked_outputs),
          <span key="flags" className={toneText("positive")}>
            {[
              item.may_emit_carry_bps ? "Carry Allowed" : "Carry Blocked",
              item.may_estimate_cost_bps ? "Cost Allowed" : "Cost Blocked",
              item.may_rank_routes ? "Rank Allowed" : "Rank Blocked",
              item.may_submit_orders ? "Exec Allowed" : "Exec Blocked",
            ].join(" / ")}
          </span>,
          item.next_action,
        ]);
  const gmxRateCarryReadinessSummaryRows =
    routeModel.status === "unavailable" || !gmxRateCarryReadinessSummary
      ? []
      : [
          [
            "Readiness Status",
            <span key="status" className={toneText(policyStatusTone(gmxRateCarryReadinessSummary.status))}>
              {policyStatusLabel(gmxRateCarryReadinessSummary.status)}
            </span>,
            <span key="inputs" className="font-mono text-slate-100">
              {gmxRateCarryReadinessSummary.blocked_input_count}/{gmxRateCarryReadinessSummary.input_count}
            </span>,
            routeModelList(gmxRateCarryReadinessSummary.required_decision_check_ids),
            routeModelList(gmxRateCarryReadinessSummary.required_manual_approval_ids),
            gmxRateCarryReadinessSummary.safe_use,
          ],
          [
            "Required Source Inputs",
            <span key="status" className={toneText("warning")}>
              Source/Fixture Gate
            </span>,
            routeModelList(gmxRateCarryReadinessSummary.required_source_inputs),
            routeModelList(gmxRateCarryReadinessSummary.required_fixture_case_ids),
            routeModelList(gmxRateCarryReadinessSummary.required_expectation_ids),
            gmxRateCarryReadinessSummary.next_action,
          ],
          [
            "Blocked Outputs",
            <span key="status" className={toneText("positive")}>
              Carry Blocked / Cost Blocked / Rank Blocked / Exec Blocked
            </span>,
            routeModelList(gmxRateCarryReadinessSummary.blocked_outputs),
            <span key="approvals" className="font-mono text-slate-100">
              {gmxRateCarryReadinessSummary.manual_approval_count}
            </span>,
            routeModelList(gmxRateCarryReadinessSummary.required_manual_approval_ids),
            "Diagnostic carry bps remains unavailable until all approvals and source/fixture gates are cleared",
          ],
        ];
  const gmxRateCarryInputRows =
    routeModel.status === "unavailable" || !gmxRateMappingReview
      ? []
      : gmxRateCarryInputChecklist.map((item) => [
          <span key="input" className="font-semibold text-cyan-200">
            {item.input_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          item.input_type,
          routeModelList(item.required_source_inputs),
          routeModelList(item.required_fixture_case_ids),
          routeModelList(item.required_expectation_ids),
          routeModelList(item.required_decision_check_ids),
          item.manual_approval_required ? item.manual_approval_id : "None",
          routeModelList(item.blocked_by),
          <span key="flags" className={toneText("positive")}>
            {[
              item.may_emit_carry_bps ? "Carry Allowed" : "Carry Blocked",
              item.may_estimate_cost_bps ? "Cost Allowed" : "Cost Blocked",
              item.may_rank_routes ? "Rank Allowed" : "Rank Blocked",
              item.may_submit_orders ? "Exec Allowed" : "Exec Blocked",
            ].join(" / ")}
          </span>,
          item.next_action,
        ]);
  const gmxRateCarrySourceEvidenceSummaryRows =
    routeModel.status === "unavailable" || !gmxRateCarrySourceEvidenceSummary
      ? []
      : [
          [
            "Evidence Status",
            <span key="status" className={toneText(policyStatusTone(gmxRateCarrySourceEvidenceSummary.status))}>
              {policyStatusLabel(gmxRateCarrySourceEvidenceSummary.status)}
            </span>,
            <span key="count" className="font-mono text-slate-100">
              {gmxRateCarrySourceEvidenceSummary.blocked_evidence_count}/{gmxRateCarrySourceEvidenceSummary.evidence_count}
            </span>,
            routeModelList(gmxRateCarrySourceEvidenceSummary.evidence_type_ids),
            routeModelList(gmxRateCarrySourceEvidenceSummary.input_ids),
            gmxRateCarrySourceEvidenceSummary.safe_use,
          ],
          [
            "Evidence Requirements",
            <span key="status" className={toneText("warning")}>
              Source / Fixture / Manual Gate
            </span>,
            routeModelList(gmxRateCarrySourceEvidenceSummary.required_source_inputs),
            routeModelList(gmxRateCarrySourceEvidenceSummary.required_fixture_case_ids),
            routeModelList(gmxRateCarrySourceEvidenceSummary.required_decision_check_ids),
            routeModelList(gmxRateCarrySourceEvidenceSummary.required_manual_approval_ids),
          ],
          [
            "Blocked Outputs",
            <span key="status" className={toneText("positive")}>
              Carry Blocked / Cost Blocked / Rank Blocked / Exec Blocked
            </span>,
            routeModelList(gmxRateCarrySourceEvidenceSummary.blocked_outputs),
            routeModelList(gmxRateCarrySourceEvidenceSummary.evidence_ids),
            routeModelList(gmxRateCarrySourceEvidenceSummary.required_expectation_ids),
            gmxRateCarrySourceEvidenceSummary.next_action,
          ],
        ];
  const gmxRateCarrySourceEvidenceRows =
    routeModel.status === "unavailable" || !gmxRateMappingReview
      ? []
      : gmxRateCarrySourceEvidenceChecklist.map((item) => [
          <span key="evidence" className="font-semibold text-cyan-200">
            {item.evidence_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          item.evidence_type,
          routeModelList(item.related_input_ids),
          routeModelList(item.required_source_inputs),
          routeModelList(item.required_fixture_case_ids),
          routeModelList(item.required_expectation_ids),
          routeModelList(item.required_decision_check_ids),
          routeModelList(item.required_manual_approval_ids),
          routeModelList(item.blocked_by),
          <span key="flags" className={toneText("positive")}>
            {[
              item.may_emit_carry_bps ? "Carry Allowed" : "Carry Blocked",
              item.may_estimate_cost_bps ? "Cost Allowed" : "Cost Blocked",
              item.may_rank_routes ? "Rank Allowed" : "Rank Blocked",
              item.may_submit_orders ? "Exec Allowed" : "Exec Blocked",
            ].join(" / ")}
          </span>,
          item.next_action,
        ]);
  const gmxRateLiveHelperSourceSummaryRows =
    routeModel.status === "unavailable" || !gmxRateLiveHelperSourceSummary
      ? []
      : [
          [
            "Live Helper Review",
            <span key="status" className={toneText(policyStatusTone(gmxRateLiveHelperSourceSummary.status))}>
              {policyStatusLabel(gmxRateLiveHelperSourceSummary.status)}
            </span>,
            <span key="count" className="font-mono text-slate-100">
              {gmxRateLiveHelperSourceSummary.blocked_review_count}/{gmxRateLiveHelperSourceSummary.review_count}
            </span>,
            routeModelList(gmxRateLiveHelperSourceSummary.observed_source_fields),
            routeModelList(gmxRateLiveHelperSourceSummary.missing_source_inputs),
            gmxRateLiveHelperSourceSummary.safe_use,
          ],
          [
            "Required Evidence",
            <span key="status" className={toneText("warning")}>
              Helper / Fixture Gate
            </span>,
            routeModelList(gmxRateLiveHelperSourceSummary.review_statuses.map((status) => policyStatusLabel(status))),
            routeModelList(gmxRateLiveHelperSourceSummary.fixture_case_ids),
            routeModelList(gmxRateLiveHelperSourceSummary.expectation_ids),
            routeModelList(gmxRateLiveHelperSourceSummary.manual_approval_ids),
          ],
          [
            "Blocked Outputs",
            <span key="status" className={toneText("positive")}>
              Carry Blocked / Cost Blocked / Rank Blocked / Exec Blocked
            </span>,
            routeModelList(gmxRateLiveHelperSourceSummary.blocked_outputs),
            routeModelList(gmxRateLiveHelperSourceSummary.diagnostic_field_ids),
            routeModelList(gmxRateLiveHelperSourceSummary.required_source_inputs),
            gmxRateLiveHelperSourceSummary.next_action,
          ],
        ];
  const gmxRateLiveHelperSourceRows =
    routeModel.status === "unavailable" || !gmxRateMappingReview
      ? []
      : gmxRateLiveHelperSourceChecklist.map((item) => [
          <span key="review" className="font-semibold text-cyan-200">
            {item.review_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          item.source_scope,
          <span key="evidence" className="font-mono text-slate-100">
            {item.evidence_count}
          </span>,
          routeModelList(item.observed_source_fields),
          routeModelList(item.required_source_inputs),
          routeModelList(item.missing_source_inputs),
          routeModelList(item.fixture_case_ids),
          routeModelList(item.expectation_ids),
          item.manual_approval_required ? item.manual_approval_id : "None",
          routeModelList(item.blocked_by),
          <span key="flags" className={toneText("positive")}>
            {[
              item.may_emit_carry_bps ? "Carry Allowed" : "Carry Blocked",
              item.may_estimate_cost_bps ? "Cost Allowed" : "Cost Blocked",
              item.may_rank_routes ? "Rank Allowed" : "Rank Blocked",
              item.may_submit_orders ? "Exec Allowed" : "Exec Blocked",
            ].join(" / ")}
          </span>,
          item.next_action,
        ]);
  const gmxRateHelperSourceFollowUpSummaryRows =
    routeModel.status === "unavailable" || !gmxRateHelperSourceFollowUpSummary
      ? []
      : [
          [
            "Follow-up Status",
            <span key="status" className={toneText(policyStatusTone(gmxRateHelperSourceFollowUpSummary.status))}>
              {policyStatusLabel(gmxRateHelperSourceFollowUpSummary.status)}
            </span>,
            <span key="count" className="font-mono text-slate-100">
              {gmxRateHelperSourceFollowUpSummary.blocked_follow_up_count}/
              {gmxRateHelperSourceFollowUpSummary.follow_up_count}
            </span>,
            routeModelList(gmxRateHelperSourceFollowUpSummary.missing_source_inputs),
            routeModelList(gmxRateHelperSourceFollowUpSummary.blocking_manual_approval_ids),
            gmxRateHelperSourceFollowUpSummary.safe_use,
          ],
          [
            "Related Gates",
            <span key="status" className={toneText("warning")}>
              Helper / Manual Gate
            </span>,
            routeModelList(gmxRateHelperSourceFollowUpSummary.related_input_ids),
            routeModelList(gmxRateHelperSourceFollowUpSummary.related_review_ids),
            routeModelList(gmxRateHelperSourceFollowUpSummary.required_decision_check_ids),
            gmxRateHelperSourceFollowUpSummary.next_action,
          ],
          [
            "Blocked Outputs",
            <span key="status" className={toneText("positive")}>
              Carry Blocked / Cost Blocked / Rank Blocked / Exec Blocked
            </span>,
            routeModelList(gmxRateHelperSourceFollowUpSummary.blocked_outputs),
            routeModelList(gmxRateHelperSourceFollowUpSummary.required_fixture_case_ids),
            routeModelList(gmxRateHelperSourceFollowUpSummary.required_expectation_ids),
            routeModelList(gmxRateHelperSourceFollowUpSummary.follow_up_statuses.map((status) => policyStatusLabel(status))),
          ],
        ];
  const gmxRateHelperSourceFollowUpRows =
    routeModel.status === "unavailable" || !gmxRateMappingReview
      ? []
      : gmxRateHelperSourceFollowUpChecklist.map((item) => [
          <span key="follow-up" className="font-semibold text-cyan-200">
            {item.follow_up_label}
          </span>,
          <span key="status" className={toneText(policyStatusTone(item.status))}>
            {policyStatusLabel(item.status)}
          </span>,
          item.follow_up_type,
          routeModelList(item.related_input_ids),
          routeModelList(item.related_review_ids),
          routeModelList(item.missing_source_inputs),
          routeModelList(item.required_fixture_case_ids),
          routeModelList(item.required_expectation_ids),
          routeModelList(item.required_decision_check_ids),
          routeModelList(item.blocking_manual_approval_ids),
          routeModelList(item.blocked_by),
          <span key="flags" className={toneText("positive")}>
            {[
              item.may_emit_carry_bps ? "Carry Allowed" : "Carry Blocked",
              item.may_estimate_cost_bps ? "Cost Allowed" : "Cost Blocked",
              item.may_rank_routes ? "Rank Allowed" : "Rank Blocked",
              item.may_submit_orders ? "Exec Allowed" : "Exec Blocked",
            ].join(" / ")}
          </span>,
          item.next_action,
        ]);
  const routeDiagnosticSafeUseBreakdownRows =
    routeModel.status === "unavailable"
      ? []
      : diagnosticSafeUseBreakdown.map((boundary) => [
          <span key="status" className={toneText(policyStatusTone(boundary.status))}>
            {policyStatusLabel(boundary.status)}
          </span>,
          <span key="components" className="font-mono text-slate-100">
            {boundary.component_count}
          </span>,
          routeModelList(boundary.venue_ids),
          routeModelList(boundary.required_input_ids),
          routeModelList(boundary.component_ids),
          routeModelList(boundary.blocked_numeric_component_ids),
          boundary.safe_use,
          boundary.next_action,
        ]);
  const routeCostDiagnosticRows = routeModel.diagnostic_cost_estimate_v0?.components.map((component) => [
    component.label,
    <span key="status" className={toneText(policyStatusTone(component.status))}>
      {policyStatusLabel(component.status)}
    </span>,
    component.venue_id,
    routeModelList(component.source_fields),
    routeModelValues(component.published_values),
    component.may_emit_component_bps ? "Display component only" : "No numeric bps",
    routeModelList(component.blocked_by),
    component.safe_use,
  ]) ?? [];

  return (
    <Shell>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.12em] text-cyan-300">Perp DEX</div>
            <h1 className="mt-1 text-2xl font-semibold text-white">{activeTab.title}</h1>
          </div>
          <div className="flex items-center gap-2">
            <SegmentedControl
              items={perpDexViews.map((item) => ({ label: item.label, href: item.href }))}
              active={activeTab.label}
            />
            <StatusBadge label={livePerpRows ? "Perp inputs live" : "Inputs pending"} tone={livePerpRows ? "positive" : "warning"} />
            <StatusBadge
              label={directVenueRows ? `${liveDexVenues}/4 normalized DEX live` : "DEX adapters pending"}
              tone={liveDexVenues ? "positive" : "warning"}
            />
          </div>
        </div>

        <TerminalPanel>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <SelectPill label="Universe" value={CORE_SYMBOLS_LABEL} />
            <SelectPill label="Perp Source" value="OKX USDT Swap" />
            <SelectPill label="Derivatives" value="Funding / OI / L/S" />
            <SelectPill
              label="DEX Venues"
              value={visibleVenueLabels.length ? visibleVenueLabels.join(" / ") : "Pending direct adapters"}
            />
            <SelectPill label="Storage" value="PostgreSQL" />
          </div>
        </TerminalPanel>

        <KpiStrip metrics={kpis} />

        {(activeView === "overview" || activeView === "venues") && (
          <TerminalPanel
            title="Perp DEX Source Status"
            caption="Compact source, enrichment and contract status for the current read-only research cockpit"
          >
            <TerminalTable
              columns={["Source", "Layer", "Status", "Rows", "Evidence", "Boundary", "Last Check"]}
              rows={sourceStatusRows.map(sourceStatusCells)}
            />
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "open-interest" || activeView === "liquidity") && (
          <TerminalPanel title="Perp Universe Readiness" caption="Live persisted streams currently available for presentation">
            <TerminalTable
              columns={["Asset", "Perp Close", "Funding", "Open Interest", "Basis", "Long Accounts", "Status"]}
              rows={matrix.rows.map(perpUniverseCells)}
            />
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues") && (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <TerminalPanel title="Venue Adapter Status" caption="Real provider status; direct DEX volume/OI pending">
              <TerminalTable columns={["Venue / Provider", "Status", "Scope"]} rows={adapterRows} />
              <div className="mt-3">
                <LinkButton href="/funding?view=perp-dex">Open Funding Matrix</LinkButton>
              </div>
            </TerminalPanel>

            <TerminalPanel title="Provider Health" caption="Current live providers backing this screen">
              {providerRows.length > 0 ? (
                <TerminalTable columns={["Provider", "Status", "Last Sync", "Last Error"]} rows={providerRows} />
              ) : (
                <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                  No provider health data returned by backend.
                </div>
              )}
            </TerminalPanel>
          </div>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "open-interest" || activeView === "liquidity") && (
          <TerminalPanel
            title="Direct Perp DEX Market Snapshots"
            caption="Hyperliquid + dYdX + Lighter + Aster normalized snapshots; GMX raw fixed-point fields; read-only, no execution path"
          >
            {dexMarkets.length > 0 ? (
              <TerminalTable
                columns={["Venue", "Market", "Mark", "Funding", "Open Interest", "24h Volume", "Max Lev", "Mode", "Status"]}
                rows={dexMarkets.map(venueMarketCells)}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Direct public Perp DEX market snapshots are not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "liquidity") && (
          <TerminalPanel
            title="Depth Diagnostics"
            caption="Display-only order book diagnostics from venues with sourced public depth fields"
          >
            {depthDiagnosticRows.length > 0 ? (
              <TerminalTable
                columns={["Venue", "Market", "Depth", "Best Bid / Ask", "Spread", "Top Bid Depth", "Top Ask Depth", "Safe Use"]}
                rows={depthDiagnosticRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                No sourced public depth diagnostics are available from direct venues right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "open-interest" || activeView === "liquidity") && (
          <TerminalPanel
            title="CoinGlass Perp DEX Enrichment"
            caption="Third-party coin-market aggregates for DEX-like venues; research-only, no ranking or execution"
          >
            {coinglassMarkets.length > 0 ? (
              <TerminalTable
                columns={["Venue", "Symbol", "Price", "Funding", "Open Interest", "L/S", "24h Liq.", "Use"]}
                rows={coinglassMarkets.map(coinGlassMarketCells)}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                CoinGlass Perp DEX enrichment is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues") && (
          <TerminalPanel
            title="CoinGlass Perp DEX Coverage"
            caption="Coverage hints for choosing the next direct adapter; not a liquidity ranking"
          >
            {coinglassCoverageRows.length > 0 ? (
              <TerminalTable
                columns={["Venue", "Status", "Rows", "Symbols", "Fields", "Next Action"]}
                rows={coinglassCoverageRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                CoinGlass Perp DEX coverage summary is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route & Execution Policy"
            caption="Machine-readable backend policy for current Perp DEX boundaries"
          >
            {routePolicyRows.length > 0 ? (
              <TerminalTable columns={["Capability", "Status", "Scope", "Next Action"]} rows={routePolicyRows} />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route policy is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Safety Guardrails"
            caption="Top-level safety flags that must stay locked before route scoring or execution"
          >
            {routeSafetyGuardrailRows.length > 0 ? (
              <TerminalTable columns={["Scope", "Guardrail", "Actual", "Expected", "Reason"]} rows={routeSafetyGuardrailRows} />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route safety guardrails are not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Blockers Matrix"
            caption="Structured blockers for route pricing, ranking and execution"
          >
            {routeBlockerRows.length > 0 ? (
              <TerminalTable
                columns={["Scope", "Blocker", "Reason", "Missing Inputs", "Blocked By", "Safe Use", "Next Action"]}
                rows={routeBlockerRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route blockers are not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Output Policy"
            caption="Allowed display outputs and blocked production outputs for the current route model"
          >
            {routeModelOutputPolicyRows.length > 0 ? (
              <TerminalTable columns={["Capability", "Status", "Expected", "Safe Use"]} rows={routeModelOutputPolicyRows} />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route output policy is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Model Blockers"
            caption="Model-level inputs that keep numeric cost, ranking and execution disabled"
          >
            {routeModelBlockerRows.length > 0 ? (
              <TerminalTable
                columns={["Blocker", "Reason", "Missing Inputs", "Blocked By", "Safe Use"]}
                rows={routeModelBlockerRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route model blockers are not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Required Inputs"
            caption="Inputs that must be sourced before numeric route cost, ranking or execution can be enabled"
          >
            {routeRequiredInputRows.length > 0 ? (
              <TerminalTable columns={["Input", "Status", "Key", "Reason"]} rows={routeRequiredInputRows} />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route required inputs are not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Cost Model v0"
            caption="Read-only input checklist; numeric cost estimates, ranking and execution remain disabled"
          >
            {routeModelComponentRows.length > 0 ? (
              <div className="space-y-4">
                <TerminalTable
                  columns={["Component", "Status", "Required Inputs", "Blocked Reason"]}
                  rows={routeModelComponentRows}
                />
                <TerminalTable columns={["Formula", "Skeleton"]} rows={routeFormulaRows} />
              </div>
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route cost model is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Model Venue Inputs"
            caption="Venue readiness for route-level fees, slippage, price impact and carry inputs"
          >
            {routeModelVenueRows.length > 0 ? (
              <TerminalTable
                columns={["Venue", "Status", "Source Semantics", "Available Inputs", "Missing Inputs", "Safe Use"]}
                rows={routeModelVenueRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Venue route model inputs are not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Components Summary"
            caption="High-level boundary for component diagnostics before any total route-cost estimate"
          >
            {routeDiagnosticComponentSummaryRows.length > 0 ? (
              <TerminalTable columns={["Metric", "Value", "Boundary", "Safe Use"]} rows={routeDiagnosticComponentSummaryRows} />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic component summary is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Venue Breakdown"
            caption="Venue-level component readiness; still no route cost, ranking or execution"
          >
            {routeDiagnosticVenueBreakdownRows.length > 0 ? (
              <TerminalTable
                columns={["Venue", "Components", "Display", "Blocked Numeric", "Sourced", "Component IDs", "Blocked IDs", "Safe Use"]}
                rows={routeDiagnosticVenueBreakdownRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic venue breakdown is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Readiness Rollup"
            caption="Compact fee/depth/carry/risk readiness; still no total cost bps, ranking or execution"
          >
            {routeDiagnosticReadinessRollupRows.length > 0 ? (
              <TerminalTable
                columns={["Category", "Status", "Required Inputs", "Components", "Sourced", "Display IDs", "Blocked IDs", "Next Action"]}
                rows={routeDiagnosticReadinessRollupRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic readiness rollup is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Depth/Staleness Policy"
            caption="Depth freshness and stale-depth gates before any slippage bps"
          >
            {routeDiagnosticDepthPolicyRows.length > 0 ? (
              <TerminalTable
                columns={["Venue", "Scope", "Endpoint", "Status", "Source Fields", "Required Policy Inputs", "Blocked By", "Slippage", "Next Action"]}
                rows={routeDiagnosticDepthPolicyRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic depth/staleness policy checklist is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Policy Inputs"
            caption="Required policy inputs behind depth freshness and stale-depth gates"
          >
            {routeDiagnosticRequiredPolicyInputRows.length > 0 ? (
              <TerminalTable
                columns={["Policy Input", "Status", "Policies", "Policy IDs", "Components", "Venues", "Endpoints", "Blocked By", "Slippage", "Next Action"]}
                rows={routeDiagnosticRequiredPolicyInputRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic policy input breakdown is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Next Actions"
            caption="Grouped research actions before any route cost, ranking or execution"
          >
            {routeDiagnosticNextActionRows.length > 0 ? (
              <TerminalTable
                columns={[
                  "Next Action",
                  "Status",
                  "Sources",
                  "Source Types",
                  "Required Inputs",
                  "Policy Inputs",
                  "Components",
                  "Venues",
                  "Total",
                  "Safe Use",
                ]}
                rows={routeDiagnosticNextActionRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic next-action breakdown is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Blocker Breakdown"
            caption="Repeated component blockers across venues; still no route cost, ranking or execution"
          >
            {routeDiagnosticBlockerBreakdownRows.length > 0 ? (
              <TerminalTable
                columns={["Blocker", "Components", "Venues", "Component IDs", "Display IDs", "Blocked Numeric IDs", "Total", "Safe Use"]}
                rows={routeDiagnosticBlockerBreakdownRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic blocker breakdown is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Required Input Breakdown"
            caption="Required-input coverage across diagnostic components; still no route cost, ranking or execution"
          >
            {routeDiagnosticRequiredInputBreakdownRows.length > 0 ? (
              <TerminalTable
                columns={["Input", "Status", "Components", "Venues", "Component IDs", "Display IDs", "Blocked IDs", "Next Action"]}
                rows={routeDiagnosticRequiredInputBreakdownRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic required input breakdown is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Source Fields Breakdown"
            caption="Sourced display fields by component and required input; not route-cost input readiness"
          >
            {routeDiagnosticSourceFieldBreakdownRows.length > 0 ? (
              <TerminalTable
                columns={["Source Field", "Status", "Components", "Venues", "Required Inputs", "Component IDs", "Blocked IDs", "Safe Use"]}
                rows={routeDiagnosticSourceFieldBreakdownRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic source fields breakdown is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Source Input Actions"
            caption="Sourced display fields mapped to required inputs and next actions; still not route-ready"
          >
            {routeDiagnosticSourceInputActionCoverageRows.length > 0 ? (
              <TerminalTable
                columns={["Source Field", "Status", "Components", "Venues", "Required Inputs", "Next Actions", "Blocked IDs", "Total", "Safe Use"]}
                rows={routeDiagnosticSourceInputActionCoverageRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic source input action coverage is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Evidence Checklist"
            caption="Route-ready evidence gates before cost bps, ranking or execution decisions"
          >
            {routeDiagnosticRouteReadyEvidenceRows.length > 0 ? (
              <TerminalTable
                columns={[
                  "Gate",
                  "Status",
                  "Evidence",
                  "Required Inputs",
                  "Policy Inputs",
                  "Source Fields",
                  "Blocked Outputs",
                  "Cost / Rank / Exec",
                  "Next Action",
                ]}
                rows={routeDiagnosticRouteReadyEvidenceRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic evidence checklist is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Venue Evidence Status"
            caption="Venue-specific evidence gaps separated from cross-venue route gates"
          >
            {routeDiagnosticVenueEvidenceRows.length > 0 ? (
              <TerminalTable
                columns={[
                  "Venue",
                  "Scope",
                  "Status",
                  "Evidence",
                  "Venue Gates",
                  "Cross Gates",
                  "Required Inputs",
                  "Policy Inputs",
                  "Evidence Fields",
                  "Blocked Outputs",
                  "Cost / Rank / Exec",
                  "Next Action",
                ]}
                rows={routeDiagnosticVenueEvidenceRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic venue evidence status is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="GMX Rate Mapping Review"
            caption="Read-only mapping review over rate relation/source-field diagnostics; no carry conversion"
          >
            {gmxRateMappingReviewRows.length > 0 ? (
              <TerminalTable
                columns={[
                  "Review",
                  "Status",
                  "Evidence",
                  "Diagnostic Fields",
                  "Required Source Inputs",
                  "Fixture Coverage",
                  "Blocked By",
                  "Carry / Cost / Rank / Exec",
                  "Next Action",
                ]}
                rows={gmxRateMappingReviewRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                GMX rate mapping review is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="GMX Rate Mapping Blockers"
            caption="Repeated blockers across GMX source relation, live mapping, helper inputs and carry boundary"
          >
            {gmxRateMappingBlockerRows.length > 0 ? (
              <TerminalTable
                columns={[
                  "Blocker",
                  "Reviews",
                  "Review IDs",
                  "Statuses",
                  "Required Source Inputs",
                  "Fixture Coverage",
                  "Blocked Outputs",
                  "Carry / Cost / Rank / Exec",
                  "Next Action",
                ]}
                rows={gmxRateMappingBlockerRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                GMX rate mapping blocker breakdown is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="GMX Rate Fixture Readiness"
            caption="Side-aware fixture coverage before any GMX carry conversion or route-cost diagnostics"
          >
            {gmxRateFixtureReadinessRows.length > 0 ? (
              <TerminalTable
                columns={[
                  "Case",
                  "Status",
                  "Evidence",
                  "Required Source Inputs",
                  "Diagnostic Fields",
                  "Fixture Coverage",
                  "Blocked By",
                  "Carry",
                  "Expectation Notes",
                  "Next Action",
                ]}
                rows={gmxRateFixtureReadinessRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                GMX rate fixture readiness matrix is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="GMX Rate Side-aware Fixtures"
            caption="Expected paying/receiving direction cases required before GMX carry bps"
          >
            {gmxRateSideAwareFixtureExpectationRows.length > 0 ? (
              <TerminalTable
                columns={[
                  "Case",
                  "Status",
                  "Position Side",
                  "longsPayShorts",
                  "Expected Direction",
                  "Required Source Inputs",
                  "Fixture Coverage",
                  "Blocked By",
                  "Carry",
                  "Next Action",
                ]}
                rows={gmxRateSideAwareFixtureExpectationRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                GMX rate side-aware fixture expectations are not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="GMX Rate Mapping Decision Checklist"
            caption="Read-only checks required before any diagnostic GMX carry bps decision"
          >
            {gmxRateMappingDecisionRows.length > 0 ? (
              <TerminalTable
                columns={[
                  "Check",
                  "Status",
                  "Required Source Inputs",
                  "Fixture Cases",
                  "Expectation IDs",
                  "Review IDs",
                  "Manual Approval",
                  "Blocked Outputs",
                  "Carry / Cost / Rank / Exec",
                  "Next Action",
                ]}
                rows={gmxRateMappingDecisionRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                GMX rate mapping decision checklist is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="GMX Rate Carry Readiness Summary"
            caption="Compact readiness summary for GMX carry inputs before any diagnostic carry bps"
          >
            {gmxRateCarryReadinessSummaryRows.length > 0 ? (
              <TerminalTable
                columns={["Area", "Status", "Inputs / Values", "Required Checks / Fixtures", "Manual Approvals", "Boundary"]}
                rows={gmxRateCarryReadinessSummaryRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                GMX rate carry readiness summary is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="GMX Rate Carry Input Checklist"
            caption="Holding period, notional, sign convention and display policy gates before carry bps"
          >
            {gmxRateCarryInputRows.length > 0 ? (
              <TerminalTable
                columns={[
                  "Input",
                  "Status",
                  "Input Type",
                  "Required Source Inputs",
                  "Fixture Cases",
                  "Expectation IDs",
                  "Decision Checks",
                  "Manual Approval",
                  "Blocked By",
                  "Carry / Cost / Rank / Exec",
                  "Next Action",
                ]}
                rows={gmxRateCarryInputRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                GMX rate carry input checklist is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="GMX Rate Carry Evidence Summary"
            caption="Source, fixture, runtime and manual approval evidence required before diagnostic carry bps"
          >
            {gmxRateCarrySourceEvidenceSummaryRows.length > 0 ? (
              <TerminalTable
                columns={["Area", "Status", "Evidence / Values", "Types / Fixtures", "Inputs / Checks", "Boundary"]}
                rows={gmxRateCarrySourceEvidenceSummaryRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                GMX rate carry evidence summary is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="GMX Rate Carry Evidence Checklist"
            caption="Evidence artifacts that must close each GMX carry input before carry conversion"
          >
            {gmxRateCarrySourceEvidenceRows.length > 0 ? (
              <TerminalTable
                columns={[
                  "Evidence",
                  "Status",
                  "Type",
                  "Related Inputs",
                  "Source Inputs",
                  "Fixture Cases",
                  "Expectation IDs",
                  "Decision Checks",
                  "Manual Approvals",
                  "Blocked By",
                  "Carry / Cost / Rank / Exec",
                  "Next Action",
                ]}
                rows={gmxRateCarrySourceEvidenceRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                GMX rate carry evidence checklist is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="GMX Rate Live Helper Source Review"
            caption="Live /markets/info helper-source review before any GMX carry conversion"
          >
            {gmxRateLiveHelperSourceSummaryRows.length > 0 || gmxRateLiveHelperSourceRows.length > 0 ? (
              <div className="space-y-4">
                {gmxRateLiveHelperSourceSummaryRows.length > 0 && (
                  <TerminalTable
                    columns={["Area", "Status", "Reviews / Values", "Observed Fields", "Missing Inputs", "Boundary"]}
                    rows={gmxRateLiveHelperSourceSummaryRows}
                  />
                )}
                {gmxRateLiveHelperSourceRows.length > 0 && (
                  <TerminalTable
                    columns={[
                      "Review",
                      "Status",
                      "Scope",
                      "Evidence",
                      "Observed Fields",
                      "Required Inputs",
                      "Missing Inputs",
                      "Fixture Cases",
                      "Expectations",
                      "Manual Approval",
                      "Blocked By",
                      "Carry / Cost / Rank / Exec",
                      "Next Action",
                    ]}
                    rows={gmxRateLiveHelperSourceRows}
                  />
                )}
              </div>
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                GMX rate live helper source review is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="GMX Rate Helper Source Follow-up"
            caption="Missing helper inputs and manual approvals still blocking GMX carry conversion"
          >
            {gmxRateHelperSourceFollowUpSummaryRows.length > 0 || gmxRateHelperSourceFollowUpRows.length > 0 ? (
              <div className="space-y-4">
                {gmxRateHelperSourceFollowUpSummaryRows.length > 0 && (
                  <TerminalTable
                    columns={["Area", "Status", "Count / Inputs", "Missing / Reviews", "Manual / Checks", "Boundary"]}
                    rows={gmxRateHelperSourceFollowUpSummaryRows}
                  />
                )}
                {gmxRateHelperSourceFollowUpRows.length > 0 && (
                  <TerminalTable
                    columns={[
                      "Follow-up",
                      "Status",
                      "Type",
                      "Related Inputs",
                      "Related Reviews",
                      "Missing Inputs",
                      "Fixture Cases",
                      "Expectations",
                      "Decision Checks",
                      "Manual Approvals",
                      "Blocked By",
                      "Carry / Cost / Rank / Exec",
                      "Next Action",
                    ]}
                    rows={gmxRateHelperSourceFollowUpRows}
                  />
                )}
              </div>
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                GMX rate helper source follow-up is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Diagnostic Safe Use Breakdown"
            caption="Boundary text grouped by components, so display diagnostics do not drift into route signals"
          >
            {routeDiagnosticSafeUseBreakdownRows.length > 0 ? (
              <TerminalTable
                columns={["Status", "Components", "Venues", "Required Inputs", "Component IDs", "Blocked IDs", "Safe Use", "Next Action"]}
                rows={routeDiagnosticSafeUseBreakdownRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route diagnostic safe use breakdown is not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "venues" || activeView === "opportunities") && (
          <TerminalPanel
            title="Route Cost Diagnostics v0"
            caption="Component-level diagnostics only; total route cost, ranking and execution remain disabled"
          >
            {routeCostDiagnosticRows.length > 0 ? (
              <TerminalTable
                columns={["Component", "Status", "Venue", "Source Fields", "Published Values", "Numeric Use", "Blocked By", "Safe Use"]}
                rows={routeCostDiagnosticRows}
              />
            ) : (
              <div className="rounded-md border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                Route cost diagnostics are not available from the backend right now.
              </div>
            )}
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "open-interest" || activeView === "liquidity") && (
          <TerminalPanel title="Persisted Perp Data Coverage" caption="Rows stored in PostgreSQL by stream">
            <TerminalTable columns={["Stream", "Rows", "Source", "Status"]} rows={dataCoverageRows} />
          </TerminalPanel>
        )}

        {(activeView === "overview" || activeView === "opportunities") && (
          <TerminalPanel
            title="Perp Research Candidates"
            caption="Basis/funding candidates from persisted streams; DEX-specific scoring waits for direct venue adapters"
          >
            <TerminalTable
              columns={["Asset", "Type", "Long Leg", "Short Leg", "Basis Edge", "Funding", "Open Interest", "Risk Note"]}
              rows={scanner.opportunities.slice(0, 5).map(opportunityCells)}
            />
          </TerminalPanel>
        )}

        {activeView === "opportunities" && (
          <TerminalPanel title="Execution Boundary" caption={routePolicy.status === "research_only" ? "Research-only state" : "Policy unavailable"}>
            <div className="rounded-md border border-amber-300/20 bg-amber-300/10 p-4 text-sm leading-6 text-amber-100">
              These rows are read-only research candidates. Direct DEX execution, venue fees, slippage, borrow costs and route-level risk checks are not connected yet.
            </div>
          </TerminalPanel>
        )}
      </div>
    </Shell>
  );
}
