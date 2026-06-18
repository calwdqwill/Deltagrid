import { fetchServerApi } from "@/lib/server-api";
import { KpiMetric, SeriesPoint } from "@/types/terminal";
import { DataHealthPayload } from "./live-data";

const CORE_SYMBOLS = ["BTC", "ETH", "SOL"] as const;
const CANDIDATE_SYMBOLS = ["HYPE", "XRP", "DOGE", "ADA", "LINK"] as const;
const TRACKED_SYMBOLS = [...CORE_SYMBOLS, ...CANDIDATE_SYMBOLS] as const;
const CORE_SYMBOLS_LABEL = CORE_SYMBOLS.join(" / ");
const CANDIDATE_SYMBOLS_LABEL = CANDIDATE_SYMBOLS.join(" / ");
const TRACKED_SYMBOLS_LABEL = TRACKED_SYMBOLS.join(" / ");
const DEFAULT_EXCHANGE = "okx";
const DEFAULT_EXCHANGE_LABEL = "OKX";
const CHART_INTERVALS = ["1m", "5m", "1h"] as const;
const CHART_RANGES = ["2h", "8h", "24h", "7d"] as const;

export {
  CORE_SYMBOLS,
  CORE_SYMBOLS_LABEL,
  CANDIDATE_SYMBOLS,
  CANDIDATE_SYMBOLS_LABEL,
  TRACKED_SYMBOLS,
  TRACKED_SYMBOLS_LABEL,
  CHART_INTERVALS,
  CHART_RANGES,
};

export type TrackedSymbol = (typeof TRACKED_SYMBOLS)[number];
export type ChartInterval = (typeof CHART_INTERVALS)[number];
export type ChartRange = (typeof CHART_RANGES)[number];

type StatusTone = "positive" | "warning";

export function symbolScopeLabel(symbol: string): "Core" | "Preview Candidate" {
  return CORE_SYMBOLS.includes(symbol.toUpperCase() as (typeof CORE_SYMBOLS)[number]) ? "Core" : "Preview Candidate";
}

interface OhlcvRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  interval: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume?: number | null;
  quote_volume?: number | null;
}

interface FundingRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  funding_rate: number | string | null;
  interval?: string | null;
}

interface OpenInterestRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  interval: string;
  oi_usd?: number | null;
  oi_coins?: number | null;
}

interface LongShortRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  interval: string;
  long_ratio?: number | null;
  short_ratio?: number | null;
  long_account_ratio?: number | null;
  short_account_ratio?: number | null;
}

interface BasisPremiumRow {
  id: string;
  timestamp: number;
  symbol: string;
  exchange: string;
  spot_price?: number | null;
  perp_price?: number | null;
  basis_pct?: number | null;
  premium_pct?: number | null;
}

interface LiquidationRow {
  timestamp: number;
  symbol: string;
  exchange: string;
  side: string;
  quantity?: number | null;
  price?: number | null;
  value_usd?: number | null;
}

export interface InteractiveCandle {
  timestamp: number;
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
  quoteVolume: number | null;
}

export interface LiveChartsWorkspace {
  symbol: string;
  exchange: string;
  exchangeLabel: string;
  interval: ChartInterval;
  range: ChartRange;
  rangeLabel: string;
  statusLabel: string;
  statusTone: StatusTone;
  freshnessLabel: string;
  freshnessTone: StatusTone;
  latestCandleIso: string;
  kpis: KpiMetric[];
  candles: InteractiveCandle[];
  priceSeries: SeriesPoint[];
  volumeSeries: SeriesPoint[];
  openInterestSeries: SeriesPoint[];
  basisSeries: SeriesPoint[];
  fundingSeries: SeriesPoint[];
  longRatioSeries: SeriesPoint[];
  sourceRows: Array<[string, string, string]>;
}

export interface LiveMatrixRow {
  asset: string;
  spotPrice: number | null;
  perpPrice: number | null;
  basisPct: number | null;
  fundingPct: number | null;
  openInterestUsd: number | null;
  longAccountRatio: number | null;
}

export interface LiveMarketMatrix {
  rows: LiveMatrixRow[];
  kpis: KpiMetric[];
  statusLabel: string;
  statusTone: StatusTone;
  sourceRows: Array<[string, string]>;
}

export interface LiveArbitrageOpportunity {
  id: string;
  type: "basis" | "funding_bias";
  asset: string;
  longLeg: string;
  shortLeg: string;
  edgePct: number;
  fundingPct: number | null;
  openInterestUsd: number | null;
  source: string;
  riskNote: string;
}

export interface LiveArbitrageScanner {
  opportunities: LiveArbitrageOpportunity[];
  kpis: KpiMetric[];
  statusLabel: string;
  statusTone: StatusTone;
}

export interface LivePerpDexVenueMarket {
  symbol: string;
  market: string;
  venue_id: string;
  venue_name: string;
  dex: string | null;
  status: "live" | "partial";
  provider_status?: string | null;
  normalization_status?: string | null;
  mark_price: number | null;
  mid_price: number | null;
  oracle_price: number | null;
  prev_day_price: number | null;
  funding_rate: number | null;
  funding_pct: number | null;
  open_interest_base: number | null;
  open_interest_usd: number | null;
  volume_24h_usd: number | null;
  volume_24h_base: number | null;
  premium: number | null;
  premium_pct: number | null;
  impact_bid_price: number | null;
  impact_ask_price: number | null;
  orderbook_depth_status?: string | null;
  orderbook_order_limit?: number | null;
  orderbook_bid_orders?: number | null;
  orderbook_ask_orders?: number | null;
  best_bid_price?: number | null;
  best_ask_price?: number | null;
  best_bid_size_base?: number | null;
  best_ask_size_base?: number | null;
  top_of_book_spread_bps?: number | null;
  bid_depth_top_orders_base?: number | null;
  ask_depth_top_orders_base?: number | null;
  bid_depth_top_orders_usd?: number | null;
  ask_depth_top_orders_usd?: number | null;
  orderbook_top_bid_orders?: Array<{ price: number; size_base: number; notional_usd: number }> | null;
  orderbook_top_ask_orders?: Array<{ price: number; size_base: number; notional_usd: number }> | null;
  orderbook_depth_safe_use?: string | null;
  only_isolated: boolean;
  max_leverage: number | null;
  sz_decimals: number | null;
  index_token_symbol?: string | null;
  index_token_decimals?: number | null;
  index_token_synthetic?: boolean | null;
  long_token_symbol?: string | null;
  long_token_decimals?: number | null;
  long_token_synthetic?: boolean | null;
  short_token_symbol?: string | null;
  short_token_decimals?: number | null;
  short_token_synthetic?: boolean | null;
  scale_validation_status?: string | null;
  scale_validation_reason?: string | null;
  pool_amount_long_token?: string | null;
  pool_amount_short_token?: string | null;
  token_amount_scale_status?: string | null;
  token_amount_scale_reason?: string | null;
  open_interest_long_usd_diagnostic?: string | null;
  open_interest_short_usd_diagnostic?: string | null;
  available_liquidity_long_usd_diagnostic?: string | null;
  available_liquidity_short_usd_diagnostic?: string | null;
  diagnostic_usd_scale_status?: string | null;
  diagnostic_usd_scale_reason?: string | null;
  diagnostic_usd_scale_decimals?: number | null;
  diagnostic_usd_scale_source?: string | null;
  rate_semantics_status?: string | null;
  rate_semantics_reason?: string | null;
  rate_semantics_period?: string | null;
  rate_semantics_source?: string | null;
  rate_relation_diagnostics?: Record<string, Record<string, string | null>>;
  long_short_ratio_1h?: number | null;
  long_short_ratio_24h?: number | null;
  long_liquidation_usd_24h?: number | null;
  short_liquidation_usd_24h?: number | null;
  liquidation_usd_24h?: number | null;
  open_interest_change_percent_24h?: number | null;
  volume_change_percent_24h?: number | null;
  source_endpoint?: string | null;
  source_exchange?: string | null;
  resolution_action?: string | null;
  resolution_reason?: string | null;
  fetched_at: string;
}

