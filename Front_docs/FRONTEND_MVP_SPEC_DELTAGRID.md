# FRONTEND_MVP_SPEC.md — Deltagrid

Версия: 0.1  
Статус: MVP frontend specification  
Формат продукта: web-based crypto research / trading terminal  
Основные источники данных: CoinGecko + CoinGlass  
Графики MVP: TradingView Lightweight Charts + бесплатные dashboard chart libraries

---

## 1. Цель MVP

Deltagrid — аналитическая web-платформа для криптотрейдеров, аналитиков и квант-ресерчеров.

Цель первой frontend-сборки — собрать рабочий интерфейс в формате профессионального research/trading terminal:

- глобальный обзор рынка;
- отдельный Perp DEX модуль;
- карточки активов;
- отдельный Funding-модуль;
- arbitrage scanner без funding-дублирования;
- market matrix без funding-дублирования;
- charts на бесплатной библиотеке;
- Strategy Lab для бэктестинга.

MVP не должен выглядеть как retail portfolio tracker, лендинг или CoinMarketCap-клон.

---

## 2. Ключевые решения

### 2.1. Навигация

Используем гибридную навигацию:

```text
Sidebar = основные разделы продукта
Top workspace tabs = открытые рабочие сущности / исследования / активы / стратегии
```

Основные разделы открываются через sidebar. Детальные рабочие контексты открываются сверху во вкладках.

### 2.2. Правый drawer

В MVP правый contextual panel / drawer не делаем.

Причина: снизить сложность первой сборки и не перегружать layout.

### 2.3. Funding

Funding — отдельный first-class модуль.

Все полноценные funding-экраны живут только в разделе `Funding`.

Нельзя дублировать полноценные funding screens в:

- Market Overview;
- Perp DEX;
- Arbitrage Scanner;
- Market Matrix.

Допускаются только маленькие preview/link-card, ведущие в Funding.

### 2.4. Charts

Платные charting-решения не покупаем.

Для MVP используем:

```text
TradingView Lightweight Charts — price / candle / line / volume / overlays
ECharts или Recharts — dashboard charts, heatmap, matrix, gauges
TanStack Table — таблицы
```

TradingView Advanced Charts / платные терминальные решения не входят в MVP.

### 2.5. AI Research

AI Research не входит в MVP и не показывается в sidebar.

---

## 3. Visual direction

Визуальная база формируется из двух приложенных референсов.

### 3.1. Reference A — gradient executive cards

Использовать из первого референса:

- крупные gradient summary cards;
- мягкие rounded corners;
- glassmorphism / dark translucent panels;
- яркие акцентные карточки;
- крупные цифры на главных summary-блоках;
- premium dashboard feeling.

Где применять:

- верхний hero-блок Market Overview;
- KPI cards;
- summary cards Funding Overview;
- Strategy Lab result summary;
- важные total / PnL / regime widgets.

Не применять ко всему интерфейсу, иначе продукт станет слишком “игровым” и менее terminal-like.

### 3.2. Reference B — dense professional terminal

Использовать из второго референса как основной UX-референс:

- плотный dark terminal layout;
- компактная верхняя панель метрик;
- левый sidebar / icon rail;
- большие chart panels;
- таблицы как основной рабочий слой;
- tabular controls;
- строгая структура;
- рабочий, а не маркетинговый интерфейс.

Reference B = основной shell и density.  
Reference A = акцентные cards и visual polish.

### 3.3. Итоговый стиль

```text
70–80%: professional dark quant terminal
20–30%: premium gradient fintech cards
```

---

## 4. Design system

### 4.1. Theme

Только dark mode для MVP.

### 4.2. Цвета

```text
Background primary:     #070A12 / #0B0D16
Background secondary:   #10121E / #121524
Surface:                #151827 / #181B2E
Surface elevated:       #1E2135
Border:                 rgba(255,255,255,0.08)
Border active:          rgba(99,102,241,0.55)
Text primary:           #F8FAFC
Text secondary:         #A1A1AA
Text muted:             #71717A
Accent purple:          #7C3AED
Accent pink:            #EC4899
Accent cyan:            #06B6D4
Accent blue:            #3B82F6
Positive:               #10B981
Negative:               #F43F5E
Warning:                #F59E0B
Orange:                 #F97316
```

### 4.3. Градиенты

Использовать умеренно.

```text
Gradient primary: purple → pink → orange
Gradient market: blue → cyan → green
Gradient risk: amber → orange → red
Gradient funding: cyan → purple
```

