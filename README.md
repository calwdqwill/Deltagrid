# DeltaGrid — Crypto Arbitrage Scanner + RWA Intelligence

Production-ready crypto arbitrage scanner. Spot and perp markets across CEX and DEX venues. RWA and treasury intelligence layer.

## Architecture

- **Frontend**: Next.js 14 + React + TypeScript + Tailwind CSS + Zustand + TanStack Query
- **Backend**: FastAPI + Python 3.11 + SQLAlchemy + SQLite (PostgreSQL-ready)
- **Data**: CoinGecko API (primary), CoinGlass, GeckoTerminal, alternative.me
- **Cache**: In-memory LRU with TTL (Redis-ready interface)
- **Persistence**: SQLite (PostgreSQL migration path via Alembic), 33 tables
- **Auth**: JWT tokens, bcrypt hashing, optional auth middleware, dual-token refresh
- **Enterprise-ready**: Plan capabilities, feature flags, request tracing, API boundary markers

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+

### Standalone HTML Preview
Для быстрого просмотра будущего scanner/backtest UX без backend и без Next.js откройте файл:

```text
frontend/preview/index.html
```

Preview работает как статический HTML: страницы связаны через обычные `<a href="">`, mock-данные находятся внутри HTML, фильтры и табы используют только минимальный inline JavaScript.

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env (optional: add COINGECKO_API_KEY)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend runs at `http://127.0.0.1:8000`

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://127.0.0.1:3000`

> **Windows note**: Use `http://127.0.0.1:3000` instead of `localhost` to avoid IPv6 timeout.

### Docker Compose
```bash
docker-compose up --build
```

## Features

### Phase 1 — MVP Scanner ✅
- Scanner with CEX-CEX, DEX-CEX, Spot-Perp tabs
- Search, sort, filter by spread/volume
- Favorite / Pin instruments
- Detail drawer with calculation breakdown
- Settings with RU/EN localization
- KPI cards (opportunities, best spread, avg spread, active signals)
- Cache with stale/fallback state handling
- Health and status endpoints

### Phase 2 — Auth + Paper Trading ✅
- **Auth**: JWT register/login with email/password, Telegram OAuth, Web3 Wallet
- **Paper Trading**: Demo accounts ($10K), portfolio state, trade lifecycle
- **Performance**: PnL, win rate, drawdown, Sharpe-ready metrics
- **Billing**: Plan definitions, referral code generation
- **User Profile**: Account info, plan status
- **PostgreSQL-ready**: Async engine + Alembic migrations configured
- **Redis-ready**: Cache abstraction interface

### Phase 3 — Trade Execution + Real Data ✅
- Market Dashboard: trending, gainers, losers, fear & greed, funding rates
- Exchange Connectors: Binance, Bybit, OKX, Hyperliquid, Aster
- Order Intent Pipeline with Risk Manager
- Kill switch, position sizing, max exposure rules
- Encrypted API key storage (Fernet AES-256)
- Execution sessions with audit trail

### Phase 4 — Scale + Live Features ✅
- Realtime streaming: Binance WebSocket + SSE fallback
- Alerting Engine: rules CRUD, evaluation, deduplication, cooldown
- Notifications: email/web-push/Telegram with preference toggles
- Provider Health Monitor: CoinGlass, GeckoTerminal integration
- Dual-token auth with automatic refresh

### Phase 5 — RWA + Treasuries ✅
- **RWA Scanner**: Tokenized gold (XAUT, PAXG), treasuries (BUIDL, USDY), credit (CFG)
- **Treasury Dashboard**: BTC holdings tracker (MicroStrategy, MARA, Tesla, Block)
- **Tokenization Platforms**: Centrifuge, Figure, Maple Finance with TVL and governance tokens
- **Detail Views**: Issuer, blockchain, contract address, NAV, yield APR, premium/discount
- **Alert Integration**: `rwa_price_threshold`, `treasury_holdings_change` rule types

