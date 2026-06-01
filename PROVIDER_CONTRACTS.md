# Provider Contracts - DeltaGrid

Документ задаёт канонические схемы рыночных данных для следующего слоя хранения и backtesting. Это не подключение API и не изменение кода проекта. Цель - заранее зафиксировать единый формат, чтобы CoinGlass, Binance, Bybit, OKX и Hyperliquid не протекали в бизнес-логику разными именами полей.

## Общие правила

### Версионирование

Все записи содержат `schema_version`. Текущая версия контрактов: `1`.

### Время

Все timestamp-поля хранятся как UTC unix milliseconds:

- `interval_start_ms` - начало интервала включительно.
- `interval_end_ms` - конец интервала исключительно.
- `event_time_ms` - время биржевого события.
- `snapshot_time_ms` - время снимка состояния.
- `ingested_at_ms` - время попадания записи в DeltaGrid.

Для 1m свечи:

```text
interval_end_ms = interval_start_ms + 60_000
```

Если провайдер отдаёт close time как последнюю миллисекунду свечи, например Binance `closeTime`, в canonical contract он переводится в exclusive end:

```text
interval_end_ms = provider_close_time_ms + 1
```

### Нормализация символов

Канонический формат инструмента:

```text
BASE-QUOTE-TYPE
```

Пример:

```text
BTC-USDT-PERP
```

Правила:

- `BASE` и `QUOTE` - uppercase asset symbols.
- `TYPE` - одно из `SPOT`, `PERP`, `FUTURE`, `OPTION`, `INDEX`.
- Для inverse/perpetual contracts `QUOTE` отражает settlement или quote asset, если он явно известен.
- `provider_symbol` всегда сохраняется отдельно, без попытки потерять исходный формат.

Примеры mapping:

| Provider | Provider symbol | Canonical symbol |
| --- | --- | --- |
| Binance | `BTCUSDT` | `BTC-USDT-PERP` |
| Bybit | `BTCUSDT` | `BTC-USDT-PERP` |
| OKX | `BTC-USDT-SWAP` | `BTC-USDT-PERP` |
| Hyperliquid | `BTC` | `BTC-USDC-PERP` |
| CoinGlass | `BTCUSDT` / exchange-specific | `BTC-USDT-PERP` |

### Общие поля источника

Эти поля рекомендуются для всех market-data контрактов.

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | Версия canonical contract. |
| `provider` | string | yes | Источник данных: `coinglass`, `binance`, `bybit`, `okx`, `hyperliquid`. |
| `exchange` | string | yes | Биржа исполнения или venue: `binance`, `bybit`, `okx`, `hyperliquid`. |
| `instrument_id` | string | yes | Внутренний ID инструмента. |
| `symbol` | string | yes | Canonical symbol, например `BTC-USDT-PERP`. |
| `provider_symbol` | string | yes | Исходный символ провайдера. |
| `ingested_at_ms` | integer | yes | UTC unix ms времени ingest. |
| `data_status` | string | yes | `live`, `cached`, `stale`, `partial`, `fallback`, `unavailable`. |
| `raw_payload` | object | no | Исходный payload для аудита и отладки. |

## OHLCV_1m

Назначение: 1-minute candle для backtesting, charting и feature generation.

### Поля

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | Версия схемы. |
| `provider` | string | yes | Источник записи. |
| `exchange` | string | yes | Venue. |
| `instrument_id` | string | yes | Внутренний ID инструмента. |
| `symbol` | string | yes | Canonical symbol. |
| `provider_symbol` | string | yes | Символ у провайдера. |
| `interval` | string | yes | Всегда `1m` для этого контракта. |
| `interval_start_ms` | integer | yes | UTC unix ms, inclusive. |
| `interval_end_ms` | integer | yes | UTC unix ms, exclusive. |
| `open` | number | yes | Open price. |
| `high` | number | yes | High price. |
| `low` | number | yes | Low price. |
| `close` | number | yes | Close price. |
| `volume_base` | number | no | Volume в base asset. |
| `volume_quote` | number | no | Turnover в quote/settle asset. |
| `trade_count` | integer | no | Количество сделок. |
| `is_final` | boolean | yes | Закрыта ли свеча. |
| `ingested_at_ms` | integer | yes | Время ingest. |
| `data_status` | string | yes | Статус качества. |
| `raw_payload` | object | no | Исходная запись. |

