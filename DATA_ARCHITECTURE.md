# Data Architecture — DeltaGrid

## Data Sources

### Phase 1 — Primary: CoinGecko
- **Plan**: Demo (10K credits/mo) for dev → Analyst ($103/mo, 500K credits) for prod
- **Endpoints**:
  - `/simple/price` — batch spot prices (5 tokens = 1 credit)
  - `/exchanges/{id}/tickers` — perp DEX tickers (Hyperliquid, Aster, Lighter)
  - `/derivatives` — CEX futures: price, index, basis, funding_rate, OI
  - `/search/trending` — trending coins
  - `/global` — global market stats
- **Headers**: `x-cg-demo-api-key` (Demo) / `x-cg-pro-api-key` (Paid)
- **Fallback**: mock data on 429/401/no key + banner "Enter API key"

### Phase 1 — Perp DEX Adapters (CG-backed)
- **Hyperliquid**: via `/exchanges/hyperliquid/tickers`
- **Aster**: via `/exchanges/aster-futures/tickers`
- **Lighter**: via `/exchanges/lighter/tickers`
- **Phase 3**: direct REST API for Hyperliquid (`allMids`, clearinghouse state)

### Phase 2+ — Additional Sources
- **alternative.me** — Fear & Greed Index (free)
- **CoinGlass** ($99-299/mo) — CEX futures, funding rate, OI — Phase 4
- **GeckoTerminal** — DEX on-chain data (via CoinGecko)

### Phase 3 — Exchange Connectors (Direct APIs)
- **Binance**: REST spot API, HMAC-SHA256 signing, 1200 req/min
- **Bybit**: V5 unified API, HMAC-SHA256 signing
- **OKX**: REST API, HMAC-SHA256 signing, passphrase required
- **Hyperliquid**: direct REST (`allMids`, clearinghouse), wallet signing для trading

## Data Flow

### Phase 1-2 Flow (HTTP Polling)
```
CoinGecko API / Perp DEX APIs
    ↓
Adapter Layer (BaseAdapter protocol)
    ↓
RawTicker (normalized raw data)
    ↓
CoinGeckoService / PerpDEXService
    ↓
ScannerService (orchestrator)
    ↓
SpreadCalculator + SignalClassifier
    ↓
CacheService (In-Memory → Redis Phase 2+)
    ↓
ScannerRecord DTO → Frontend
```

### Phase 3 Flow (Direct Exchange APIs + Order Intent Pipeline)
```
Binance/OKX/Bybit/Hyperliquid REST API
    ↓
ExchangeConnector (BinanceConnector, OKXConnector, etc.)
    ↓
OrderManager (retry, partial fill tracking, status sync)
    ↓
ExecutionService (intent lifecycle, risk check)
    ↓
RiskManager (rules, kill-switch, position sizing)
    ↓
OrderEvent / AuditLog (persistence)
    ↓
Frontend (Execution dashboard, OrderIntentModal)
```

### Phase 4 Flow (WebSocket Streaming + Provider Layer + Alerting)
```
Binance/OKX/Hyperliquid WebSocket
    ↓
WebSocketManager (unified connection manager)
    ↓
NormalizedStreamEvent (real-time tickers)
    ↓
[Stream → Frontend via WS/SSE]  [Stream → AlertService evaluation]
                                          ↓
                                   AlertRule matching
                                          ↓
                                   AlertEvent + AlertDelivery
                                          ↓
                                   NotificationService
                                          ↓
                                   Email / WebPush / Telegram
```

### Phase 4 Provider Layer Flow
```
CoinGlass API / GeckoTerminal API
    ↓
CoinGlassClient / GeckoTerminalClient (rate-limit aware)
    ↓
ProviderHealthMonitor
    ↓
MarketEnrichmentService
    ↓
GET /market/enrichments + GET /health/providers
```

## Data Status Lifecycle

| Status | Meaning | UI Indicator |
|--------|---------|--------------|
| `live` | Fresh request < TTL | Green dot |
| `cached` | From cache, within TTL | Blue label |
| `stale` | Cache expired, data exists | Amber warning |
| `fallback` | Mock/test data | Amber banner |
| `partial` | Some fields null | Gray label |
| `unavailable` | Source silent | Red label |

## Persistence

### Phase 1 Tables (SQLite)
```sql
preferences     -- key-value store for settings
favorites       -- instrument_ids
pinned          -- instrument_ids
```