Правило: не более 1–2 крупных gradient-секций на экран.

### 4.4. Typography

```text
Main UI: Inter / Geist / IBM Plex Sans
Numbers: JetBrains Mono / IBM Plex Mono
Tables: mono или tabular numbers
```

### 4.5. Density

Режим: balanced high-density.

Требования:

- высокая плотность данных;
- читаемые отступы;
- без “пустого SaaS-воздуха”;
- без нечитаемой Bloomberg-перегрузки;
- таблицы и графики — главные элементы.

---

## 5. App shell

### 5.1. Базовый layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Top workspace tabs + search + controls                       │
├───────────────┬──────────────────────────────────────────────┤
│ Left sidebar  │ Main workspace                               │
│ + subnav      │                                              │
│               │                                              │
└───────────────┴──────────────────────────────────────────────┘
```

### 5.2. Left sidebar MVP

```text
Market Overview
Perp DEX
Assets
Funding
Arbitrage Scanner
Market Matrix
Charts
Strategy Lab
```

### 5.3. Sidebar nested navigation

Perp DEX и Funding должны иметь раскрывающуюся иерархию с визуальной “ниточкой” / tree-line.

Пример:

```text
▾ Perp DEX
   ├─ Overview
   ├─ Venues
   ├─ Open Interest
   ├─ Liquidity
   └─ Opportunities

▾ Funding
   ├─ Overview
   ├─ Funding History
   ├─ Perp DEX Funding
   ├─ Funding Arbitrage
   ├─ Funding Matrix
   ├─ Predicted Funding
   └─ Long / Short Legs
```

### 5.4. Top workspace tabs

Top tabs нужны для рабочих контекстов.

Открываются во вкладках:

```text
BTC
ETH
SOL
BTC-USD PERP
SOL-USD PERP
Funding Opportunity #124
BTC Funding History
Hyperliquid vs Binance
Strategy Backtest #1
Market Matrix: Perps
```

Не нужно плодить вкладки для простого перехода по базовым разделам sidebar.

Поведение вкладок:

- active tab выделяется цветом;
- tab можно закрыть;
- можно открыть новую сущность из таблицы/поиска;
- при клике на asset/market/opportunity открывать новый workspace tab;
- если tab уже открыт, активировать существующий, а не создавать дубль.

---

## 6. Information Architecture MVP

```text
Deltagrid
├── Market Overview
│   ├── Market Command Center
│   ├── Market Heatmap
│   ├── BTC / ETH Overview
│   ├── Total Market Cap
│   ├── Top Gainers / Losers
│   ├── Fear & Greed
│   ├── Market Breadth
│   └── Top Assets
│
├── Perp DEX
│   ├── Overview
│   ├── Venues
│   ├── Open Interest
│   ├── Liquidity
│   └── Opportunities
│
├── Assets
│   ├── Asset List
│   └── Asset Deep Dive
│
├── Funding
│   ├── Overview
│   ├── Funding History
│   ├── Perp DEX Funding
│   ├── Funding Arbitrage
│   ├── Funding Matrix
│   ├── Predicted Funding
│   └── Long / Short Legs
│
├── Arbitrage Scanner
│   ├── Basis Arbitrage
│   ├── Cross-Exchange Spread
│   ├── Spot / Perp Dislocation
│   ├── Liquidity Anomaly
│   └── OI / Price Divergence
│
├── Market Matrix
│   ├── Price Matrix
│   ├── Spread Matrix
│   ├── OI Matrix
│   ├── Volume Matrix
│   ├── Liquidity Matrix
│   ├── Depth Matrix
│   └── Slippage Matrix
│
├── Charts
│   ├── Price Chart
│   ├── Volume Chart
│   ├── OI Chart
│   ├── Basis Chart
│   └── Funding Chart
│
└── Strategy Lab
    ├── Strategy Selector
    ├── Parameters
    ├── Backtest Results
    ├── Equity Curve
    ├── Drawdown
    ├── PnL Distribution
    └── Trade Log
