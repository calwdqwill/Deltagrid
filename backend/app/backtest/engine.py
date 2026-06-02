"""Backtest Engine — bar-by-bar event loop for perpetual futures backtesting.

Ключевой принцип — structural look-ahead bias elimination:
- При обработке бара t в памяти доступны данные только до t включительно
- Данные t+1, t+2, ... не загружены и недоступны
- Каждый бар обрабатывается строго последовательно
"""

import time
from typing import List, Optional, Tuple

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.backtest.config import BacktestConfig, EquityPoint, Position, Trade
from app.backtest.fee_model import calculate_trade_fee
from app.backtest.funding_model import get_funding_payment, get_funding_rate_at_time
from app.backtest.metrics import (
    BacktestResult,
    calculate_drawdown,
    calculate_sharpe,
    calculate_sortino,
    decompose_pnl,
)
from app.backtest.slippage_model import calculate_slippage
from app.backtest.strategies.registry import BaseStrategy
from app.backtest.strategies import STRATEGY_REGISTRY


class BacktestEngine:
    """Bar-by-bar event loop for perpetual futures backtesting."""

    def __init__(self, db_session: Session, config: BacktestConfig):
        self.db = db_session
        self.config = config
        self.initial_equity = config.position_size_usd

    def run(self) -> BacktestResult:
        """Main entry point. Executes full backtest."""
        start_time = time.time()

        # Resolve strategy class
        strategy_class = STRATEGY_REGISTRY.get(self.config.strategy_type)
        if strategy_class is None:
            raise ValueError(
                f"Unknown strategy: {self.config.strategy_type}. "
                f"Available: {list(STRATEGY_REGISTRY.keys())}"
            )

        strategy: BaseStrategy = strategy_class(params=self.config.params)

        # Load data
        df_ohlcv, df_funding = self._load_data(
            self.config.symbol,
            self.config.exchange,
            self.config.start_ms,
            self.config.end_ms,
        )

        if df_ohlcv is None or df_ohlcv.empty:
            raise ValueError(
                f"No OHLCV data found for {self.config.symbol}/{self.config.exchange} "
                f"in range {self.config.start_ms}–{self.config.end_ms}"
            )

        # Merge funding rate into OHLCV for easy access during bar loop
        if df_funding is not None and not df_funding.empty:
            # Forward-fill funding rate onto each 1m bar
            df_combined = pd.merge_asof(
                df_ohlcv.reset_index(),
                df_funding.reset_index(),
                on="timestamp",
                direction="backward",
            ).set_index("timestamp")
        else:
            df_combined = df_ohlcv.copy()
            df_combined["funding_rate"] = 0.0

        # For liquidation strategy, load and merge liquidation data
        if self.config.strategy_type == "liquidation_cascade_fade":
            df_liq = self._load_liquidations(
                self.config.symbol,
                self.config.exchange,
                self.config.start_ms,
                self.config.end_ms,
            )
            if df_liq is not None and not df_liq.empty:
                # Sum liquidation value per minute
                df_liq_min = (
                    df_liq.groupby("timestamp")["value_usd"]
                    .sum()
                    .reindex(df_combined.index, fill_value=0.0)
                )
                df_combined["liquidation_value_usd"] = df_liq_min
            else:
                df_combined["liquidation_value_usd"] = 0.0

            # Pre-compute indicators (no look-ahead)
            df_combined["liq_sum_1h"] = (
                df_combined["liquidation_value_usd"].rolling(window=60, min_periods=1).sum()
            )
            df_combined["price_change_1h"] = df_combined["close"].pct_change(periods=60)

        # Run bar loop
        trades, equity_curve = self._bar_loop(df_combined, strategy)

        # Calculate metrics
        result = self._build_result(
            trades,
            equity_curve,
            df_combined,
            strategy,
            elapsed_ms=int((time.time() - start_time) * 1000),
        )

        return result

    def _load_data(
        self,
        symbol: str,
        exchange: str,
        start_ms: int,
        end_ms: int,
    ) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Loads OHLCV + funding data from SQLite.
        Returns: (df_ohlcv, df_funding) indexed by timestamp
        """
        # Load OHLCV
        query_ohlcv = text(
            """
            SELECT timestamp, open, high, low, close, volume
            FROM ohlcv
            WHERE symbol = :symbol
              AND exchange = :exchange
              AND interval = '1m'
              AND timestamp >= :start_ms
              AND timestamp <= :end_ms
            ORDER BY timestamp
            """
        )
        result = self.db.execute(
            query_ohlcv,
            {
                "symbol": symbol,
                "exchange": exchange,
                "start_ms": start_ms,
                "end_ms": end_ms,
            },
        )
        rows = result.fetchall()
        if not rows:
            return None, None

        df_ohlcv = pd.DataFrame(
            rows, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df_ohlcv["timestamp"] = pd.to_numeric(df_ohlcv["timestamp"])
        df_ohlcv = df_ohlcv.set_index("timestamp").sort_index()

        # Load funding rates
        query_funding = text(
            """
            SELECT timestamp, funding_rate
            FROM funding_rates
            WHERE symbol = :symbol
              AND exchange = :exchange
              AND timestamp >= :start_ms
              AND timestamp <= :end_ms
            ORDER BY timestamp
            """
        )
        result = self.db.execute(
            query_funding,
            {
                "symbol": symbol,
                "exchange": exchange,
                "start_ms": start_ms,
                "end_ms": end_ms,
            },
        )
        rows_funding = result.fetchall()
        if rows_funding:
            df_funding = pd.DataFrame(rows_funding, columns=["timestamp", "funding_rate"])
            df_funding["timestamp"] = pd.to_numeric(df_funding["timestamp"])
            df_funding = df_funding.set_index("timestamp").sort_index()
        else:
            df_funding = None

        return df_ohlcv, df_funding

    def _load_liquidations(
        self,
        symbol: str,
        exchange: str,
        start_ms: int,
        end_ms: int,
    ) -> Optional[pd.DataFrame]:
        """Load liquidation data from DB."""
        query = text(
            """
            SELECT timestamp, side, value_usd
            FROM liquidations
            WHERE symbol = :symbol
              AND exchange = :exchange
              AND timestamp >= :start_ms
              AND timestamp <= :end_ms
            ORDER BY timestamp
            """
        )
        result = self.db.execute(
            query,
            {
                "symbol": symbol,
                "exchange": exchange,
                "start_ms": start_ms,
                "end_ms": end_ms,
            },
        )
        rows = result.fetchall()
        if not rows:
            return None

        df = pd.DataFrame(rows, columns=["timestamp", "side", "value_usd"])
        df["timestamp"] = pd.to_numeric(df["timestamp"])
        return df.set_index("timestamp").sort_index()

    def _bar_loop(
        self,
        df: pd.DataFrame,
        strategy: BaseStrategy,
    ) -> Tuple[List[Trade], List[EquityPoint]]:
        """
        Core event loop. Iterates bar by bar.
        At each bar t: only df.iloc[:t+1] is conceptually available to strategy.
        """
        trades: List[Trade] = []
        equity_curve: List[EquityPoint] = []

        position = Position()
        equity = self.initial_equity  # tracks cash-like value after realized items
        peak_equity = equity

        is_maker = self.config.fee_type == "maker"

        for t in range(len(df)):
            current_bar = df.iloc[t]
            timestamp_ms = int(df.index[t])
            is_last_bar = (t == len(df) - 1)

            # ---- Funding payment ----
            if position.side != "flat":
                funding_rate = get_funding_rate_at_time(
                    timestamp_ms,
                    df[["funding_rate"]] if "funding_rate" in df.columns else None,
                )
                payment = get_funding_payment(
                    timestamp_ms=timestamp_ms,
                    position_side=position.side,
                    size_usd=position.size_usd,
                    funding_rate=funding_rate,
                    exchange=self.config.exchange,
                )
                if payment != 0:
                    # get_funding_payment: positive = trader pays, negative = receives
                    # funding_pnl tracks PnL contribution: positive = gain, negative = cost
                    position.funding_pnl -= payment
                    equity -= payment  # paying reduces equity, receiving increases it

            # ---- Check exit ----
            if position.side != "flat":
                should_exit, exit_reason = strategy.check_exit(position, df, t)
                if is_last_bar:
                    # Force close any open position at end of backtest
                    should_exit = True
                    exit_reason = "time_based"
                if should_exit:
                    exit_price = float(current_bar["close"])

                    # Calculate exit fee
                    exit_fee = calculate_trade_fee(
                        position.size_usd, is_maker, self.config.exchange
                    )

                    # Calculate exit slippage
                    exit_slippage = 0.0
                    if self.config.use_slippage:
                        volume_1m = float(current_bar.get("volume", 0)) * exit_price
                        exit_slippage = calculate_slippage(
                            position.size_usd, volume_1m, self.config.symbol, self.config.exchange
                        )

                    # Price PnL (realized on exit)
                    if position.side == "long":
                        price_pnl = (exit_price - position.entry_price) / position.entry_price * position.size_usd
                    else:  # short
                        price_pnl = (position.entry_price - exit_price) / position.entry_price * position.size_usd

                    # Update equity with realized price PnL and exit costs
                    # (entry costs and funding already deducted during bar loop)
                    equity += price_pnl - exit_fee - exit_slippage

                    # Net PnL for trade record
                    net_pnl = (
                        price_pnl
                        + position.funding_pnl
                        - position.fees_paid
                        - exit_fee
                        - position.slippage_paid
                        - exit_slippage
                    )

                    trade = Trade(
                        entry_time_ms=position.entry_time_ms,
                        exit_time_ms=timestamp_ms,
                        symbol=self.config.symbol,
                        exchange=self.config.exchange,
                        side=position.side,
                        entry_price=position.entry_price,
                        exit_price=exit_price,
                        size_usd=position.size_usd,
                        price_pnl=price_pnl,
                        funding_pnl=position.funding_pnl,
                        fees=position.fees_paid + exit_fee,
                        slippage=position.slippage_paid + exit_slippage,
                        net_pnl=net_pnl,
                        hold_duration_min=int((timestamp_ms - position.entry_time_ms) / 60000),
                        exit_reason=exit_reason,
                    )
                    trades.append(trade)

                    # Reset position
                    position = Position()

            # ---- Check entry (only if flat) ----
            if position.side == "flat":
                signal = strategy.generate_signals(df, t)
                if signal in ("long", "short"):
                    entry_price = float(current_bar["close"])
                    size_usd = self.config.position_size_usd * self.config.leverage

                    # Entry fee
                    entry_fee = calculate_trade_fee(
                        size_usd, is_maker, self.config.exchange
                    )

                    # Entry slippage
                    entry_slippage = 0.0
                    if self.config.use_slippage:
                        volume_1m = float(current_bar.get("volume", 0)) * entry_price
                        entry_slippage = calculate_slippage(
                            size_usd, volume_1m, self.config.symbol, self.config.exchange
                        )

                    # Deduct entry costs from equity immediately
                    equity -= entry_fee + entry_slippage

                    position = Position(
                        side=signal,
                        entry_price=entry_price,
                        size_usd=size_usd,
                        entry_time_ms=timestamp_ms,
                        fees_paid=entry_fee,
                        slippage_paid=entry_slippage,
                    )

            # ---- Mark-to-market equity for curve ----
            mtm_equity = equity
            if position.side != "flat":
                current_price = float(current_bar["close"])
                if position.side == "long":
                    unrealized = (current_price - position.entry_price) / position.entry_price * position.size_usd
                else:
                    unrealized = (position.entry_price - current_price) / position.entry_price * position.size_usd
                # Add unrealized price PnL (entry costs and funding already in equity)
                mtm_equity += unrealized

            # Update peak and drawdown
            if mtm_equity > peak_equity:
                peak_equity = mtm_equity
            drawdown = mtm_equity - peak_equity
            drawdown_pct = drawdown / peak_equity if peak_equity != 0 else 0.0

            equity_curve.append(
                EquityPoint(
                    timestamp_ms=timestamp_ms,
                    equity=mtm_equity,
                    drawdown=drawdown,
                    drawdown_pct=drawdown_pct,
                )
            )

        return trades, equity_curve

    def _build_result(
        self,
        trades: List[Trade],
        equity_curve: List[EquityPoint],
        df: pd.DataFrame,
        strategy: BaseStrategy,
        elapsed_ms: int,
    ) -> BacktestResult:
        """Build BacktestResult from trades and equity curve."""
        total_bars = len(df)

        # Data coverage: % of expected 1m bars present
        if total_bars > 1:
            expected_ms = df.index[-1] - df.index[0]
            expected_bars = expected_ms / 60000 + 1
            data_coverage = min(100.0, (total_bars / expected_bars) * 100)
        else:
            data_coverage = 100.0

        # Equity series for calculations
        equity_series = pd.Series(
            [e.equity for e in equity_curve],
            index=[e.timestamp_ms for e in equity_curve],
        )

        if equity_series.empty or len(equity_series) < 2:
            return BacktestResult(
                strategy_type=self.config.strategy_type,
                symbol=self.config.symbol,
                exchange=self.config.exchange,
                start_ms=self.config.start_ms,
                end_ms=self.config.end_ms,
                total_bars=total_bars,
                data_coverage=data_coverage,
                elapsed_ms=elapsed_ms,
            )

        initial_equity = equity_series.iloc[0]
        final_equity = equity_series.iloc[-1]

        # Total return
        total_return_pct = ((final_equity - initial_equity) / initial_equity) * 100 if initial_equity else 0.0

        # CAGR
        duration_ms = self.config.end_ms - self.config.start_ms
        duration_years = duration_ms / (365.25 * 24 * 3600 * 1000)
        if duration_years > 0 and initial_equity > 0:
            cagr_pct = ((final_equity / initial_equity) ** (1 / duration_years) - 1) * 100
        else:
            cagr_pct = 0.0

        # Drawdown
        max_drawdown_pct, max_drawdown_duration_ms = calculate_drawdown(equity_series)
        max_drawdown_pct *= 100  # convert to percentage

        # Daily returns for Sharpe/Sortino
        equity_df = pd.DataFrame({"equity": equity_series})
        equity_df.index = pd.to_datetime(equity_df.index, unit="ms")
        daily_equity = equity_df.resample("D", label="right", closed="right").last()
        daily_returns = daily_equity["equity"].pct_change().dropna()

        sharpe = calculate_sharpe(daily_returns)
        sortino = calculate_sortino(daily_returns)

        # Calmar
        calmar = abs(cagr_pct / max_drawdown_pct) if max_drawdown_pct != 0 else 0.0

        # Trade stats
        total_trades = len(trades)
        if total_trades > 0:
            winning_trades = sum(1 for t in trades if t.net_pnl > 0)
            losing_trades = sum(1 for t in trades if t.net_pnl < 0)
            win_rate = (winning_trades / total_trades) * 100

            gross_profit = sum(t.net_pnl for t in trades if t.net_pnl > 0)
            gross_loss = abs(sum(t.net_pnl for t in trades if t.net_pnl < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

            pnls = [t.net_pnl for t in trades]
            avg_trade_pnl = sum(pnls) / len(pnls)
            median_trade_pnl = float(pd.Series(pnls).median())
            avg_win = sum(t.net_pnl for t in trades if t.net_pnl > 0) / winning_trades if winning_trades > 0 else 0.0
            avg_loss = sum(t.net_pnl for t in trades if t.net_pnl < 0) / losing_trades if losing_trades > 0 else 0.0
            best_trade = max(pnls)
            worst_trade = min(pnls)

            hold_times = [t.hold_duration_min for t in trades]
            avg_hold_time_min = sum(hold_times) / len(hold_times)
            median_hold_time_min = float(pd.Series(hold_times).median())
        else:
            winning_trades = 0
            losing_trades = 0
            win_rate = 0.0
            profit_factor = 0.0
            avg_trade_pnl = 0.0
            median_trade_pnl = 0.0
            avg_win = 0.0
            avg_loss = 0.0
            best_trade = 0.0
            worst_trade = 0.0
            avg_hold_time_min = 0.0
            median_hold_time_min = 0.0

        # Exposure time: % of bars where we have an open position
        if equity_curve and total_bars > 0:
            exposure_bars = sum(
                1
                for i in range(len(equity_curve))
                if any(
                    t.entry_time_ms <= equity_curve[i].timestamp_ms < t.exit_time_ms
                    for t in trades
                )
            )
            exposure_time_pct = (exposure_bars / total_bars) * 100
        else:
            exposure_time_pct = 0.0

        # PnL decomposition
        decomp = decompose_pnl(trades, self.initial_equity)

        return BacktestResult(
            strategy_type=self.config.strategy_type,
            symbol=self.config.symbol,
            exchange=self.config.exchange,
            start_ms=self.config.start_ms,
            end_ms=self.config.end_ms,
            total_bars=total_bars,
            data_coverage=data_coverage,
            total_return_pct=total_return_pct,
            cagr_pct=cagr_pct,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            max_drawdown_pct=max_drawdown_pct,
            max_drawdown_duration_ms=max_drawdown_duration_ms,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_trade_pnl=avg_trade_pnl,
            median_trade_pnl=median_trade_pnl,
            avg_win=avg_win,
            avg_loss=avg_loss,
            best_trade=best_trade,
            worst_trade=worst_trade,
            exposure_time_pct=exposure_time_pct,
            avg_hold_time_min=avg_hold_time_min,
            median_hold_time_min=median_hold_time_min,
            price_pnl_pct=decomp["price_pnl"],
            funding_pnl_pct=decomp["funding_pnl"],
            fees_drag_pct=-decomp["fees"],
            slippage_drag_pct=-decomp["slippage"],
            net_pnl_pct=decomp["price_pnl"] + decomp["funding_pnl"] - decomp["fees"] - decomp["slippage"],
            trades=trades,
            equity_curve=equity_curve,
        )