### Phase 2 Tables (SQLite, PostgreSQL-ready via Alembic)
```sql
users              -- id, email, username, hashed_password, plan, is_active
paper_accounts     -- user_id, name, initial_balance, current_balance, currency
paper_trades       -- account_id, strategy, instrument_id, side, entry/exit_price, pnl
performance_snapshots -- account_id, total_pnl, win_rate, max_drawdown, sharpe_ratio
referrals          -- referrer_id, code, referral_count
payments           -- user_id, plan, amount, status, provider
```

### Phase 3 Tables (SQLite, PostgreSQL-ready via Alembic)
```sql
exchange_accounts      -- user_id, exchange_name, label, is_active, created_at
exchange_keys          -- account_id, encrypted_api_key, encrypted_secret, key_identifier (SHA-256)
connector_capabilities -- exchange_name, features (spot, margin, futures, withdraw), trading_pairs, config_schema
real_orders            -- intent_id, exchange_account_id, exchange_order_id, symbol, side, type, status, filled_qty, avg_price
order_events           -- order_id, event_type, payload, created_at
execution_runs         -- user_id, session_id, start_time, end_time, status, pnl
risk_rules             -- user_id, rule_type, params, is_active
position_snapshots     -- user_id, exchange_account_id, symbol, size, entry_price, unrealized_pnl
live_trade_sessions    -- user_id, name, strategy, status, started_at, stopped_at
audit_logs             -- user_id, action, resource_type, resource_id, details, created_at
```

### Phase 4 Tables (SQLite, PostgreSQL-ready via Alembic)
```sql
provider_health        -- provider_name, status, last_success_at, last_failure_at, error_count, latency_ms
market_enrichments     -- provider, symbol, metric_type, value, timestamp, raw_data
provider_sync_logs     -- provider, endpoint, status, records_fetched, duration_ms, error_msg
realtime_feed_sessions -- user_id, feed_type, status, connected_at, disconnected_at
stream_events          -- session_id, event_type, symbol, price, volume, timestamp
alert_rules            -- user_id, name, rule_type, symbol, threshold_value, comparison, cooldown_minutes, is_active, severity, channels
alert_events           -- rule_id, alert_type, symbol, message, severity, triggered_at
alert_deliveries       -- event_id, channel, status, sent_at, error_msg
notification_preferences -- user_id, email_enabled, web_push_enabled, telegram_enabled, market_alerts_enabled, execution_alerts_enabled, risk_alerts_enabled, min_severity, quiet_hours_start, quiet_hours_end
exchange_funding_rates -- exchange, symbol, funding_rate, next_funding_time, timestamp
```

## Cache Strategy

- **Phase 1-2**: In-memory dict + TTL (300s default)
- **Phase 3+**: Redis (Upstash free tier → paid)
- **Cache key**: `scanner_records`
- **TTL**: configurable via `CACHE_TTL_SECONDS` env (default: 300s)
- **Warm-up**: cache pre-filled on backend startup
- **Singleton**: single cache/registry instance shared across requests
- **Phase 4**: LRU eviction via `OrderedDict`, invalidation on preference changes

## Formulas

```
grossSpreadPct = ((sellPrice - buyPrice) / buyPrice) * 100
netProfitPct   = grossSpreadPct - feeBuyPct(0.10) - feeSellPct(0.10) - slippagePct

paperTradePnl  = (exitPrice - entryPrice) * quantity - fees
paperPnlPct    = (paperTradePnl / (entryPrice * quantity)) * 100
```

## Signal Logic

| Signal | Condition |
|--------|-----------|
| STRONG | netProfitPct > 1.0% + volume OK |
| BUY_SELL | netProfitPct 0.5-1.0% |
| MARGINAL | netProfitPct 0.1-0.5% |
| HOLD | everything else |

## API Rate Limits

| Source | Limit | Retry |
|--------|-------|-------|
| CoinGecko Demo | 10-30 calls/min | 3x exponential backoff |
| CoinGecko Paid | 500 calls/min | 3x exponential backoff |
| Binance direct | 1200 req/min | 3x with jitter |
| Bybit V5 | 120 req/s | 3x with jitter |
| OKX direct | 30 req/s | 3x with jitter |
| Hyperliquid direct | ~100 req/s | 3x with jitter |
| CoinGlass | 100-300 req/min | 3x with jitter |
| GeckoTerminal | 30 req/min | 3x with jitter |