export interface LivePerpDexVenueSnapshot {
  venue_id: string;
  venue_name: string;
  source: string;
  status: "live" | "partial" | "empty" | "unavailable";
  dex: string | null;
  requested_symbols: string[];
  requested_exchanges?: string[];
  candidate_exchanges?: string[];
  markets: LivePerpDexVenueMarket[];
  fetched_at: string | null;
  read_only: boolean;
  execution_enabled: boolean;
  ranking_enabled?: boolean;
  production_signal_enabled?: boolean;
  normalization_status?: string | null;
  scale_validation_status?: string | null;
  token_amount_scale_status?: string | null;
  diagnostic_usd_scale_status?: string | null;
  rate_semantics_status?: string | null;
  coverage_summary?: {
    requested_symbols: string[];
    requested_exchanges: string[];
    total_rows: number;
    exchanges_with_matches: number;
    field_groups: string[];
    field_totals: Record<string, number>;
    direct_adapter_candidate_hints: string[];
    selection_policy: string;
    by_exchange: Record<
      string,
      {
        status: string;
        requested_rows: number;
        matched_rows: number;
        matched_symbols: string[];
        missing_symbols: string[];
        available_field_groups: string[];
        field_coverage: Record<string, number>;
        route_input_status: string;
        next_action: string;
      }
    >;
  };
  reason?: string;
}

export interface LivePerpDexRouteCapability {
  id: string;
  label: string;
  status: "partial_ready" | "blocked";
  scope: string;
  allowed: boolean;
  next_action: string;
}

export interface LivePerpDexRouteBlocker {
  id: string;
  severity: "blocker";
  scope: string;
  reason: string;
  missing_inputs?: string[];
  blocked_by?: string[];
  safe_use?: string;
  next_action: string;
}

export interface LivePerpDexRouteConstraints {
  status: "research_only" | "unavailable";
  read_only: boolean;
  execution_enabled: boolean;
  production_liquidity_signal: boolean;
  normalized_snapshot_venues: string[];
  raw_snapshot_venues: string[];
  capabilities: LivePerpDexRouteCapability[];
  blockers: LivePerpDexRouteBlocker[];
  ui_policy: {
    may_show_market_rows: boolean;
    may_show_research_candidates: boolean;
    may_rank_by_liquidity: boolean;
    may_submit_orders: boolean;
  };
  reason?: string;
}

export interface LivePerpDexRouteModelComponent {
  id: string;
  label: string;
  status: string;
  required_inputs: string[];
  blocked_reason: string;
}

export interface LivePerpDexRouteModelVenue {
  venue_id: string;
  venue_name: string;
  status: string;
  source_semantics?: string;
  available_inputs: string[];
  missing_inputs: string[];
  cost_input_status?: Record<string, string>;
  safe_use: string;
}

export interface LivePerpDexRouteModelRequiredInput {
  id: string;
  label: string;
  reason: string;
}

export interface LivePerpDexRouteModelBlocker {
  id: string;
  severity: string;
  reason: string;
  missing_inputs?: string[];
  blocked_by?: string[];
  safe_use?: string;
}

export interface LivePerpDexRouteCostDiagnosticComponent {
  id: string;
  label: string;
  venue_id: string;
  status: string;
  source_fields: string[];
  published_values?: Record<string, string | number | boolean>;
  may_emit_component_bps: boolean;
  required_input_ids?: string[];
  blocked_by: string[];
  safe_use: string;
}

export interface LivePerpDexRouteCostDiagnosticVenueBreakdown {
  venue_id: string;
  venue_label: string;
  component_count: number;
  display_only_component_count: number;
  blocked_numeric_component_count: number;
  sourced_component_count: number;
  component_ids: string[];
  display_component_ids: string[];
  blocked_numeric_component_ids: string[];
  sourced_component_ids: string[];
  numeric_total_status: string;
  safe_use: string;
}

export interface LivePerpDexRouteCostDiagnosticBlockerBreakdown {
  blocker: string;
  component_count: number;
  component_ids: string[];
  venue_ids: string[];
  display_component_ids: string[];
  blocked_numeric_component_ids: string[];
  numeric_total_status: string;
  safe_use: string;
}