### Пример JSON

```json
{
  "schema_version": 1,
  "provider": "binance",
  "exchange": "binance",
  "instrument_id": "binance:BTC-USDT-PERP",
  "symbol": "BTC-USDT-PERP",
  "provider_symbol": "BTCUSDT",
  "interval": "1m",
  "interval_start_ms": 1717200000000,
  "interval_end_ms": 1717200060000,
  "open": 67450.1,
  "high": 67488.0,
  "low": 67420.5,
  "close": 67470.2,
  "volume_base": 124.52,
  "volume_quote": 8401132.45,
  "trade_count": 3184,
  "is_final": true,
  "ingested_at_ms": 1717200061200,
  "data_status": "live"
}
```

### Provider mapping

| Canonical field | CoinGlass | Binance | Bybit | OKX | Hyperliquid |
| --- | --- | --- | --- | --- | --- |
| `provider_symbol` | `symbol` или exchange-specific symbol | request `symbol` | request `symbol` | request `instId` | `s` / request `coin` |
| `interval_start_ms` | `time` / `timestamp` | kline `[0]` open time | `list[].startTime` | candle `[0]` `ts` | `t` |
| `interval_end_ms` | derived from interval | kline `[6] + 1` close time | `startTime + interval` | `ts + interval` | `T` или `t + interval` |
| `open` | `open` / `o` | kline `[1]` | `openPrice` | candle `[1]` `o` | `o` |
| `high` | `high` / `h` | kline `[2]` | `highPrice` | candle `[2]` `h` | `h` |
| `low` | `low` / `l` | kline `[3]` | `lowPrice` | candle `[3]` `l` | `l` |
| `close` | `close` / `c` | kline `[4]` | `closePrice` | candle `[4]` `c` | `c` |
| `volume_base` | `volume` | kline `[5]` base asset volume | `volume` | `vol` или `volCcy` по instrument type | `v` |
| `volume_quote` | `turnover` / `quoteVolume` | kline `[7]` quote asset volume | `turnover` | `volCcyQuote` | нет гарантированного поля, считать как `v * close` при необходимости |
| `trade_count` | `tradeCount` / absent | kline `[8]` number of trades | absent | absent | `n` |
| `is_final` | absent или derived | closed REST candle = `true` | closed REST candle = `true` | `confirm == "1"` | historical candle = `true` |

## FundingRate

Назначение: funding history и текущие funding snapshots для perp markets.

### Поля

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | Версия схемы. |
| `provider` | string | yes | Источник записи. |
| `exchange` | string | yes | Venue. |
| `instrument_id` | string | yes | Внутренний ID инструмента. |
| `symbol` | string | yes | Canonical symbol. |
| `provider_symbol` | string | yes | Символ у провайдера. |
| `funding_time_ms` | integer | yes | Время funding event. |
| `interval_start_ms` | integer | no | Начало funding-периода, если известно. |
| `interval_end_ms` | integer | no | Конец funding-периода, если известно. |
| `interval_hours` | number | no | Funding interval в часах. |
| `funding_rate` | number | yes | Decimal fraction, например `0.0001` для `0.01%`. |
| `predicted_funding_rate` | number | no | Прогноз следующего funding. |
| `annualized_rate` | number | no | Annualized decimal fraction, если провайдер отдаёт или рассчитано отдельно. |
| `mark_price` | number | no | Mark price на момент funding. |
| `index_price` | number | no | Index/oracle price. |
| `premium` | number | no | Premium decimal fraction. |
| `ingested_at_ms` | integer | yes | Время ingest. |
| `data_status` | string | yes | Статус качества. |
| `raw_payload` | object | no | Исходная запись. |

### Пример JSON

```json
{
  "schema_version": 1,
  "provider": "okx",
  "exchange": "okx",
  "instrument_id": "okx:BTC-USDT-PERP",
  "symbol": "BTC-USDT-PERP",
  "provider_symbol": "BTC-USDT-SWAP",
  "funding_time_ms": 1717200000000,
  "interval_start_ms": 1717171200000,
  "interval_end_ms": 1717200000000,
  "interval_hours": 8,
  "funding_rate": 0.000087,
  "predicted_funding_rate": 0.000091,
  "annualized_rate": 0.095265,
  "mark_price": 67470.2,
  "index_price": 67462.8,
  "premium": 0.00011,
  "ingested_at_ms": 1717200002500,
  "data_status": "live"
}
```