```

---

## 7. Screen specifications

## 7.1. Market Overview / Market Command Center

### Назначение

Глобальный срез рынка. Экран должен отвечать на вопросы:

- рынок risk-on или risk-off;
- что происходит с общей капитализацией;
- кто ведет рынок — BTC, ETH, альты, стейблы;
- где топ-гейнеры и топ-лузеры;
- какой общий sentiment;
- есть ли broad market participation.

### Запрещено в этом экране

Не добавлять:

- Funding Heatmap;
- Funding Rate Table;
- Funding Arbitrage;
- Funding Matrix;
- Long / Short funding legs.

Всё это живёт в Funding.

### Блоки

```text
Top KPI Row:
- Total Market Cap
- 24h Volume
- BTC Dominance
- ETH Dominance
- Stablecoin Market Cap
- Fear & Greed

Main:
- Market Heatmap
- Total Market Cap Chart
- BTC / ETH Overview
- Top Gainers / Top Losers
- Market Breadth

Bottom:
- Top Assets Table
```

### UI

- один крупный gradient summary/hero panel можно использовать вверху;
- market heatmap — центральный visual block;
- таблица top assets — рабочая нижняя зона;
- top gainers/losers — справа или под KPI row;
- без funding-heavy компонентов.

### Data

```text
CoinGecko:
- global market data
- global market cap chart
- top assets
- market prices / market cap / volume

CoinGlass / fallback:
- Fear & Greed, если endpoint доступен
```

---

## 7.2. Perp DEX

### Назначение

Отдельный модуль по perpetual DEX, но без полноценной funding-аналитики.

### Subnav

```text
Overview
Venues
Open Interest
Liquidity
Opportunities
```

### Overview blocks

```text
- Total Perp DEX Volume
- Total Perp DEX OI
- Active Venues
- Venue Market Share
- Venue Comparison Cards
- OI by Venue
- Liquidity Snapshot
- Opportunities Preview
```

### Убираем

```text
Perp DEX → Funding
```

Если нужен funding context, показывать только link-card:

```text
View Perp DEX Funding → Funding / Perp DEX Funding
```

---

## 7.3. Assets

### Назначение

Список активов + Asset Deep Dive.

### Asset List

Колонки:

```text
Asset
Price
24h %
7d %
Market Cap
24h Volume
Volume / Market Cap
OI
Perp Volume
Last 7D Sparkline
```

### Asset Deep Dive

Без on-chain в MVP.

Блоки:

```text
Asset Header
Price / Volume / Market Cap
Spot vs Perp Volume
Open Interest
Liquidations
Venue Breakdown
Liquidity / Spread / Depth
Correlation
Signal Summary
Related Opportunities
```

Funding можно показать только как compact metric/link, но не полноценный funding screen.

---

## 7.4. Funding

### Назначение

Центральный модуль по funding-аналитике, funding history, funding arbitrage, matrix и long/short legs.

### Subnav

```text
Overview
Funding History
Perp DEX Funding
Funding Arbitrage
Funding Matrix
Predicted Funding
Long / Short Legs
```

### Funding Overview

Блоки:

```text
Current Funding Extremes
Top Positive Funding
Top Negative Funding
Average Funding by Venue
Market-wide Funding Regime
Funding Opportunity Summary
```

### Funding History

Блоки:

```text
Asset selector
Venue selector
Market type selector
Timeframe selector
Funding history chart
Annualized funding
Current vs historical percentile
```

### Perp DEX Funding

Блоки:

```text
Perp DEX venue comparison
Funding by protocol
Funding heatmap
Venue-specific extremes
```

### Funding Arbitrage

Блоки:

```text
Opportunity Table
Long Leg
Short Leg
Funding Edge
Net APR
Fees Estimate
Slippage Estimate
Liquidity Score
Risk Score
Action
```

### Funding Matrix

Логика:

```text
Rows = assets / markets
Columns = exchanges / venues
Cell = funding rate + long/short signal
```

Пример:

```text
          Binance    OKX      Bybit    Hyperliquid    dYdX
BTC       +0.010%    +0.008%  +0.011%  +0.006%        -0.002%
ETH       +0.014%    +0.012%  +0.009%  +0.004%        -0.001%
SOL       +0.025%    +0.018%  +0.021%  +0.006%        -0.004%
```

### Long / Short Legs

Правило:

```text
Positive funding:
- short perp получает funding
- hedge leg обычно long spot / long opposite exposure

