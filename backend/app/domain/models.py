import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Date, Float, Boolean, Integer, BigInteger, create_engine, ForeignKey, Text, DECIMAL, UniqueConstraint, PrimaryKeyConstraint, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


# Phase 1 tables (with Phase 2 user_id extension)
class Preference(Base):
    __tablename__ = "preferences"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    key = Column(String, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "key", name="uix_user_preference_key"),)


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    instrument_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "instrument_id", name="uix_user_favorite"),)


class PinnedInstrument(Base):
    __tablename__ = "pinned"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    instrument_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "instrument_id", name="uix_user_pinned"),)


# Phase 2: Auth
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=True)
    username = Column(String, unique=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    telegram_id = Column(String, unique=True, nullable=True)
    wallet_address = Column(String, unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    plan = Column(String, default="free")
    session_version = Column(Integer, default=1)
    plan_started_at = Column(DateTime, nullable=True)
    plan_expires_at = Column(DateTime, nullable=True)
    feature_flags_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Phase 2: Paper Trading
class PaperAccount(Base):
    __tablename__ = "paper_accounts"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, default="Demo Account")
    initial_balance = Column(DECIMAL(18, 8), default=10000.0)
    current_balance = Column(DECIMAL(18, 8), default=10000.0)
    currency = Column(String, default="USDT")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id = Column(String, primary_key=True, default=generate_uuid)
    account_id = Column(String, ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy = Column(String, nullable=False)
    instrument_id = Column(String, nullable=False)
    side = Column(String, nullable=False)
    entry_price = Column(DECIMAL(18, 8), nullable=False)
    exit_price = Column(DECIMAL(18, 8), nullable=True)
    quantity = Column(DECIMAL(18, 8), nullable=False)
    status = Column(String, default="open")
    pnl = Column(DECIMAL(18, 8), nullable=True)
    pnl_pct = Column(DECIMAL(10, 4), nullable=True)
    fee_pct = Column(DECIMAL(10, 4), default=0.10)
    slippage_pct = Column(DECIMAL(10, 4), default=0.0)
    metadata_json = Column(Text, nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)


class StrategyRun(Base):
    __tablename__ = "strategy_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    account_id = Column(String, ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy = Column(String, nullable=False)
    config_json = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)


class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"

    id = Column(String, primary_key=True, default=generate_uuid)
    account_id = Column(String, ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(18, 8), default=0)
    max_drawdown_pct = Column(DECIMAL(10, 4), nullable=True)
    sharpe_ratio = Column(DECIMAL(10, 4), nullable=True)
    win_rate_pct = Column(DECIMAL(10, 4), nullable=True)
    snapshot_at = Column(DateTime, default=datetime.utcnow)


# Phase 2: Billing / Referral hooks
class Referral(Base):
    __tablename__ = "referrals"

    id = Column(String, primary_key=True, default=generate_uuid)
    referrer_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    code = Column(String, unique=True, nullable=False)
    status = Column(String, default="pending")
    reward_amount = Column(DECIMAL(18, 8), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    converted_at = Column(DateTime, nullable=True)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    plan = Column(String, nullable=False)
    amount = Column(DECIMAL(18, 8), nullable=True)
    currency = Column(String, default="USDT")
    provider = Column(String, nullable=True)
    status = Column(String, default="pending")
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)


# =============================================================================
# Phase 3: Execution / Auto-Trader Foundation
# =============================================================================

class ExchangeAccount(Base):
    __tablename__ = "exchange_accounts"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange_name = Column(String, nullable=False)
    account_label = Column(String, default="Main")
    account_type = Column(String, default="spot")
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "exchange_name", "account_label", name="uix_user_exchange_label"),)


class ExchangeKey(Base):
    __tablename__ = "exchange_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    account_id = Column(String, ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    api_key_encrypted = Column(Text, nullable=False)
    api_secret_encrypted = Column(Text, nullable=False)
    passphrase_encrypted = Column(Text, nullable=True)
    permissions_json = Column(Text, default='{"read": true, "trade": false, "withdraw": false}')
    is_testnet = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    last_error_message = Column(Text, nullable=True)