### Provider mapping

| Canonical field | CoinGlass | Binance | Bybit | OKX | Hyperliquid |
| --- | --- | --- | --- | --- | --- |
| `provider_symbol` | `symbol` | `symbol` | `symbol` | `instId` | `coin` |
| `funding_time_ms` | `fundingTime` / `time` / `timestamp` | `fundingTime` | `fundingRateTimestamp` | `fundingTime` | `time` |
| `interval_hours` | exchange metadata or provider field if present | exchange funding schedule, commonly 8h | instrument `fundingInterval` in minutes / 60 | derived from `fundingTime` cadence | usually 1h for Hyperliquid perps, verify per asset |
| `funding_rate` | `fundingRate` / `funding_rate` | `fundingRate` | `fundingRate` | `fundingRate` | `fundingRate` or asset context `funding` |
| `predicted_funding_rate` | `nextFundingRate` / provider-specific | absent in funding history | ticker current fields may expose next funding estimate | `nextFundingRate` | `predictedFundings` response, if used |
| `annualized_rate` | `fundingRateAnnualized` | calculated | calculated | calculated | calculated |
| `mark_price` | `markPrice` if present | `markPrice` in funding history | ticker `markPrice` | public mark price endpoint | asset context `markPx` |
| `index_price` | `indexPrice` if present | premium index endpoint `indexPrice` | ticker `indexPrice` | index/mark price endpoint | asset context `oraclePx` |
| `premium` | `premium` if present | premium index endpoint | ticker `basisRate` is not premium; use only if endpoint confirms semantics | `premium` | `premium` |

## OpenInterest

Назначение: снимок open interest для perp/futures instruments.

### Поля

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | Версия схемы. |
| `provider` | string | yes | Источник записи. |
| `exchange` | string | yes | Venue. |
| `instrument_id` | string | yes | Внутренний ID инструмента. |
| `symbol` | string | yes | Canonical symbol. |
| `provider_symbol` | string | yes | Символ у провайдера. |
| `snapshot_time_ms` | integer | yes | UTC unix ms снимка. |
| `open_interest_contracts` | number | no | OI в контрактах. |
| `open_interest_base` | number | no | OI в base asset. |
| `open_interest_quote` | number | no | OI в quote/settle asset. |
| `open_interest_usd` | number | no | OI в USD notional. |
| `mark_price` | number | no | Цена для notional conversion. |
| `ingested_at_ms` | integer | yes | Время ingest. |
| `data_status` | string | yes | Статус качества. |
| `raw_payload` | object | no | Исходная запись. |

### Пример JSON

```json
{
  "schema_version": 1,
  "provider": "hyperliquid",
  "exchange": "hyperliquid",
  "instrument_id": "hyperliquid:BTC-USDC-PERP",
  "symbol": "BTC-USDC-PERP",
  "provider_symbol": "BTC",
  "snapshot_time_ms": 1717200000000,
  "open_interest_contracts": null,
  "open_interest_base": 18452.91,
  "open_interest_quote": null,
  "open_interest_usd": 1244850000.0,
  "mark_price": 67450.0,
  "ingested_at_ms": 1717200001200,
  "data_status": "live"
}
```

### Provider mapping

| Canonical field | CoinGlass | Binance | Bybit | OKX | Hyperliquid |
| --- | --- | --- | --- | --- | --- |
| `provider_symbol` | `symbol` | `symbol` | `symbol` | `instId` | universe `name` / request `coin` |
| `snapshot_time_ms` | `time` / `timestamp` | `time` | `timestamp` | `ts` | ingest time for `metaAndAssetCtxs`, unless response time exists |
| `open_interest_contracts` | `openInterest` / `open_interest` | `openInterest` | `openInterest` if contract-denominated | `oi` | absent |
| `open_interest_base` | `openInterestAmount` / provider-specific | for USDT-M, `openInterest` is often base quantity | `openInterest` if coin-denominated | `oiCcy` for some instruments | asset context `openInterest` |
| `open_interest_quote` | `openInterestUsd` / provider-specific | calculated as base * mark | `openInterestValue` from ticker or calculated | calculated | calculated |
| `open_interest_usd` | `openInterestUsd` / `sumOpenInterestValue` | calculated | `openInterestValue` if USD/USDT | calculated from `oiCcy` and mark | calculated from `openInterest * markPx` |
| `mark_price` | `markPrice` if present | premium index `markPrice` | ticker `markPrice` | mark price endpoint | asset context `markPx` |