export interface LivePerpDexRouteCostDiagnosticRequiredInputBreakdown {
  input_id: string;
  input_label: string;
  status: string;
  reason: string;
  component_count: number;
  component_ids: string[];
  venue_ids: string[];
  display_component_ids: string[];
  blocked_numeric_component_ids: string[];
  sourced_component_ids: string[];
  numeric_total_status: string;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexRouteCostDiagnosticSourceFieldBreakdown {
  source_field: string;
  status: string;
  component_count: number;
  component_ids: string[];
  venue_ids: string[];
  required_input_ids: string[];
  display_component_ids: string[];
  blocked_numeric_component_ids: string[];
  numeric_total_status: string;
  safe_use: string;
}

export interface LivePerpDexRouteCostDiagnosticSafeUseBreakdown {
  safe_use: string;
  status: string;
  component_count: number;
  component_ids: string[];
  venue_ids: string[];
  required_input_ids: string[];
  display_component_ids: string[];
  blocked_numeric_component_ids: string[];
  numeric_total_status: string;
  next_action: string;
}

export interface LivePerpDexRouteCostDiagnosticReadinessRollup {
  category_id: string;
  category_label: string;
  status: string;
  required_input_ids: string[];
  component_count: number;
  sourced_component_count: number;
  display_component_ids: string[];
  blocked_numeric_component_ids: string[];
  numeric_total_status: string;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexRouteCostDiagnosticDepthPolicyChecklist {
  policy_id: string;
  venue_id: string;
  venue_label: string;
  component_id: string;
  depth_scope: string;
  source_endpoint: string;
  status: string;
  source_fields: string[];
  required_policy_inputs: string[];
  blocked_by: string[];
  may_emit_slippage_bps: boolean;
  numeric_total_status: string;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexRouteCostDiagnosticRequiredPolicyInputBreakdown {
  input_id: string;
  input_label: string;
  status: string;
  policy_count: number;
  policy_ids: string[];
  component_ids: string[];
  venue_ids: string[];
  source_endpoints: string[];
  blocked_by: string[];
  may_emit_slippage_bps: boolean;
  numeric_total_status: string;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexRouteCostDiagnosticNextActionBreakdown {
  action_id: string;
  next_action: string;
  status: string;
  source_count: number;
  source_types: string[];
  source_ids: string[];
  required_input_ids: string[];
  required_policy_inputs: string[];
  component_ids: string[];
  venue_ids: string[];
  policy_ids: string[];
  rollup_category_ids: string[];
  numeric_total_status: string;
  safe_use: string;
}

export interface LivePerpDexRouteCostDiagnosticSourceInputActionCoverage {
  coverage_id: string;
  source_field: string;
  status: string;
  component_count: number;
  component_ids: string[];
  venue_ids: string[];
  required_input_count: number;
  required_input_ids: string[];
  next_action_count: number;
  next_action_ids: string[];
  next_actions: string[];
  source_types: string[];
  display_component_ids: string[];
  blocked_numeric_component_ids: string[];
  numeric_total_status: string;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexRouteCostDiagnosticRouteReadyEvidenceChecklist {
  gate_id: string;
  gate_label: string;
  status: string;
  required_input_ids: string[];
  required_policy_inputs: string[];
  component_ids: string[];
  policy_ids: string[];
  source_field_ids: string[];
  blocked_outputs: string[];
  evidence_count: number;
  numeric_total_status: string;
  may_estimate_cost_bps: boolean;
  may_rank_routes: boolean;
  may_submit_orders: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexRouteCostDiagnosticVenueEvidenceStatus {
  venue_id: string;
  venue_label: string;
  venue_scope: string;
  status: string;
  venue_gate_ids: string[];
  cross_venue_gate_ids: string[];
  required_input_ids: string[];
  required_policy_inputs: string[];
  component_ids: string[];
  policy_ids: string[];
  source_field_ids: string[];
  diagnostic_field_ids: string[];
  fixture_coverage_ids: string[];
  blocked_outputs: string[];
  evidence_count: number;
  numeric_total_status: string;
  may_estimate_cost_bps: boolean;
  may_rank_routes: boolean;
  may_submit_orders: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateSemanticsFixtureCoverage {
  id: string;
  status: string;
  scope: string;
  assertion: string;
  safe_use: string;
}

export interface LivePerpDexGmxRateSemantics {
  status: string;
  mapping_review?: {
    status: string;
    source_confirmed: string[];
    source_inputs_required: string[];
    live_observed: string[];
    diagnostic_fields: string[];
    safe_use: string;
  };
  blocked_for_numeric_carry?: string[];
  fixture_coverage?: LivePerpDexGmxRateSemanticsFixtureCoverage[];
  next_action?: string;
}

export interface LivePerpDexGmxRateMappingReviewItem {
  review_id: string;
  review_label: string;
  status: string;
  evidence_count: number;
  diagnostic_field_ids: string[];
  source_inputs_required: string[];
  fixture_coverage_ids: string[];
  blocked_by: string[];
  blocked_outputs: string[];
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateMappingBlockerBreakdown {
  blocker_id: string;
  blocker: string;
  review_count: number;
  review_ids: string[];
  review_statuses: string[];
  source_inputs_required: string[];
  fixture_coverage_ids: string[];
  blocked_outputs: string[];
  may_emit_carry_bps: boolean;
  may_estimate_cost_bps: boolean;
  may_rank_routes: boolean;
  may_submit_orders: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateFixtureReadiness {
  case_id: string;
  case_label: string;
  status: string;
  evidence_count: number;
  diagnostic_field_ids: string[];
  source_inputs_required: string[];
  fixture_coverage_ids: string[];
  expectation_ids?: string[];
  expectation_notes?: string[];
  blocked_by: string[];
  blocked_outputs: string[];
  may_emit_carry_bps: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateSideAwareFixtureExpectation {
  expectation_id: string;
  case_id: string;
  case_label: string;
  status: string;
  position_side: string;
  longs_pay_shorts: boolean;
  expected_funding_direction: string;
  required_source_inputs: string[];
  fixture_coverage_ids: string[];
  blocked_by: string[];
  blocked_outputs: string[];
  may_emit_carry_bps: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateMappingDecisionCheck {
  check_id: string;
  check_label: string;
  status: string;
  required_source_inputs: string[];
  required_fixture_case_ids: string[];
  required_expectation_ids: string[];
  required_review_ids: string[];
  manual_approval_required: boolean;
  manual_approval_id: string;
  blocked_outputs: string[];
  may_emit_carry_bps: boolean;
  may_estimate_cost_bps: boolean;
  may_rank_routes: boolean;
  may_submit_orders: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateCarryReadinessSummary {
  status: string;
  input_count: number;
  blocked_input_count: number;
  manual_approval_count: number;
  required_source_inputs: string[];
  required_fixture_case_ids: string[];
  required_expectation_ids: string[];
  required_decision_check_ids: string[];
  required_manual_approval_ids: string[];
  blocked_outputs: string[];
  may_emit_carry_bps: boolean;
  may_estimate_cost_bps: boolean;
  may_rank_routes: boolean;
  may_submit_orders: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateCarryInputCheck {
  input_id: string;
  input_label: string;
  status: string;
  input_type: string;
  required_source_inputs: string[];
  required_fixture_case_ids: string[];
  required_expectation_ids: string[];
  required_decision_check_ids: string[];
  manual_approval_required: boolean;
  manual_approval_id: string;
  blocked_by: string[];
  blocked_outputs: string[];
  may_emit_carry_bps: boolean;
  may_estimate_cost_bps: boolean;
  may_rank_routes: boolean;
  may_submit_orders: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateCarrySourceEvidenceSummary {
  status: string;
  evidence_count: number;
  blocked_evidence_count: number;
  evidence_ids: string[];
  evidence_type_ids: string[];
  input_ids: string[];
  required_source_inputs: string[];
  required_fixture_case_ids: string[];
  required_expectation_ids: string[];
  required_decision_check_ids: string[];
  required_manual_approval_ids: string[];
  blocked_outputs: string[];
  may_emit_carry_bps: boolean;
  may_estimate_cost_bps: boolean;
  may_rank_routes: boolean;
  may_submit_orders: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateCarrySourceEvidenceCheck {
  evidence_id: string;
  evidence_label: string;
  evidence_type: string;
  status: string;
  related_input_ids: string[];
  required_source_inputs: string[];
  required_fixture_case_ids: string[];
  required_expectation_ids: string[];
  required_decision_check_ids: string[];
  required_manual_approval_ids: string[];
  blocked_by: string[];
  blocked_outputs: string[];
  may_emit_carry_bps: boolean;
  may_estimate_cost_bps: boolean;
  may_rank_routes: boolean;
  may_submit_orders: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateLiveHelperSourceSummary {
  status: string;
  review_count: number;
  blocked_review_count: number;
  review_ids: string[];
  review_statuses: string[];
  observed_source_fields: string[];
  required_source_inputs: string[];
  present_source_inputs: string[];
  missing_source_inputs: string[];
  diagnostic_field_ids: string[];
  fixture_case_ids: string[];
  expectation_ids: string[];
  manual_approval_ids: string[];
  blocked_outputs: string[];
  may_emit_carry_bps: boolean;
  may_estimate_cost_bps: boolean;
  may_rank_routes: boolean;
  may_submit_orders: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateLiveHelperSourceReview {
  review_id: string;
  review_label: string;
  status: string;
  source_scope: string;
  evidence_count: number;
  observed_source_fields: string[];
  required_source_inputs: string[];
  present_source_inputs: string[];
  missing_source_inputs: string[];
  diagnostic_field_ids: string[];
  fixture_case_ids: string[];
  expectation_ids: string[];
  manual_approval_required: boolean;
  manual_approval_id: string;
  blocked_by: string[];
  blocked_outputs: string[];
  may_emit_carry_bps: boolean;
  may_estimate_cost_bps: boolean;
  may_rank_routes: boolean;
  may_submit_orders: boolean;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexGmxRateMappingReview {
  status: string;
  read_only: boolean;
  source_relation_status: string;
  live_mapping_status: string;
  source_confirmed_count: number;
  live_observed_count: number;
  fixture_coverage_count: number;
  diagnostic_field_ids: string[];
  source_inputs_required: string[];
  fixture_coverage_ids: string[];
  blocked_outputs: string[];
  may_emit_carry_bps: boolean;
  may_estimate_cost_bps: boolean;
  may_rank_routes: boolean;
  may_submit_orders: boolean;
  safe_use: string;
  next_action: string;
  review_items: LivePerpDexGmxRateMappingReviewItem[];
  blocker_breakdown?: LivePerpDexGmxRateMappingBlockerBreakdown[];
  fixture_readiness_matrix?: LivePerpDexGmxRateFixtureReadiness[];
  side_aware_fixture_expectations?: LivePerpDexGmxRateSideAwareFixtureExpectation[];
  mapping_decision_checklist?: LivePerpDexGmxRateMappingDecisionCheck[];
  carry_readiness_summary?: LivePerpDexGmxRateCarryReadinessSummary;
  carry_input_checklist?: LivePerpDexGmxRateCarryInputCheck[];
  carry_source_evidence_summary?: LivePerpDexGmxRateCarrySourceEvidenceSummary;
  carry_source_evidence_checklist?: LivePerpDexGmxRateCarrySourceEvidenceCheck[];
  live_helper_source_summary?: LivePerpDexGmxRateLiveHelperSourceSummary;
  live_helper_source_checklist?: LivePerpDexGmxRateLiveHelperSourceReview[];
}

export interface LivePerpDexRouteCostDiagnosticSummary {
  status: string;
  boundary: string;
  component_count: number;
  display_only_component_count: number;
  blocked_numeric_component_count: number;
  sourced_component_count: number;
  component_ids: string[];
  display_component_ids: string[];
  blocked_numeric_component_ids: string[];
  sourced_component_ids: string[];
  venue_breakdown?: LivePerpDexRouteCostDiagnosticVenueBreakdown[];
  blocker_breakdown?: LivePerpDexRouteCostDiagnosticBlockerBreakdown[];
  required_input_breakdown?: LivePerpDexRouteCostDiagnosticRequiredInputBreakdown[];
  source_field_breakdown?: LivePerpDexRouteCostDiagnosticSourceFieldBreakdown[];
  safe_use_breakdown?: LivePerpDexRouteCostDiagnosticSafeUseBreakdown[];
  readiness_rollup?: LivePerpDexRouteCostDiagnosticReadinessRollup[];
  depth_staleness_policy_checklist?: LivePerpDexRouteCostDiagnosticDepthPolicyChecklist[];
  required_policy_input_breakdown?: LivePerpDexRouteCostDiagnosticRequiredPolicyInputBreakdown[];
  next_action_breakdown?: LivePerpDexRouteCostDiagnosticNextActionBreakdown[];
  source_input_action_coverage?: LivePerpDexRouteCostDiagnosticSourceInputActionCoverage[];
  route_ready_evidence_checklist?: LivePerpDexRouteCostDiagnosticRouteReadyEvidenceChecklist[];
  venue_evidence_status?: LivePerpDexRouteCostDiagnosticVenueEvidenceStatus[];
  may_emit_numeric_total_bps: boolean;
  numeric_total_status: string;
  safe_use: string;
  next_action: string;
}

export interface LivePerpDexRouteCostDiagnostics {
  status: string;
  read_only: boolean;
  may_emit_numeric_total_bps: boolean;
  safe_use: string;
  components: LivePerpDexRouteCostDiagnosticComponent[];
  summary?: LivePerpDexRouteCostDiagnosticSummary;
  next_action: string;
}

export interface LivePerpDexRouteModel {
  version: string;
  status: "inputs_required" | "unavailable";
  read_only: boolean;
  execution_enabled: boolean;
  ranking_enabled: boolean;
  production_signal_enabled: boolean;
  model_scope: string;
  supported_venues: string[];
  model_components: LivePerpDexRouteModelComponent[];
  venue_readiness: LivePerpDexRouteModelVenue[];
  required_inputs: LivePerpDexRouteModelRequiredInput[];
  formula_skeleton: Record<string, string>;
  diagnostic_cost_estimate_v0?: LivePerpDexRouteCostDiagnostics;
  gmx_rate_semantics?: LivePerpDexGmxRateSemantics;
  gmx_rate_mapping_review_v0?: LivePerpDexGmxRateMappingReview;
  output_policy: {
    may_show_checklist: boolean;
    may_show_formula_skeleton: boolean;
    may_show_diagnostic_cost_components?: boolean;
    may_estimate_cost_bps: boolean;
    may_rank_routes: boolean;
    may_submit_orders: boolean;
  };
  blockers: LivePerpDexRouteModelBlocker[];
  next_action: string;
  reason?: string;
}

export interface LiveStrategyReadiness {
  kpis: KpiMetric[];
  priceSeries: SeriesPoint[];
  fundingSeries: SeriesPoint[];
  readinessRows: Array<[string, string, string]>;
  statusLabel: string;
  statusTone: StatusTone;
}

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function latest<T extends { timestamp: number }>(rows: T[]): T | null {
  if (!rows.length) return null;
  return rows.reduce((best, row) => (row.timestamp > best.timestamp ? row : best), rows[0]);
}

function formatRows(value?: number): string {
  return (value ?? 0).toLocaleString("en-US");
}

function formatCompactCurrency(value: number | null): string {
  if (value === null) return "No data";
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(2)}T`;
  if (abs >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `$${(value / 1_000).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

function formatPercent(value: number | null, digits = 3): string {
  if (value === null) return "No data";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

function pointLabel(timestamp: number): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return String(timestamp);
  return date.toISOString().slice(11, 16);
}

function intervalMs(interval: ChartInterval): number {
  if (interval === "5m") return 5 * 60 * 1000;
  if (interval === "1h") return 60 * 60 * 1000;
  return 60 * 1000;
}

function rangeMs(range: ChartRange): number {
  if (range === "2h") return 2 * 60 * 60 * 1000;
  if (range === "8h") return 8 * 60 * 60 * 1000;
  if (range === "7d") return 7 * 24 * 60 * 60 * 1000;
  return 24 * 60 * 60 * 1000;
}

function rangeLabel(range: ChartRange): string {
  if (range === "2h") return "2 hours";
  if (range === "8h") return "8 hours";
  if (range === "7d") return "7 days";
  return "24 hours";
}

function timestampIso(timestamp?: number | null): string {
  if (!timestamp) return "No candle";
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return "Invalid timestamp";
  return date.toISOString().replace(".000Z", "Z");
}

function freshnessTone(status?: string): StatusTone {
  return status === "fresh" ? "positive" : "warning";
}

function rowsToSeries<T extends { timestamp: number }>(
  rows: T[],
  valueSelector: (row: T) => number | null,
  maxPoints = 240
): SeriesPoint[] {
  return rows
    .slice(-maxPoints)
    .map((row) => ({ label: pointLabel(row.timestamp), value: valueSelector(row) }))
    .filter((point): point is SeriesPoint => point.value !== null);
}

function fundingPercent(row: FundingRow | null): number | null {
  const rate = toNumber(row?.funding_rate);
  return rate === null ? null : rate * 100;
}

function longAccountPercent(row: LongShortRow | null): number | null {
  const direct = toNumber(row?.long_account_ratio);
  if (direct !== null) return direct * 100;
  const fallback = toNumber(row?.long_ratio);
  return fallback === null ? null : fallback * 100;
}

async function fetchRows<T>(path: string): Promise<T[]> {
  const response = await fetchServerApi<T[]>(path);
  return response?.success ? response.data : [];
}

export async function getLiveHyperliquidMarkets(
  symbols: readonly string[] = CORE_SYMBOLS
): Promise<LivePerpDexVenueSnapshot> {
  const normalizedSymbols = symbols.map((symbol) => symbol.toUpperCase());
  const response = await fetchServerApi<LivePerpDexVenueSnapshot>(
    `/perp-dex/venues/hyperliquid/markets?symbols=${encodeURIComponent(normalizedSymbols.join(","))}`
  );

  if (response?.success) return response.data;

  return {
    venue_id: "hyperliquid",
    venue_name: "Hyperliquid",
    source: "hyperliquid_info_metaAndAssetCtxs",
    status: "unavailable",
    dex: null,
    requested_symbols: normalizedSymbols,
    markets: [],
    fetched_at: null,
    read_only: true,
    execution_enabled: false,
    reason: "backend_unavailable",
  };
}

export async function getLiveDydxMarkets(
  symbols: readonly string[] = CORE_SYMBOLS
): Promise<LivePerpDexVenueSnapshot> {
  const normalizedSymbols = symbols.map((symbol) => symbol.toUpperCase());
  const response = await fetchServerApi<LivePerpDexVenueSnapshot>(
    `/perp-dex/venues/dydx/markets?symbols=${encodeURIComponent(normalizedSymbols.join(","))}`
  );

  if (response?.success) return response.data;

  return {
    venue_id: "dydx",
    venue_name: "dYdX",
    source: "dydx_indexer_perpetualMarkets",
    status: "unavailable",
    dex: null,
    requested_symbols: normalizedSymbols,
    markets: [],
    fetched_at: null,
    read_only: true,
    execution_enabled: false,
    reason: "backend_unavailable",
  };
}

export async function getLiveLighterMarkets(
  symbols: readonly string[] = CORE_SYMBOLS
): Promise<LivePerpDexVenueSnapshot> {
  const normalizedSymbols = symbols.map((symbol) => symbol.toUpperCase());
  const response = await fetchServerApi<LivePerpDexVenueSnapshot>(
    `/perp-dex/venues/lighter/markets?symbols=${encodeURIComponent(normalizedSymbols.join(","))}`
  );

  if (response?.success) return response.data;

  return {
    venue_id: "lighter",
    venue_name: "Lighter",
    source: "lighter_order_books_details",
    status: "unavailable",
    dex: null,
    requested_symbols: normalizedSymbols,
    markets: [],
    fetched_at: null,
    read_only: true,
    execution_enabled: false,
    normalization_status: "lighter_public_market_details",
    reason: "backend_unavailable",
  };
}

export async function getLiveAsterMarkets(
  symbols: readonly string[] = CORE_SYMBOLS
): Promise<LivePerpDexVenueSnapshot> {
  const normalizedSymbols = symbols.map((symbol) => symbol.toUpperCase());
  const response = await fetchServerApi<LivePerpDexVenueSnapshot>(
    `/perp-dex/venues/aster/markets?symbols=${encodeURIComponent(normalizedSymbols.join(","))}`
  );

  if (response?.success) return response.data;

  return {
    venue_id: "aster",
    venue_name: "Aster",
    source: "aster_fapi_public_market_data",
    status: "unavailable",
    dex: null,
    requested_symbols: normalizedSymbols,
    markets: [],
    fetched_at: null,
    read_only: true,
    execution_enabled: false,
    normalization_status: "aster_public_futures_market_data",
    reason: "backend_unavailable",
  };
}

export async function getLiveGmxMarkets(
  symbols: readonly string[] = CORE_SYMBOLS
): Promise<LivePerpDexVenueSnapshot> {
  const normalizedSymbols = symbols.map((symbol) => symbol.toUpperCase());
  const response = await fetchServerApi<LivePerpDexVenueSnapshot>(
    `/perp-dex/venues/gmx/markets?symbols=${encodeURIComponent(normalizedSymbols.join(","))}`
  );

  if (response?.success) return response.data;

  return {
    venue_id: "gmx",
    venue_name: "GMX",
    source: "gmx_markets_info",
    status: "unavailable",
    dex: "arbitrum",
    requested_symbols: normalizedSymbols,
    markets: [],
    fetched_at: null,
    read_only: true,
    execution_enabled: false,
    normalization_status: "unavailable",
    reason: "backend_unavailable",
  };
}

export async function getLiveCoinGlassPerpDexMarkets(
  symbols: readonly string[] = CORE_SYMBOLS
): Promise<LivePerpDexVenueSnapshot> {
  const normalizedSymbols = symbols.map((symbol) => symbol.toUpperCase());
  const response = await fetchServerApi<LivePerpDexVenueSnapshot>(
    `/perp-dex/venues/coinglass/markets?symbols=${encodeURIComponent(normalizedSymbols.join(","))}`
  );

  if (response?.success) return response.data;

  return {
    venue_id: "coinglass_perp_dex",
    venue_name: "CoinGlass Perp DEX",
    source: "coinglass_futures_coins_markets",
    status: "unavailable",
    dex: "coinglass",
    requested_symbols: [...normalizedSymbols],
    requested_exchanges: [],
    candidate_exchanges: [],
    markets: [],
    fetched_at: null,
    read_only: true,
    execution_enabled: false,
    ranking_enabled: false,
    production_signal_enabled: false,
    normalization_status: "coinglass_coin_market_enrichment",
    coverage_summary: {
      requested_symbols: [...normalizedSymbols],
      requested_exchanges: [],
      total_rows: 0,
      exchanges_with_matches: 0,
      field_groups: [],
      field_totals: {},
      direct_adapter_candidate_hints: [],
      selection_policy: "backend unavailable",
      by_exchange: {},
    },
    reason: "backend_unavailable",
  };
}

export async function getLivePerpDexRouteConstraints(): Promise<LivePerpDexRouteConstraints> {
  const response = await fetchServerApi<LivePerpDexRouteConstraints>("/perp-dex/route-constraints");
  if (response?.success) return response.data;

  return {
    status: "unavailable",
    read_only: true,
    execution_enabled: false,
    production_liquidity_signal: false,
    normalized_snapshot_venues: [],
    raw_snapshot_venues: [],
    capabilities: [],
    blockers: [],
    ui_policy: {
      may_show_market_rows: false,
      may_show_research_candidates: false,
      may_rank_by_liquidity: false,
      may_submit_orders: false,
    },
    reason: "backend_unavailable",
  };
}

export async function getLivePerpDexRouteModel(): Promise<LivePerpDexRouteModel> {
  const response = await fetchServerApi<LivePerpDexRouteModel>("/perp-dex/route-model");
  if (response?.success) return response.data;

  return {
    version: "v0",
    status: "unavailable",
    read_only: true,
    execution_enabled: false,
    ranking_enabled: false,
    production_signal_enabled: false,
    model_scope: "unavailable",
    supported_venues: [],
    model_components: [],
    venue_readiness: [],
    required_inputs: [],
    formula_skeleton: {},
    diagnostic_cost_estimate_v0: {
      status: "unavailable",
      read_only: true,
      may_emit_numeric_total_bps: false,
      safe_use: "backend unavailable",
      components: [],
      summary: {
        status: "unavailable",
        boundary: "component_readiness_only",
        component_count: 0,
        display_only_component_count: 0,
        blocked_numeric_component_count: 0,
        sourced_component_count: 0,
        component_ids: [],
        display_component_ids: [],
        blocked_numeric_component_ids: [],
        sourced_component_ids: [],
        venue_breakdown: [],
        blocker_breakdown: [],
        required_input_breakdown: [],
        source_field_breakdown: [],
        safe_use_breakdown: [],
        readiness_rollup: [],
        depth_staleness_policy_checklist: [],
        required_policy_input_breakdown: [],
        next_action_breakdown: [],
        source_input_action_coverage: [],
        route_ready_evidence_checklist: [],
        venue_evidence_status: [],
        may_emit_numeric_total_bps: false,
        numeric_total_status: "blocked",
        safe_use: "backend unavailable",
        next_action: "restore backend route model endpoint",
      },
      next_action: "restore backend route model endpoint",
    },
    output_policy: {
      may_show_checklist: false,
      may_show_formula_skeleton: false,
      may_show_diagnostic_cost_components: false,
      may_estimate_cost_bps: false,
      may_rank_routes: false,
      may_submit_orders: false,
    },
    blockers: [],
    next_action: "restore backend route model endpoint",
    reason: "backend_unavailable",
  };
}

async function fetchOhlcvWindowByPages(symbol: string, interval: ChartInterval, range: ChartRange): Promise<OhlcvRow[]> {
  const latestRows = await fetchRows<OhlcvRow>(`/data/ohlcv?symbol=${symbol}&exchange=${DEFAULT_EXCHANGE}&interval=${interval}`);
  const latestRow = latest(latestRows);
  if (!latestRow) return [];

  const stepMs = intervalMs(interval);
  const endMs = latestRow.timestamp;
  const startMs = Math.max(0, endMs - rangeMs(range) + stepMs);
  const pageSpanMs = stepMs * 999;
  const pageRanges: Array<{ start: number; end: number }> = [];
  const rowsByKey = new Map<number, OhlcvRow>();

  for (const row of latestRows) {
    if (row.timestamp >= startMs && row.timestamp <= endMs) {
      rowsByKey.set(row.timestamp, row);
    }
  }

  for (let cursor = startMs; cursor <= endMs; cursor += pageSpanMs + stepMs) {
    const pageEnd = Math.min(cursor + pageSpanMs, endMs);
    pageRanges.push({ start: Math.floor(cursor), end: Math.floor(pageEnd) });
  }

  for (let index = 0; index < pageRanges.length; index += 4) {
    const batch = pageRanges.slice(index, index + 4);
    const pages = await Promise.all(
      batch.map((page) =>
        fetchRows<OhlcvRow>(
          `/data/ohlcv?symbol=${symbol}&exchange=${DEFAULT_EXCHANGE}&interval=${interval}&start=${page.start}&end=${page.end}`
        )
      )
    );

    for (const pageRows of pages) {
      for (const row of pageRows) {
        rowsByKey.set(row.timestamp, row);
      }
    }
  }

  return Array.from(rowsByKey.values()).sort((a, b) => a.timestamp - b.timestamp);
}

async function fetchOhlcvWindow(symbol: string, interval: ChartInterval, range: ChartRange): Promise<OhlcvRow[]> {
  const response = await fetchServerApi<OhlcvRow[]>(
    `/data/ohlcv/window?symbol=${symbol}&exchange=${DEFAULT_EXCHANGE}&interval=${interval}&range=${range}`
  );
  if (response?.success) return response.data;

  return fetchOhlcvWindowByPages(symbol, interval, range);
}

function rowsToCandles(rows: OhlcvRow[]): InteractiveCandle[] {
  return rows
    .map((row) => {
      const open = toNumber(row.open);
      const high = toNumber(row.high);
      const low = toNumber(row.low);
      const close = toNumber(row.close);
      if (open === null || high === null || low === null || close === null) return null;

      return {
        timestamp: row.timestamp,
        time: Math.floor(row.timestamp / 1000),
        open,
        high,
        low,
        close,
        volume: toNumber(row.volume),
        quoteVolume: toNumber(row.quote_volume),
      };
    })
    .filter((row): row is InteractiveCandle => row !== null);
}

async function symbolStreams(symbol: string, interval: ChartInterval = "1m", range: ChartRange = "24h") {
  const normalizedSymbol = symbol.toUpperCase();
  const ohlcv = await fetchOhlcvWindow(normalizedSymbol, interval, range);
  const funding = await fetchRows<FundingRow>(`/data/funding?symbol=${normalizedSymbol}&exchange=${DEFAULT_EXCHANGE}`);
  const oiPrimary = await fetchRows<OpenInterestRow>(`/data/open-interest?symbol=${normalizedSymbol}&exchange=${DEFAULT_EXCHANGE}`);
  const oiCoinGlass = await fetchRows<OpenInterestRow>(`/data/open-interest?symbol=${normalizedSymbol}&exchange=coinglass`);
  const basis = await fetchRows<BasisPremiumRow>(`/data/basis-premium?symbol=${normalizedSymbol}&exchange=${DEFAULT_EXCHANGE}`);
  const longShort = await fetchRows<LongShortRow>(`/data/long-short-ratio?symbol=${normalizedSymbol}&exchange=${DEFAULT_EXCHANGE}`);
  const liquidations = await fetchRows<LiquidationRow>(`/data/liquidations?symbol=${normalizedSymbol}&exchange=${DEFAULT_EXCHANGE}`);

  return {
    symbol: normalizedSymbol,
    ohlcv,
    funding,
    openInterest: oiPrimary.length ? oiPrimary : oiCoinGlass,
    basis,
    longShort,
    liquidations,
  };
}

export async function getLiveChartsWorkspace(
  symbol = "BTC",
  interval: ChartInterval = "1m",
  range: ChartRange = "24h"
): Promise<LiveChartsWorkspace> {
  const streams = await symbolStreams(symbol, interval, range);
  const healthResponse = await fetchServerApi<DataHealthPayload>("/data/health");
  const health = healthResponse?.success ? healthResponse.data : null;
  const latestCandle = latest(streams.ohlcv);
  const selectedFreshness = health?.freshness.streams.find(
    (stream) =>
      stream.symbol === streams.symbol &&
      stream.exchange === DEFAULT_EXCHANGE &&
      stream.stream === "ohlcv" &&
      stream.interval === interval
  );
  const latestFunding = latest(streams.funding);
  const latestOi = latest(streams.openInterest);
  const latestBasis = latest(streams.basis);
  const latestLongShort = latest(streams.longShort);
  const price = toNumber(latestCandle?.close);
  const funding = fundingPercent(latestFunding);
  const oiUsd = toNumber(latestOi?.oi_usd);
  const basisPct = toNumber(latestBasis?.basis_pct);
  const longPct = longAccountPercent(latestLongShort);
  const candles = rowsToCandles(streams.ohlcv);
  const selectedRangeLabel = rangeLabel(range);

  const kpis: KpiMetric[] = [
    {
      label: "Last Price",
      value: price === null ? "No data" : `$${price.toLocaleString("en-US", { maximumFractionDigits: 2 })}`,
      caption: `${streams.symbol} ${DEFAULT_EXCHANGE_LABEL} ${interval}`,
      tone: price !== null ? "positive" : "warning",
    },
    {
      label: "Visible Candles",
      value: formatRows(candles.length),
      caption: `${selectedRangeLabel} ${interval}`,
      tone: candles.length > 0 ? "positive" : "warning",
    },
    {
      label: "Funding",
      value: formatPercent(funding),
      caption: `${DEFAULT_EXCHANGE_LABEL} history`,
      tone: funding === null ? "warning" : funding >= 0 ? "positive" : "negative",
    },
    {
      label: "Open Interest",
      value: formatCompactCurrency(oiUsd),
      caption: latestOi?.exchange ?? "No OI rows",
      tone: oiUsd !== null && oiUsd > 0 ? "positive" : "warning",
    },
    {
      label: "Basis",
      value: formatPercent(basisPct),
      caption: `CoinGecko spot vs ${DEFAULT_EXCHANGE_LABEL} perp`,
      tone: basisPct === null ? "warning" : basisPct >= 0 ? "positive" : "negative",
    },
    {
      label: "Long Accounts",
      value: formatPercent(longPct, 2),
      caption: `${DEFAULT_EXCHANGE_LABEL} L/S`,
      tone: longPct === null ? "warning" : longPct >= 50 ? "positive" : "negative",
    },
  ];

  return {
    symbol: streams.symbol,
    exchange: DEFAULT_EXCHANGE,
    exchangeLabel: DEFAULT_EXCHANGE_LABEL,
    interval,
    range,
    rangeLabel: selectedRangeLabel,
    statusLabel: streams.ohlcv.length ? "Interactive OKX candles" : "No OHLCV rows",
    statusTone: streams.ohlcv.length ? "positive" : "warning",
    freshnessLabel: selectedFreshness
      ? `${selectedFreshness.status} - ${selectedFreshness.age_minutes?.toFixed(1) ?? "?"}m`
      : "freshness unknown",
    freshnessTone: freshnessTone(selectedFreshness?.status),
    latestCandleIso: timestampIso(latestCandle?.timestamp),
    kpis,
    candles,
    priceSeries: rowsToSeries(streams.ohlcv, (row) => toNumber(row.close)),
    volumeSeries: rowsToSeries(streams.ohlcv, (row) => toNumber(row.quote_volume) ?? toNumber(row.volume)),
    openInterestSeries: rowsToSeries(streams.openInterest, (row) => toNumber(row.oi_usd)),
    basisSeries: rowsToSeries(streams.basis, (row) => toNumber(row.basis_pct)),
    fundingSeries: rowsToSeries(streams.funding, fundingPercent),
    longRatioSeries: rowsToSeries(streams.longShort, (row) => longAccountPercent(row)),
    sourceRows: [
      ["OHLCV", `${streams.ohlcv.length} rows`, `${DEFAULT_EXCHANGE_LABEL} ${interval} / ${selectedRangeLabel}`],
      ["Funding", `${streams.funding.length} rows`, DEFAULT_EXCHANGE_LABEL],
      ["Open Interest", `${streams.openInterest.length} rows`, latestOi?.exchange ?? "okx/coinglass"],
      ["Basis", `${streams.basis.length} rows`, `CoinGecko + ${DEFAULT_EXCHANGE_LABEL}`],
      ["Long/Short", `${streams.longShort.length} rows`, DEFAULT_EXCHANGE_LABEL],
      ["Liquidations", `${streams.liquidations.length} rows`, "Pending ingestion when 0"],
    ],
  };
}

export async function getLiveMarketMatrix(): Promise<LiveMarketMatrix> {
  const [streams, healthResponse] = await Promise.all([
    Promise.all(CORE_SYMBOLS.map((symbol) => symbolStreams(symbol))),
    fetchServerApi<DataHealthPayload>("/data/health"),
  ]);
  const health = healthResponse?.success ? healthResponse.data : null;

  const rows: LiveMatrixRow[] = streams.map((stream) => {
    const candle = latest(stream.ohlcv);
    const basis = latest(stream.basis);
    const funding = latest(stream.funding);
    const oi = latest(stream.openInterest);
    const longShort = latest(stream.longShort);

    return {
      asset: stream.symbol,
      spotPrice: toNumber(basis?.spot_price),
      perpPrice: toNumber(basis?.perp_price) ?? toNumber(candle?.close),
      basisPct: toNumber(basis?.basis_pct),
      fundingPct: fundingPercent(funding),
      openInterestUsd: toNumber(oi?.oi_usd),
      longAccountRatio: longAccountPercent(longShort),
    };
  });
  const liveRows = rows.filter((row) => row.perpPrice !== null || row.spotPrice !== null).length;
  const maxBasis = rows.reduce<LiveMatrixRow | null>((best, row) => {
    if (row.basisPct === null) return best;
    if (!best || Math.abs(row.basisPct) > Math.abs(best.basisPct ?? 0)) return row;
    return best;
  }, null);
  const maxOi = rows.reduce<LiveMatrixRow | null>((best, row) => {
    if (row.openInterestUsd === null) return best;
    if (!best || row.openInterestUsd > (best.openInterestUsd ?? 0)) return row;
    return best;
  }, null);

  return {
    rows,
    statusLabel: liveRows ? "Live PostgreSQL matrix" : "No matrix rows",
    statusTone: liveRows ? "positive" : "warning",
    kpis: [
      {
        label: "Assets",
        value: `${liveRows}/${rows.length}`,
        caption: CORE_SYMBOLS_LABEL,
        tone: liveRows === rows.length ? "positive" : "warning",
      },
      {
        label: "Max Basis",
        value: maxBasis ? `${maxBasis.asset} ${formatPercent(maxBasis.basisPct)}` : "No data",
        caption: "Spot vs perp",
        tone: maxBasis?.basisPct === undefined || maxBasis?.basisPct === null ? "warning" : maxBasis.basisPct >= 0 ? "positive" : "negative",
      },
      {
        label: "Largest OI",
        value: maxOi ? maxOi.asset : "No data",
        caption: maxOi ? formatCompactCurrency(maxOi.openInterestUsd) : "Open interest",
        tone: maxOi ? "positive" : "warning",
      },
      {
        label: "Funding Rows",
        value: formatRows(health?.row_counts.funding_rates),
        caption: "PostgreSQL",
        tone: (health?.row_counts.funding_rates ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "OI Rows",
        value: formatRows(health?.row_counts.open_interest),
        caption: "PostgreSQL",
        tone: (health?.row_counts.open_interest ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "Basis Rows",
        value: formatRows(health?.row_counts.basis_premium),
        caption: "PostgreSQL",
        tone: (health?.row_counts.basis_premium ?? 0) > 0 ? "positive" : "warning",
      },
    ],
    sourceRows: [
      ["Price", `CoinGecko spot + latest ${DEFAULT_EXCHANGE_LABEL} 1m perp close`],
      ["Funding", `${DEFAULT_EXCHANGE_LABEL} funding history`],
      ["Open Interest", `${DEFAULT_EXCHANGE_LABEL} snapshot preferred, CoinGlass fallback`],
      ["Basis", `CoinGecko spot vs ${DEFAULT_EXCHANGE_LABEL} perp approximate snapshot`],
      ["Long/Short", `${DEFAULT_EXCHANGE_LABEL} account ratio`],
    ],
  };
}

export async function getLiveArbitrageScanner(): Promise<LiveArbitrageScanner> {
  const matrix = await getLiveMarketMatrix();
  const opportunities: LiveArbitrageOpportunity[] = matrix.rows
    .filter((row) => row.basisPct !== null || row.fundingPct !== null)
    .map((row) => {
      const basis = row.basisPct ?? 0;
      const funding = row.fundingPct ?? 0;
      const edge = Math.abs(basis);
      const shortPerp = basis >= 0;
      const type: LiveArbitrageOpportunity["type"] = edge >= Math.abs(funding) ? "basis" : "funding_bias";

      return {
        id: `basis-${row.asset.toLowerCase()}`,
        type,
        asset: row.asset,
        longLeg: shortPerp ? "CoinGecko spot proxy" : `${DEFAULT_EXCHANGE_LABEL} perp`,
        shortLeg: shortPerp ? `${DEFAULT_EXCHANGE_LABEL} perp` : "CoinGecko spot proxy",
        edgePct: edge,
        fundingPct: row.fundingPct,
        openInterestUsd: row.openInterestUsd,
        source: "basis_premium + funding_rates",
        riskNote: row.openInterestUsd && row.openInterestUsd > 0 ? "Data-backed" : "OI missing",
      };
    })
    .sort((left, right) => right.edgePct - left.edgePct);

  return {
    opportunities,
    statusLabel: opportunities.length ? "Live basis scan" : "No live opportunities",
    statusTone: opportunities.length ? "positive" : "warning",
    kpis: [
      {
        label: "Opportunities",
        value: String(opportunities.length),
        caption: "Basis/funding candidates",
        tone: opportunities.length ? "positive" : "warning",
      },
      {
        label: "Largest Edge",
        value: opportunities[0] ? `${opportunities[0].asset} ${formatPercent(opportunities[0].edgePct)}` : "No data",
        caption: "Absolute basis",
        tone: opportunities[0] ? "positive" : "warning",
      },
      ...matrix.kpis.slice(3, 6),
    ],
  };
}

export async function getLiveStrategyReadiness(): Promise<LiveStrategyReadiness> {
  const [charts, healthResponse] = await Promise.all([
    getLiveChartsWorkspace("BTC"),
    fetchServerApi<DataHealthPayload>("/data/health"),
  ]);
  const health = healthResponse?.success ? healthResponse.data : null;
  const rows = health?.row_counts ?? {};
  const hasCoreInputs = (rows.ohlcv ?? 0) > 0 && (rows.funding_rates ?? 0) > 0 && (rows.open_interest ?? 0) > 0;

  return {
    statusLabel: hasCoreInputs ? "Live inputs ready" : "Inputs incomplete",
    statusTone: hasCoreInputs ? "positive" : "warning",
    priceSeries: charts.priceSeries,
    fundingSeries: charts.fundingSeries,
    kpis: [
      {
        label: "Backtest Engine",
        value: "Pending",
        caption: "Real output only",
        tone: "warning",
      },
      {
        label: "OHLCV Rows",
        value: formatRows(rows.ohlcv),
        caption: "Price input",
        tone: (rows.ohlcv ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "Funding Rows",
        value: formatRows(rows.funding_rates),
        caption: "Funding input",
        tone: (rows.funding_rates ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "OI Rows",
        value: formatRows(rows.open_interest),
        caption: "Risk/liquidity input",
        tone: (rows.open_interest ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "Basis Rows",
        value: formatRows(rows.basis_premium),
        caption: "Basis input",
        tone: (rows.basis_premium ?? 0) > 0 ? "positive" : "warning",
      },
      {
        label: "Data Quality",
        value: health ? `${health.data_quality.score.toFixed(0)}/100` : "No data",
        caption: "24h window",
        tone: health && health.data_quality.score >= 80 ? "positive" : "warning",
      },
    ],
    readinessRows: [
      ["Price candles", formatRows(rows.ohlcv), (rows.ohlcv ?? 0) > 0 ? "Ready" : "Missing"],
      ["Funding rates", formatRows(rows.funding_rates), (rows.funding_rates ?? 0) > 0 ? "Ready" : "Missing"],
      ["Open interest", formatRows(rows.open_interest), (rows.open_interest ?? 0) > 0 ? "Ready" : "Missing"],
      ["Basis snapshots", formatRows(rows.basis_premium), (rows.basis_premium ?? 0) > 0 ? "Ready" : "Missing"],
      ["Liquidations", formatRows(rows.liquidations), (rows.liquidations ?? 0) > 0 ? "Ready" : "Pending ingestion"],
      ["Backtest engine", "0 live runs", "Pending implementation"],
    ],
  };
}