### Phase 6.0 — Architecture Hardening ✅
- **Plan Capabilities**: Database-driven feature gating (free/pro/enterprise)
- **Feature Flags**: User-level overrides with expiration support
- **Request Tracing**: `X-Request-ID` middleware on all requests
- **Global Exception Handler**: Consistent `{ error: { code, message, request_id } }` format
- **API Boundaries**: `@internal` / `@public_ready` endpoint markers
- **CORS Hardening**: Environment-aware restrictions

## API Endpoints

### Phase 1 Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/scanner` | List scanner records |
| `GET /api/v1/scanner/{id}` | Record detail |
| `GET /api/v1/preferences` | User preferences |
| `POST /api/v1/preferences` | Update preferences |
| `GET /api/v1/health` | Health check |
| `GET /api/v1/health/status` | Data source status |

### Phase 2 Endpoints
| Endpoint | Description | Auth |
|----------|-------------|------|
| `POST /api/v1/auth/register` | Register new user | Public |
| `POST /api/v1/auth/login` | Login | Public |
| `GET /api/v1/auth/me` | Current user | Required |
| `GET /api/v1/paper/accounts` | List paper accounts | Required |
| `POST /api/v1/paper/accounts` | Create paper account | Required |
| `GET /api/v1/paper/accounts/{id}/trades` | List trades | Required |
| `POST /api/v1/paper/accounts/{id}/trades` | Open trade | Required |
| `POST /api/v1/paper/accounts/{id}/trades/{trade_id}/close` | Close trade | Required |
| `GET /api/v1/performance/accounts/{id}` | Performance metrics | Required |
| `GET /api/v1/billing/plans` | Available plans | Public |

### Phase 3 Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/market/trending` | Trending coins |
| `GET /api/v1/market/gainers` | Top gainers |
| `GET /api/v1/market/losers` | Top losers |
| `GET /api/v1/market/fear-greed` | Fear & Greed index |
| `GET /api/v1/market/funding-rates` | Perp funding rates |
| `GET /api/v1/exchange-accounts` | Exchange accounts |
| `GET /api/v1/connectors/capabilities` | Connector registry |
| `GET /api/v1/execution/intents` | Order intents |
| `GET /api/v1/risk/rules` | Risk rules |

### Phase 4 Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/stream/config` | Stream configuration |
| `WS /api/v1/stream/ws` | WebSocket stream |
| `GET /api/v1/stream/sse` | SSE fallback |
| `GET /api/v1/alerts/rules` | Alert rules |
| `GET /api/v1/alerts/events` | Alert events |
| `GET /api/v1/notifications/preferences` | Notification preferences |
| `GET /api/v1/health/providers` | Provider health status |

### Phase 5 Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/rwa/assets` | RWA assets (category filter) |
| `GET /api/v1/rwa/assets/{id}` | RWA asset detail |
| `GET /api/v1/rwa/assets/{id}/snapshots` | RWA asset history |
| `GET /api/v1/rwa/categories` | RWA category counts |
| `GET /api/v1/rwa/compare` | Compare two RWA assets |
| `GET /api/v1/treasury/entities` | Treasury entities |
| `GET /api/v1/treasury/entities/{id}` | Treasury entity detail |
| `GET /api/v1/treasury/entities/{id}/snapshots` | Treasury entity history |
| `GET /api/v1/treasury/btc-holdings` | BTC holdings leaderboard |
| `GET /api/v1/treasury/platforms` | Tokenization platforms |

## Roadmap

| Phase | Status | Focus |
|-------|--------|-------|
| 1 | ✅ Done | MVP Scanner |
| 2 | ✅ Done | Auth + Paper Trading + Revenue hooks |
| 3 | ✅ Done | Trade Execution + Real Data Connectors + Market Dashboard |
| 4 | ✅ Done | Scale + Alerts + Realtime Streaming + Provider Health |
| 5 | ✅ Done | RWA + Treasuries + Tokenization Intelligence |
| 6 | 📋 Planned | Enterprise + B2B + Multi-tenancy + White-label |