## Liquidation

Назначение: liquidation events или агрегированные liquidation buckets. Контракт допускает оба варианта, потому что провайдеры отдают разные уровни детализации.

### Поля

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | Версия схемы. |
| `provider` | string | yes | Источник записи. |
| `exchange` | string | yes | Venue. |
| `instrument_id` | string | yes | Внутренний ID инструмента. |
| `symbol` | string | yes | Canonical symbol. |
| `provider_symbol` | string | yes | Символ у провайдера. |
| `liquidation_id` | string | no | Provider event id, если есть. |
| `is_aggregate` | boolean | yes | `true`, если запись bucket/aggregate. |
| `event_time_ms` | integer | no | Время event. |
| `interval_start_ms` | integer | no | Начало bucket, если aggregate. |
| `interval_end_ms` | integer | no | Конец bucket, если aggregate. |
| `side` | string | yes | `buy`, `sell`, `long`, `short` или `unknown`. |
| `position_side` | string | no | `long`, `short`, `net`, если провайдер отдаёт. |
| `price` | number | no | Bankruptcy/order/liquidation price по семантике провайдера. |
| `quantity_base` | number | no | Размер в base asset. |
| `quantity_quote` | number | no | Notional в quote/USD. |
| `order_type` | string | no | Provider order type. |
| `status` | string | no | Provider order status. |
| `ingested_at_ms` | integer | yes | Время ingest. |
| `data_status` | string | yes | Статус качества. |
| `raw_payload` | object | no | Исходная запись. |

### Пример JSON

```json
{
  "schema_version": 1,
  "provider": "binance",
  "exchange": "binance",
  "instrument_id": "binance:BTC-USDT-PERP",
  "symbol": "BTC-USDT-PERP",
  "provider_symbol": "BTCUSDT",
  "liquidation_id": "binance:BTCUSDT:1717200000123:sell:1.25",
  "is_aggregate": false,
  "event_time_ms": 1717200000123,
  "interval_start_ms": null,
  "interval_end_ms": null,
  "side": "sell",
  "position_side": "long",
  "price": 66420.5,
  "quantity_base": 1.25,
  "quantity_quote": 83025.625,
  "order_type": "LIMIT",
  "status": "FILLED",
  "ingested_at_ms": 1717200001100,
  "data_status": "live"
}
```

### Provider mapping

| Canonical field | CoinGlass | Binance | Bybit | OKX | Hyperliquid |
| --- | --- | --- | --- | --- | --- |
| `liquidation_id` | absent или provider id | derived from force order fields | derived from websocket payload | derived from `instId`, `ts`, `side`, `sz` | not available from stable public info endpoints |
| `is_aggregate` | often `true` for history buckets | `false` for force orders | `false` for websocket liquidation events | `false` or provider grouped details | not supported |
| `event_time_ms` | bucket timestamp if event-level unavailable | `time` or force order stream `T` | websocket data `T` | detail `ts` | not supported |
| `interval_start_ms` | aggregate bucket timestamp | absent | absent | absent | not supported |
| `interval_end_ms` | derived from bucket interval | absent | absent | absent | not supported |
| `side` | `side`, `longLiquidation*`, `shortLiquidation*` mapped to `long`/`short` | `side` | `S` | `side` | not supported |
| `position_side` | long/short bucket side if present | derived: liquidation sell usually closes long, buy closes short | derived from `S` if no explicit field | `posSide` | not supported |
| `price` | `price` / `avgPrice` / absent for aggregate | `price` or `averagePrice`; stream `p` / `ap` | `p` | `bkPx` | not supported |
| `quantity_base` | `amount` / calculated from notional | `origQty` / `executedQty`; stream `q` / `z` | `v` | `sz` | not supported |
| `quantity_quote` | `liquidationUsd`, `longLiquidationUsd`, `shortLiquidationUsd` | calculated `quantity_base * price` | calculated | calculated | not supported |
| `status` | absent | `status`; stream `X` | absent | absent | not supported |

## LongShortRatio

Назначение: sentiment/positioning ratio для market regime, crowded trade и фильтров стратегии.