class ConnectorCapability(Base):
    __tablename__ = "connector_capabilities"

    exchange_name = Column(String, primary_key=True)
    supports_spot = Column(Boolean, default=False)
    supports_perp = Column(Boolean, default=False)
    supports_margin = Column(Boolean, default=False)
    supports_market_order = Column(Boolean, default=False)
    supports_limit_order = Column(Boolean, default=False)
    supports_stop_loss = Column(Boolean, default=False)
    supports_cancel = Column(Boolean, default=False)
    supports_ws = Column(Boolean, default=False)
    rate_limit_requests_per_minute = Column(Integer, default=1200)


class RealOrder(Base):
    __tablename__ = "real_orders"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String, ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    client_order_id = Column(String, nullable=False)
    exchange_order_id = Column(String, nullable=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    order_type = Column(String, nullable=False)
    quantity = Column(DECIMAL(18, 8), nullable=False)
    filled_quantity = Column(DECIMAL(18, 8), default=0)
    remaining_quantity = Column(DECIMAL(18, 8), nullable=True)
    price = Column(DECIMAL(18, 8), nullable=True)
    avg_fill_price = Column(DECIMAL(18, 8), nullable=True)
    stop_price = Column(DECIMAL(18, 8), nullable=True)
    status = Column(String, default="intent")
    fee_amount = Column(DECIMAL(18, 8), nullable=True)
    fee_currency = Column(String, nullable=True)
    strategy = Column(String, nullable=True)
    strategy_run_id = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    filled_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OrderEvent(Base):
    __tablename__ = "order_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("real_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=True)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExecutionRun(Base):
    __tablename__ = "execution_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=True)
    strategy = Column(String, nullable=True)
    status = Column(String, default="running")
    is_live = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)


class RiskRule(Base):
    __tablename__ = "risk_rules"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String, ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    rule_type = Column(String, nullable=False)
    symbol = Column(String, nullable=True)
    threshold_value = Column(DECIMAL(18, 8), nullable=False)
    comparison = Column(String, default="lte")
    action = Column(String, default="block")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PositionSnapshot(Base):
    __tablename__ = "position_snapshots"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String, ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    quantity = Column(DECIMAL(18, 8), default=0)
    avg_entry_price = Column(DECIMAL(18, 8), nullable=True)
    unrealized_pnl = Column(DECIMAL(18, 8), nullable=True)
    realized_pnl = Column(DECIMAL(18, 8), nullable=True)
    snapshot_at = Column(DateTime, default=datetime.utcnow)


class LiveTradeSession(Base):
    __tablename__ = "live_trade_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String, ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_orders_placed = Column(Integer, default=0)
    total_orders_filled = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(18, 8), default=0)
    metadata_json = Column(Text, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    details_json = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# =============================================================================
# Phase 4: Provider Enrichments & Health
# =============================================================================

class ProviderHealth(Base):
    __tablename__ = "provider_health"

    id = Column(String, primary_key=True, default=generate_uuid)
    provider_name = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False, default="healthy")
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    last_error_message = Column(Text, nullable=True)
    avg_response_ms = Column(Integer, nullable=True)
    failure_count_24h = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MarketEnrichment(Base):
    __tablename__ = "market_enrichments"

    id = Column(String, primary_key=True, default=generate_uuid)
    symbol = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False)
    enrichment_type = Column(String, nullable=False, index=True)
    value_decimal = Column(DECIMAL(18, 8), nullable=True)
    value_json = Column(Text, nullable=True)
    currency = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    ttl_seconds = Column(Integer, default=300)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProviderSyncLog(Base):
    __tablename__ = "provider_sync_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    provider_name = Column(String, nullable=False, index=True)
    sync_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    records_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RealtimeFeedSession(Base):
    __tablename__ = "realtime_feed_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    feed_type = Column(String, nullable=False)
    exchange = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    symbols = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String, default="active")
    error_message = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)


class StreamEvent(Base):
    __tablename__ = "stream_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("realtime_feed_sessions.id"), nullable=False)
    event_type = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    payload_json = Column(Text, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)


# =============================================================================
# Phase 4: Alerting Engine
# =============================================================================

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)
    symbol = Column(String, nullable=True)
    threshold_value = Column(DECIMAL(18, 8), nullable=True)
    comparison = Column(String, default="gte")
    cooldown_minutes = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    severity = Column(String, default="info")
    channels_json = Column(Text, default='["email"]')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    rule_id = Column(String, ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String, nullable=False)
    symbol = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    severity = Column(String, nullable=True)
    dedup_hash = Column(String, nullable=True)
    triggered_at = Column(DateTime, default=datetime.utcnow)