Negative funding:
- long perp получает funding
- hedge leg обычно short spot / short opposite exposure
```

UI должен подсвечивать:

```text
Long leg
Short leg
Where to receive funding
Where to hedge
Estimated net edge
Execution constraints
```

### Важное ограничение

Нельзя показывать только высокий funding. Надо показывать исполнимую возможность:

```text
funding edge
minus fees
minus slippage
minus borrow / hedge cost
minus liquidity risk
minus venue / counterparty risk
```

---

## 7.5. Arbitrage Scanner

### Назначение

Сканер non-funding арбитражей и рыночных dislocations.

### Убираем из этого раздела

```text
Funding Arbitrage
Funding Arb
Funding Matrix
```

### Оставляем

```text
Basis Arbitrage
Cross-Exchange Spread
Spot / Perp Dislocation
Liquidity Anomaly
OI / Price Divergence
```

### Таблица

Колонки:

```text
Opportunity
Type
Asset / Market
Long Leg
Short Leg
Edge
Net APR / Expected Return
Liquidity
Fees Estimate
Slippage Estimate
Risk Score
Action
```

Funding opportunities могут отображаться только как link/previews:

```text
Funding opportunities moved to Funding → Funding Arbitrage
```

---

## 7.6. Market Matrix

### Назначение

Cross-exchange матрица по рынкам без funding.

### Метрики

```text
Price
Spread
Open Interest
Volume
Liquidity
Depth
Slippage
Basis
```

### Убираем

```text
Funding Matrix
Funding metric as full mode
```

Funding matrix живёт в:

```text
Funding → Funding Matrix
```

### Логика

```text
Rows = assets / markets
Columns = venues
Cell = selected metric
```

---

## 7.7. Charts

### Назначение

Графический слой для временных рядов.

### Charts MVP

```text
Price Chart
Volume Chart
OI Chart
Basis Chart
Funding Chart
```

### UI controls

```text
Asset selector
Exchange selector
Market type: Spot / Perp
Timeframe selector
Chart type: Candles / Line
Overlay selector: Volume / OI / Basis / Funding
```

### Что не делаем

```text
Drawing tools
Pine Script
Order placement
Advanced multi-chart workspace
Trading panel
100+ indicators
```

---

## 7.8. Strategy Lab

### Назначение

Аналитический backtesting экран.

### MVP = вариант A + немного B

Основной фокус — backtest UI:

```text
Strategy Selector
Parameters
Backtest Run
Equity Curve
Drawdown Chart
PnL Distribution
Metrics Summary
Trade Log
```

Немного research workspace:

```text
Hypothesis note
Strategy description
Saved runs
Compare runs
```

### Metrics

```text
Total Return
CAGR / Annualized Return
Sharpe
Sortino
Max Drawdown
Win Rate
Profit Factor
Average Trade
Trades Count
Exposure Time
```

---

## 8. Data architecture

### 8.1. Primary data sources

```text
CoinGecko:
- global market data
- global market cap chart
- asset prices
- market cap
- volume
- OHLC / market chart
- top assets

CoinGlass:
- funding rate history
- open interest history
- liquidations
- derivatives metrics
- perp venue data
- fear & greed, if available by plan
```

### 8.2. Normalized entities

```ts
type Asset = {
  id: string;
  symbol: string;
  name: string;
  marketCap?: number;
  price?: number;
  volume24h?: number;
};

type Venue = {
  id: string;
  name: string;
  type: 'cex' | 'perp_dex' | 'dex';
};

type Market = {
  id: string;
  asset: string;
  quote: string;
  venue: string;
  marketType: 'spot' | 'perp' | 'futures';
};

type Candle = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
};

type FundingRate = {
  time: number;
  asset: string;
  market: string;
  venue: string;
  rate: number;
  annualized?: number;
  predicted?: number;
};

type OpenInterestPoint = {
  time: number;
  asset: string;
  market: string;
  venue: string;
  value: number;
};