### Поля

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | Версия схемы. |
| `provider` | string | yes | Источник записи. |
| `exchange` | string | yes | Venue. |
| `instrument_id` | string | yes | Внутренний ID инструмента. |
| `symbol` | string | yes | Canonical symbol. |
| `provider_symbol` | string | yes | Символ у провайдера. |
| `ratio_type` | string | yes | `global_account`, `top_account`, `top_position`, `taker_volume`, `provider_aggregate`. |
| `interval` | string | no | Например `5m`, `1h`, `1d`. |
| `interval_start_ms` | integer | yes | UTC unix ms, inclusive. |
| `interval_end_ms` | integer | yes | UTC unix ms, exclusive. |
| `long_ratio` | number | no | Доля long, `0..1`. |
| `short_ratio` | number | no | Доля short, `0..1`. |
| `long_short_ratio` | number | yes | `long_ratio / short_ratio`, если обе доли известны. |
| `long_value` | number | no | Provider-specific long volume/accounts. |
| `short_value` | number | no | Provider-specific short volume/accounts. |
| `ingested_at_ms` | integer | yes | Время ingest. |
| `data_status` | string | yes | Статус качества. |
| `raw_payload` | object | no | Исходная запись. |

### Пример JSON

```json
{
  "schema_version": 1,
  "provider": "binance",
  "exchange": "binance",
  "instrument_id": "binance:BTC-USDT-PERP",
  "symbol": "BTC-USDT-PERP",
  "provider_symbol": "BTCUSDT",
  "ratio_type": "global_account",
  "interval": "5m",
  "interval_start_ms": 1717200000000,
  "interval_end_ms": 1717200300000,
  "long_ratio": 0.5142,
  "short_ratio": 0.4858,
  "long_short_ratio": 1.0585,
  "long_value": null,
  "short_value": null,
  "ingested_at_ms": 1717200301200,
  "data_status": "live"
}
```

### Provider mapping

| Canonical field | CoinGlass | Binance | Bybit | OKX | Hyperliquid |
| --- | --- | --- | --- | --- | --- |
| `ratio_type` | endpoint/category name | endpoint: global/top account/top position/taker volume | account-ratio endpoint type | Rubik stats endpoint name | not available as stable public field |
| `interval_start_ms` | `time` / `timestamp` | `timestamp` | `timestamp` | `ts` | not supported |
| `interval_end_ms` | derived from period | `timestamp + period` | `timestamp + period` | derived from period | not supported |
| `long_ratio` | `longAccount` / `longRatio` / provider-specific | `longAccount` | `buyRatio` when endpoint represents long buyers | absent, derive if OKX returns enough fields | not supported |
| `short_ratio` | `shortAccount` / `shortRatio` / provider-specific | `shortAccount` | `sellRatio` | absent, derive if OKX returns enough fields | not supported |
| `long_short_ratio` | `longShortRatio` / `ratio` | `longShortRatio` or `buySellRatio` for taker volume | `buyRatio / sellRatio` | `ratio` | not supported |
| `long_value` | provider-specific long volume/accounts | `buyVol` for taker volume endpoint | absent | provider-specific | not supported |
| `short_value` | provider-specific short volume/accounts | `sellVol` for taker volume endpoint | absent | provider-specific | not supported |

## BasisPremium

Назначение: basis/premium features для funding arbitrage, cash-and-carry и perp dislocation monitoring.

### Поля

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | Версия схемы. |
| `provider` | string | yes | Источник записи. |
| `exchange` | string | yes | Venue. |
| `instrument_id` | string | yes | Внутренний ID инструмента. |
| `symbol` | string | yes | Canonical symbol. |
| `provider_symbol` | string | yes | Символ у провайдера. |
| `snapshot_time_ms` | integer | yes | UTC unix ms снимка. |
| `mark_price` | number | no | Mark price. |
| `index_price` | number | no | Index/oracle price. |
| `basis` | number | no | `mark_price - index_price` или provider basis. |
| `basis_pct` | number | no | `basis / index_price`. |
| `premium` | number | no | Provider premium index decimal fraction. |
| `premium_pct` | number | no | Premium в процентах, если провайдер отдаёт процент. |
| `next_funding_time_ms` | integer | no | Время следующего funding. |
| `ingested_at_ms` | integer | yes | Время ingest. |
| `data_status` | string | yes | Статус качества. |
| `raw_payload` | object | no | Исходная запись. |

### Пример JSON