class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"

    id = Column(String, primary_key=True, default=generate_uuid)
    alert_event_id = Column(String, ForeignKey("alert_events.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String, nullable=False)
    status = Column(String, default="pending")
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    metadata_json = Column(Text, nullable=True)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    email_enabled = Column(Boolean, default=True)
    email_address = Column(String, nullable=True)
    web_push_enabled = Column(Boolean, default=False)
    web_push_subscription_json = Column(Text, nullable=True)
    telegram_enabled = Column(Boolean, default=False)
    telegram_chat_id = Column(String, nullable=True)
    market_alerts_enabled = Column(Boolean, default=True)
    execution_alerts_enabled = Column(Boolean, default=True)
    risk_alerts_enabled = Column(Boolean, default=True)
    rwa_alerts_enabled = Column(Boolean, default=True)
    min_severity = Column(String, default="info")
    quiet_hours_start = Column(Integer, nullable=True)
    quiet_hours_end = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# Phase 5: RWA & Treasury Intelligence
# =============================================================================

class RwaAsset(Base):
    __tablename__ = "rwa_assets"

    id = Column(String, primary_key=True, default=generate_uuid)
    symbol = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    asset_class = Column(String, default="rwa", nullable=False)
    issuer = Column(String, nullable=True)
    blockchain = Column(String, nullable=True)
    contract_address = Column(String, nullable=True)
    decimals = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    is_executable = Column(Boolean, default=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RwaAssetSnapshot(Base):
    __tablename__ = "rwa_asset_snapshots"

    id = Column(String, primary_key=True, default=generate_uuid)
    asset_id = Column(String, ForeignKey("rwa_assets.id", ondelete="CASCADE"), nullable=False)
    source = Column(String, nullable=False)
    source_quality = Column(String, default="verified", nullable=False)
    price_usd = Column(DECIMAL(18, 8), nullable=True)
    nav_usd = Column(DECIMAL(18, 8), nullable=True)
    market_cap_usd = Column(DECIMAL(24, 8), nullable=True)
    total_supply = Column(DECIMAL(24, 8), nullable=True)
    volume_24h_usd = Column(DECIMAL(24, 8), nullable=True)
    yield_apr = Column(DECIMAL(10, 4), nullable=True)
    premium_discount_pct = Column(DECIMAL(10, 4), nullable=True)
    raw_payload_json = Column(Text, nullable=True)
    fetched_at = Column(DateTime, nullable=False)
    next_expected_update_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TreasuryEntity(Base):
    __tablename__ = "treasury_entities"

    id = Column(String, primary_key=True, default=generate_uuid)
    entity_type = Column(String, nullable=False)
    name = Column(String, nullable=False, unique=True)
    ticker = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    website_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TreasurySnapshot(Base):
    __tablename__ = "treasury_snapshots"

    id = Column(String, primary_key=True, default=generate_uuid)
    entity_id = Column(String, ForeignKey("treasury_entities.id", ondelete="CASCADE"), nullable=False)
    source = Column(String, nullable=False)
    source_quality = Column(String, default="verified", nullable=False)
    btc_holdings = Column(DECIMAL(18, 8), nullable=True)
    btc_value_usd = Column(DECIMAL(24, 8), nullable=True)
    total_treasury_usd = Column(DECIMAL(24, 8), nullable=True)
    shares_outstanding = Column(DECIMAL(24, 8), nullable=True)
    btc_per_share = Column(DECIMAL(18, 8), nullable=True)
    raw_payload_json = Column(Text, nullable=True)
    report_date = Column(Date, nullable=True)
    fetched_at = Column(DateTime, nullable=False)
    next_expected_update_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TokenizationPlatform(Base):
    __tablename__ = "tokenization_platforms"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    website_url = Column(String, nullable=True)
    tvl_usd = Column(DECIMAL(24, 8), nullable=True)
    active_pools = Column(Integer, nullable=True)
    blockchain = Column(String, nullable=True)
    governance_token = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(Text, nullable=True)
    last_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# =============================================================================
# Phase 6: Capability & Feature Flag Foundation
# =============================================================================

class PlanCapability(Base):
    __tablename__ = "plan_capabilities"

    id = Column(String, primary_key=True, default=generate_uuid)
    plan_id = Column(String, nullable=False, index=True)
    feature_key = Column(String, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    limit_value = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("plan_id", "feature_key", name="uix_plan_feature"),)


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    flag_key = Column(String, nullable=False)
    flag_value = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "flag_key", name="uix_user_flag"),)


# =============================================================================
# Data Layer — Backtesting + Market Data Ingestion
# =============================================================================

class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(String, primary_key=True, default=generate_uuid)
    canonical_symbol = Column(String, nullable=False)
    base_asset = Column(String, nullable=False)
    quote_asset = Column(String, nullable=False)
    instrument_type = Column(String, nullable=False)   # perp | spot | future
    exchange = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    aliases = relationship("InstrumentAlias", back_populates="instrument", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("canonical_symbol", "exchange", "instrument_type", name="uix_instrument"),
    )


class InstrumentAlias(Base):
    __tablename__ = "instrument_aliases"

    id = Column(String, primary_key=True, default=generate_uuid)
    instrument_id = Column(String, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)
    alias = Column(String, nullable=False)
    alias_type = Column(String, nullable=False)   # ticker | cg_id | cg_symbol
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    instrument = relationship("Instrument", back_populates="aliases")

    __table_args__ = (
        UniqueConstraint("provider", "alias", name="uix_provider_alias"),
    )


class DataOhlcv(Base):
    __tablename__ = "ohlcv"

    timestamp = Column(BigInteger, nullable=False)
    symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    interval = Column(String, nullable=False)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    quote_volume = Column(Float, nullable=True)
    trades_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        PrimaryKeyConstraint("timestamp", "symbol", "exchange", "interval", name="pk_ohlcv"),
        Index("idx_ohlcv_lookup", "symbol", "exchange", "interval", "timestamp"),
    )