type Opportunity = {
  id: string;
  type: 'funding' | 'basis' | 'cross_exchange' | 'liquidity' | 'oi_divergence';
  asset: string;
  longLeg?: string;
  shortLeg?: string;
  edge?: number;
  netApr?: number;
  liquidityScore?: string;
  riskScore?: number;
};
```

---

## 9. Frontend stack recommendation

```text
Framework: Next.js / React / TypeScript
Styling: Tailwind CSS
UI primitives: shadcn/ui or custom components
Tables: TanStack Table
Server/cache: TanStack Query or server actions depending current architecture
Charts: TradingView Lightweight Charts
Dashboard visualizations: ECharts or Recharts
State: Zustand or minimal React state for UI workspace tabs
```

---

## 10. Core components

```text
AppShell
SidebarNav
NestedSidebarSection
WorkspaceTabs
TopSearchBar
KpiCard
GradientSummaryCard
MetricCard
ChartPanel
TradingChartPanel
HeatmapPanel
MatrixGrid
DataTable
FilterBar
SegmentedControl
TimeframeSelector
VenueSelector
AssetSelector
OpportunityTable
BacktestResultPanel
StatusBadge
RiskBadge
LongShortLegBadge
Sparkline
```

---

## 11. Anti-duplication rules

### Funding rule

```text
Do not duplicate full funding screens outside Funding.
```

Full funding screens allowed only in:

```text
Funding → Overview
Funding → Funding History
Funding → Perp DEX Funding
Funding → Funding Arbitrage
Funding → Funding Matrix
Funding → Predicted Funding
Funding → Long / Short Legs
```

Other sections may only contain:

```text
compact funding metric
small preview card
link to Funding module
```

### Market Overview rule

```text
Market Overview must stay global market overview.
No funding heatmap, no funding arbitrage, no funding matrix.
```

### Charts rule

```text
Charts may include Funding Chart only as visualization.
Charts must not become funding strategy module.
```

---

## 12. MVP / P1 split

### MVP

```text
App shell
Sidebar navigation
Top workspace tabs
Market Overview
Perp DEX without Funding section
Assets list + Deep Dive
Funding full module
Arbitrage Scanner without Funding Arb
Market Matrix without Funding Matrix
Charts with Lightweight Charts
Strategy Lab static/first functional layout
Mock data + initial CoinGecko/CoinGlass integration
```

### P1

```text
Saved layouts
Advanced workspace tabs
Right contextual drawer
More indicators in Charts
Advanced backtest comparison
Alerting
Export reports
AI Research
On-chain layer in Asset Deep Dive
```

---

## 13. Acceptance criteria

MVP frontend считается готовым, если:

- sidebar содержит утвержденные разделы;
- Perp DEX и Funding имеют nested nav с tree-line / “ниточкой”;
- top tabs открывают рабочие сущности и закрываются;
- right drawer отсутствует;
- Market Overview не содержит funding heatmap / funding arbitrage / funding matrix;
- Funding содержит все funding-related screens;
- Arbitrage Scanner не содержит Funding Arb;
- Market Matrix не содержит Funding Matrix;
- Charts использует бесплатную библиотеку;
- visual style = terminal + premium gradient cards;
- интерфейс читаемый в desktop web;
- все страницы могут работать сначала на mock data;
- data layer подготовлен под CoinGecko и CoinGlass.

---

## 14. Prompt for Codex / KimiCode

```text
Ты работаешь над проектом Deltagrid — web-based crypto research/trading terminal для криптотрейдеров, аналитиков и квант-ресерчеров.

Задача: разработать frontend MVP shell и структуру экранов по спецификации FRONTEND_MVP_SPEC.md.

Ключевые требования:
1. Сделать dark-mode terminal UI в стиле professional crypto research dashboard.
2. Использовать гибридную навигацию: left sidebar для основных разделов и top workspace tabs для открытых сущностей.
3. В sidebar должны быть разделы: Market Overview, Perp DEX, Assets, Funding, Arbitrage Scanner, Market Matrix, Charts, Strategy Lab.
4. Perp DEX и Funding должны иметь nested navigation с визуальной tree-line / “ниточкой”.
5. В MVP не делать правый contextual drawer.
6. Funding — отдельный first-class модуль. Все funding screens должны жить только в Funding.
7. Убрать funding heatmap / funding arbitrage / funding matrix из Market Overview, Perp DEX, Arbitrage Scanner и Market Matrix.
8. Market Overview должен быть глобальным market command center: total market cap, 24h volume, BTC/ETH dominance, Fear & Greed, top gainers/losers, market heatmap, BTC/ETH overview, market breadth, top assets.
9. Charts делать только на бесплатных решениях: TradingView Lightweight Charts для финансовых графиков, ECharts/Recharts для dashboard-графиков.
10. Использовать balanced high-density интерфейс: много данных, но читаемо.
11. Сначала допускается mock data, но data models и service layer должны быть готовы под CoinGecko и CoinGlass.
12. Все markdown-файлы проекта вести на русском языке.

Не делать:
- retail portfolio tracker;
- лендинговый fintech UI;
- AI Research в MVP;
- mobile-first layout;
- платные charting-решения;
- дублирование funding-экранов по разным разделам.
```