```json
{
  "schema_version": 1,
  "provider": "hyperliquid",
  "exchange": "hyperliquid",
  "instrument_id": "hyperliquid:BTC-USDC-PERP",
  "symbol": "BTC-USDC-PERP",
  "provider_symbol": "BTC",
  "snapshot_time_ms": 1717200000000,
  "mark_price": 67450.0,
  "index_price": 67431.0,
  "basis": 19.0,
  "basis_pct": 0.00028177,
  "premium": 0.00028,
  "premium_pct": 0.028,
  "next_funding_time_ms": 1717203600000,
  "ingested_at_ms": 1717200001000,
  "data_status": "live"
}
```

### Provider mapping

| Canonical field | CoinGlass | Binance | Bybit | OKX | Hyperliquid |
| --- | --- | --- | --- | --- | --- |
| `snapshot_time_ms` | `time` / `timestamp` | premium index response time or ingest time | ticker timestamp or ingest time | `ts` from mark/index/funding endpoints | ingest time for asset context |
| `mark_price` | `markPrice` | `markPrice` | `markPrice` | mark price endpoint | `markPx` |
| `index_price` | `indexPrice` | `indexPrice` | `indexPrice` | index ticker/price endpoint | `oraclePx` |
| `basis` | `basis` | calculated `markPrice - indexPrice` | `basis` if ticker exposes it, otherwise calculated | calculated | calculated `markPx - oraclePx` |
| `basis_pct` | `basisRate` / `basis_rate` | calculated | `basisRate` or calculated | calculated | calculated |
| `premium` | `premium` if present | premium index endpoint / premium index kline | use only if endpoint semantics confirms premium | funding-rate `premium` | `premium` |
| `premium_pct` | `premiumRate` / calculated | calculated | calculated | calculated | calculated |
| `next_funding_time_ms` | `nextFundingTime` | `nextFundingTime` | `nextFundingTime` | `nextFundingTime` | derived from funding cadence |

## ExchangeMetadata

Назначение: справочник venues, capabilities, sync policy и fee defaults.

### Поля

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | Версия схемы. |
| `exchange_id` | string | yes | Stable slug: `binance`, `bybit`, `okx`, `hyperliquid`. |
| `name` | string | yes | Display name. |
| `exchange_type` | string | yes | `cex`, `perp_dex`, `aggregator`. |
| `status` | string | yes | `active`, `degraded`, `disabled`. |
| `supports_spot` | boolean | yes | Spot support. |
| `supports_perp` | boolean | yes | Perp support. |
| `supports_ws` | boolean | yes | Public WebSocket support. |
| `supports_private_trading` | boolean | yes | Trading API support in DeltaGrid. |
| `rate_limit_per_minute` | integer | no | Safe internal limit. |
| `maker_fee_rate_default` | number | no | Decimal fraction. |
| `taker_fee_rate_default` | number | no | Decimal fraction. |
| `metadata` | object | no | Rate limit, docs URL, quirks. |
| `updated_at_ms` | integer | yes | Последнее обновление справочника. |

### Пример JSON

```json
{
  "schema_version": 1,
  "exchange_id": "okx",
  "name": "OKX",
  "exchange_type": "cex",
  "status": "active",
  "supports_spot": true,
  "supports_perp": true,
  "supports_ws": true,
  "supports_private_trading": true,
  "rate_limit_per_minute": 1800,
  "maker_fee_rate_default": 0.0002,
  "taker_fee_rate_default": 0.0005,
  "metadata": {
    "requires_passphrase": true,
    "symbol_format": "BTC-USDT-SWAP"
  },
  "updated_at_ms": 1717200000000
}
```

### Provider mapping

| Canonical field | CoinGlass | Binance | Bybit | OKX | Hyperliquid |
| --- | --- | --- | --- | --- | --- |
| `exchange_id` | `exchangeName` / normalized exchange key | fixed `binance` | fixed `bybit` | fixed `okx` | fixed `hyperliquid` |
| `name` | `exchangeName` | exchange info context | exchange name from config | exchange name from config | exchange name from config |
| `exchange_type` | aggregator metadata | `cex` | `cex` | `cex` | `perp_dex` |
| `status` | provider status if available | exchange info / connector health | connector health | connector health | connector health |
| `supports_spot` | exchange capability aggregate | exchange info symbols include spot only in Spot API; futures API is separate | instruments categories | `instType` includes `SPOT` | `false` |
| `supports_perp` | exchange capability aggregate | USD-M/COIN-M futures exchange info | `category=linear` / `inverse` | `SWAP` instruments | `true` |
| `supports_ws` | provider docs | exchange public streams | public WS | public WS | public WS |
| `rate_limit_per_minute` | plan-specific | exchange info `rateLimits` | docs/config | docs/config | docs/config |
| `maker_fee_rate_default` | fee endpoint or config | account/commission endpoints or config | fee-rate endpoint or config | trade fee endpoint or config | protocol fee schedule/config |
| `taker_fee_rate_default` | fee endpoint or config | account/commission endpoints or config | fee-rate endpoint or config | trade fee endpoint or config | protocol fee schedule/config |