class DataFundingRate(Base):
    __tablename__ = "funding_rates"

    timestamp = Column(BigInteger, nullable=False)
    symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    funding_rate = Column(Float, nullable=True)
    next_funding_time = Column(BigInteger, nullable=True)
    interval = Column(String, default="8h")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        PrimaryKeyConstraint("timestamp", "symbol", "exchange", name="pk_funding_rates"),
        Index("idx_funding_lookup", "symbol", "exchange", "timestamp"),
    )


class DataOpenInterest(Base):
    __tablename__ = "open_interest"

    timestamp = Column(BigInteger, nullable=False)
    symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    interval = Column(String, nullable=False)
    oi_usd = Column(Float, nullable=True)
    oi_coins = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        PrimaryKeyConstraint("timestamp", "symbol", "exchange", "interval", name="pk_open_interest"),
        Index("idx_oi_lookup", "symbol", "exchange", "interval", "timestamp"),
    )


class DataLiquidation(Base):
    __tablename__ = "liquidations"

    timestamp = Column(BigInteger, nullable=False)
    symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    side = Column(String, nullable=False)
    quantity = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    value_usd = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        PrimaryKeyConstraint("timestamp", "symbol", "exchange", "side", name="pk_liquidations"),
        Index("idx_liq_lookup", "symbol", "exchange", "timestamp"),
    )


class DataLongShortRatio(Base):
    __tablename__ = "long_short_ratio"

    timestamp = Column(BigInteger, nullable=False)
    symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    interval = Column(String, nullable=False)
    long_ratio = Column(Float, nullable=True)
    short_ratio = Column(Float, nullable=True)
    long_account_ratio = Column(Float, nullable=True)
    short_account_ratio = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        PrimaryKeyConstraint("timestamp", "symbol", "exchange", "interval", name="pk_long_short_ratio"),
        Index("idx_ls_lookup", "symbol", "exchange", "interval", "timestamp"),
    )