## InstrumentMetadata

Назначение: справочник торговых инструментов и их constraints.

### Поля

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | Версия схемы. |
| `instrument_id` | string | yes | Stable internal id: `{exchange}:{symbol}`. |
| `exchange_id` | string | yes | Venue slug. |
| `symbol` | string | yes | Canonical symbol. |
| `provider_symbol` | string | yes | Символ биржи/провайдера. |
| `base_asset` | string | yes | Base asset. |
| `quote_asset` | string | yes | Quote asset. |
| `settle_asset` | string | no | Settlement asset. |
| `instrument_type` | string | yes | `spot`, `perp`, `future`, `option`, `index`. |
| `contract_type` | string | no | `linear`, `inverse`, `quanto`, `spot`. |
| `contract_size` | number | no | Contract value. |
| `tick_size` | number | no | Price step. |
| `lot_size` | number | no | Quantity step. |
| `min_qty` | number | no | Minimum order quantity. |
| `min_notional` | number | no | Minimum notional. |
| `price_precision` | integer | no | Price precision if provider exposes it. |
| `quantity_precision` | integer | no | Quantity precision if provider exposes it. |
| `status` | string | yes | `active`, `prelaunch`, `settled`, `delisted`, `disabled`. |
| `listed_at_ms` | integer | no | Listing time. |
| `expires_at_ms` | integer | no | Expiry/delivery time. |
| `funding_interval_hours` | number | no | Funding cadence for perps. |
| `max_leverage` | number | no | Max leverage. |
| `metadata` | object | no | Provider-specific constraints. |
| `updated_at_ms` | integer | yes | Last metadata update. |

### Пример JSON

```json
{
  "schema_version": 1,
  "instrument_id": "bybit:BTC-USDT-PERP",
  "exchange_id": "bybit",
  "symbol": "BTC-USDT-PERP",
  "provider_symbol": "BTCUSDT",
  "base_asset": "BTC",
  "quote_asset": "USDT",
  "settle_asset": "USDT",
  "instrument_type": "perp",
  "contract_type": "linear",
  "contract_size": 1.0,
  "tick_size": 0.1,
  "lot_size": 0.001,
  "min_qty": 0.001,
  "min_notional": 5.0,
  "price_precision": 1,
  "quantity_precision": 3,
  "status": "active",
  "listed_at_ms": 1650000000000,
  "expires_at_ms": null,
  "funding_interval_hours": 8,
  "max_leverage": 100,
  "metadata": {
    "unified_margin_trade": true
  },
  "updated_at_ms": 1717200000000
}
```

### Provider mapping

| Canonical field | CoinGlass | Binance | Bybit | OKX | Hyperliquid |
| --- | --- | --- | --- | --- | --- |
| `instrument_id` | normalized `{exchange}:{canonical}` | `{exchange}:{canonical}` | `{exchange}:{canonical}` | `{exchange}:{canonical}` | `{exchange}:{canonical}` |
| `provider_symbol` | `symbol` | `symbols[].symbol` | `list[].symbol` | `instId` | `universe[].name` |
| `base_asset` | `baseAsset` / parsed | `baseAsset` | `baseCoin` | `baseCcy` or parsed `instId` | `name` mapped to asset |
| `quote_asset` | `quoteAsset` / parsed | `quoteAsset` | `quoteCoin` | `quoteCcy` or parsed `instId` | usually `USDC` for perps |
| `settle_asset` | `settleAsset` / parsed | `marginAsset` | `settleCoin` | `settleCcy` | `USDC` |
| `instrument_type` | `instrumentType` / parsed | futures exchange info context | request `category` / `contractType` | `instType` | `perp` |
| `contract_type` | provider-specific | `contractType`, linear by quote/margin asset | `contractType` | `ctType` if available, else parsed | linear perp |
| `contract_size` | `contractSize` | `contractSize` if present, else `1` for many USDT-M pairs | `lotSizeFilter` semantics, often `1` | `ctVal`, `ctMult`, `ctValCcy` | size is coin amount; use `1` unit convention |
| `tick_size` | `tickSize` | filter `PRICE_FILTER.tickSize` | `priceFilter.tickSize` | `tickSz` | derived from price decimals if available |
| `lot_size` | `stepSize` | filter `LOT_SIZE.stepSize` | `lotSizeFilter.qtyStep` | `lotSz` | `szDecimals` gives quantity precision |
| `min_qty` | `minQty` | filter `LOT_SIZE.minQty` | `lotSizeFilter.minOrderQty` | `minSz` | derived from `szDecimals`, not always explicit |
| `min_notional` | `minNotional` | filter `MIN_NOTIONAL.notional` | `lotSizeFilter.minNotionalValue` | derived/config | not explicit |
| `price_precision` | provider-specific | `pricePrecision` | from `priceScale` or tick size | from `tickSz` | from asset context / metadata if available |
| `quantity_precision` | provider-specific | `quantityPrecision` | from `qtyStep` | from `lotSz` | `szDecimals` |
| `status` | `status` | `status` | `status` | `state` | `isDelisted` / universe flags |
| `listed_at_ms` | `launchTime` if present | `onboardDate` | `launchTime` | `listTime` | absent |
| `expires_at_ms` | `deliveryTime` if present | `deliveryDate` | `deliveryTime` | `expTime` | absent for perps |
| `funding_interval_hours` | provider-specific | exchange schedule/config | `fundingInterval / 60` | derived from funding cadence | funding cadence/config |
| `max_leverage` | provider-specific | leverage brackets endpoint or config | `leverageFilter.maxLeverage` | `lever` | `maxLeverage` |

## Валидационные правила

- `interval_start_ms < interval_end_ms`.
- Для `OHLCV_1m`: `high >= low`, `high >= open`, `high >= close`, `low <= open`, `low <= close`.
- `funding_rate` хранится как decimal fraction, не как процент.
- `long_ratio` и `short_ratio` хранятся в диапазоне `0..1`.
- Если `long_ratio` и `short_ratio` есть, `long_short_ratio = long_ratio / short_ratio`.
- Если `basis` и `index_price` есть, `basis_pct = basis / index_price`.
- Если provider отдаёт агрегированные liquidation buckets, `is_aggregate = true`, а event-specific поля могут быть `null`.
- `raw_payload` можно хранить только в audit/debug слое, не использовать как основной источник бизнес-логики.

## Факт / допущение / рекомендация

### Факт

- В текущем проекте уже есть provider layer для CoinGlass/GeckoTerminal, exchange connectors для Binance, Bybit, OKX, Hyperliquid и существующая документация по data status lifecycle.
- В проекте не были найдены файлы `PRODUCT_STRATEGY.md`, `DATA_PRIORITY.md`, `API_INTEGRATION_PLAN.md`, `BACKTESTING_SPEC.md`, `UX_STRUCTURE.md`, `IMPLEMENTATION_ROADMAP.md`, `DATA_QUALITY_RISKS.md` в корне, на Desktop и в OneDrive на момент подготовки документа.
- Binance, Bybit, OKX и Hyperliquid используют разные форматы символов и timestamp-полей, поэтому normalization layer обязателен перед записью в БД.

### Допущение

- CoinGlass mapping описан как provider-compatible слой, потому что точные имена полей зависят от версии endpoint и тарифного плана.
- Для Hyperliquid canonical quote/settle asset по perp instruments принят как `USDC`, если конкретный asset context не говорит иначе.
- SQLite schema на следующем этапе может хранить decimal values как `REAL`, но в Python-слое финансовые расчёты желательно делать через `Decimal`.

### Рекомендация

- Перед реализацией ingest добавить маленький adapter contract test на каждый provider endpoint: raw fixture -> canonical JSON -> DB row.
- Не смешивать `provider_symbol` и `symbol`: вся бизнес-логика должна работать только с canonical `symbol`.
- Для liquidation данных сначала поддержать агрегированные buckets от CoinGlass и event-level потоки Binance/Bybit/OKX как разные режимы одного контракта.