class BasisPremium(Base):
    __tablename__ = "basis_premium"

    id = Column(String, primary_key=True, default=generate_uuid)
    symbol = Column(String, nullable=False, index=True)
    exchange = Column(String, nullable=False, index=True)
    spot_price = Column(Float, nullable=True)
    perp_price = Column(Float, nullable=True)
    basis_pct = Column(Float, nullable=True)
    premium_pct = Column(Float, nullable=True)
    timestamp = Column(BigInteger, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExchangeFee(Base):
    __tablename__ = "exchange_fees"

    id = Column(String, primary_key=True, default=generate_uuid)
    exchange = Column(String, nullable=False, unique=True)
    maker_fee_pct = Column(Float, nullable=True)
    taker_fee_pct = Column(Float, nullable=True)
    withdrawal_fee_json = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProviderSyncRun(Base):
    __tablename__ = "provider_sync_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    provider_name = Column(String, nullable=False, index=True)
    sync_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    start_time = Column(BigInteger, nullable=True)
    end_time = Column(BigInteger, nullable=True)
    records_fetched = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_sync_runs_provider", "provider_name", "sync_type", "created_at"),
    )


class DataQualityLog(Base):
    __tablename__ = "data_quality_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    table_name = Column(String, nullable=False)
    symbol = Column(String, nullable=True)
    exchange = Column(String, nullable=True)
    check_type = Column(String, nullable=False)   # gap | duplicate | outlier | stale
    severity = Column(String, default="warning")  # info | warning | critical
    description = Column(Text, nullable=True)
    timestamp = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BackfillJobRecord(Base):
    __tablename__ = "backfill_jobs"

    id = Column(String, primary_key=True)
    symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    data_type = Column(String, nullable=False)
    interval = Column(String, nullable=False)
    start_time = Column(BigInteger, nullable=False)
    end_time = Column(BigInteger, nullable=False)
    status = Column(String, default="pending")
    records_fetched = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(BigInteger, nullable=True)
    completed_at = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_jobs_status", "status", "exchange"),
        Index("idx_jobs_lookup", "symbol", "exchange", "data_type", "status"),
    )


class BacktestConfig(Base):
    __tablename__ = "backtest_configs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    strategy = Column(String, nullable=False)
    symbols_json = Column(Text, nullable=False)          # ["BTC", "ETH"]
    exchanges_json = Column(Text, nullable=False)        # ["binance"]
    start_time = Column(Integer, nullable=False)
    end_time = Column(Integer, nullable=False)
    interval = Column(String, default="1m")
    initial_balance = Column(DECIMAL(18, 8), default=10000)
    fee_pct = Column(Float, default=0.1)
    config_json = Column(Text, nullable=True)            # strategy-specific params
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    config_id = Column(String, ForeignKey("backtest_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, default="pending")   # pending | running | completed | failed
    total_trades = Column(Integer, default=0)
    win_count = Column(Integer, default=0)
    loss_count = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(18, 8), default=0)
    total_pnl_pct = Column(DECIMAL(10, 4), default=0)
    max_drawdown_pct = Column(DECIMAL(10, 4), nullable=True)
    sharpe_ratio = Column(DECIMAL(10, 4), nullable=True)
    sortino_ratio = Column(DECIMAL(10, 4), nullable=True)
    win_rate_pct = Column(DECIMAL(10, 4), nullable=True)
    avg_trade_pnl = Column(DECIMAL(18, 8), nullable=True)
    profit_factor = Column(DECIMAL(10, 4), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id = Column(String, primary_key=True, default=generate_uuid)
    result_id = Column(String, ForeignKey("backtest_results.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    side = Column(String, nullable=False)   # long | short
    entry_time = Column(BigInteger, nullable=False)
    exit_time = Column(BigInteger, nullable=True)
    entry_price = Column(DECIMAL(18, 8), nullable=False)
    exit_price = Column(DECIMAL(18, 8), nullable=True)
    quantity = Column(DECIMAL(18, 8), nullable=False)
    pnl = Column(DECIMAL(18, 8), nullable=True)
    pnl_pct = Column(DECIMAL(10, 4), nullable=True)
    fee = Column(DECIMAL(18, 8), default=0)
    status = Column(String, default="open")   # open | closed
    created_at = Column(DateTime, default=datetime.utcnow)


class BacktestEquity(Base):
    __tablename__ = "backtest_equity"

    id = Column(String, primary_key=True, default=generate_uuid)
    result_id = Column(String, ForeignKey("backtest_results.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(BigInteger, nullable=False)
    equity = Column(DECIMAL(18, 8), nullable=False)
    realized_pnl = Column(DECIMAL(18, 8), default=0)
    unrealized_pnl = Column(DECIMAL(18, 8), default=0)
    drawdown_pct = Column(DECIMAL(10, 4), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_equity_result_ts", "result_id", "timestamp"),
    )
