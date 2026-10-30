"""
compiler/interpreter.py — SwayaLang Execution Engine & Backtest Runtime
========================================================================
Phase 2 deliverable for BCSE307P Compiler Design Laboratory.

Responsibility:
    Execute compiled SwayaLang strategies bar-by-bar against market price data.
    Provides:
      - Historical and synthetic OHLCV data loader.
      - Mathematical indicator calculation engine (SMA, EMA, RSI).
      - Runtime environment with dynamic variable binding (PRICE, ENTRY_PRICE).
      - Recursive AST condition/expression evaluation engine.
      - Portfolio state machine (cash, open positions, trade execution, PnL).
      - Performance metric computation (Win rate, Return %, Max Drawdown).

Compiler Concepts:
    - Runtime Environment and memory model for dynamic variables.
    - AST tree-walking interpreter (expression & boolean condition evaluation).
    - Signal dispatching and state machine transitions.
    - Concrete simulation providing quantitative proof of compiler correctness.

Usage:
    from compiler.interpreter import Interpreter, MarketData
    data = MarketData.from_csv("examples/data/AAPL_daily.csv")
    engine = Interpreter(data, initial_capital=100000.0)
    report = engine.run(ast_root)
    print(report.format_summary())
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from compiler.ast_nodes import (
    ActionNode,
    ASTNode,
    BinOpExprNode,
    BoolOpNode,
    ComparisonNode,
    FuncCallNode,
    IdentNode,
    IndicatorDeclNode,
    NumberLitNode,
    ProgramNode,
    RuleBlockNode,
    StrategyNode,
)


# ---------------------------------------------------------------------------
# Market Data Model
# ---------------------------------------------------------------------------

@dataclass
class MarketData:
    """Historical or synthetic time-series bars."""
    dates:   List[str]
    opens:   List[float]
    highs:   List[float]
    lows:    List[float]
    closes:  List[float]
    volumes: List[float]
    ticker:  str = "ASSET"

    def __len__(self) -> int:
        return len(self.closes)

    @classmethod
    def from_csv(cls, path: str | Path, ticker: str = "ASSET") -> MarketData:
        """Load OHLCV price series from a CSV file."""
        csv_path = Path(path)
        if not csv_path.is_file():
            raise FileNotFoundError(f"CSV market data not found: '{csv_path}'")

        dates, opens, highs, lows, closes, volumes = [], [], [], [], [], []
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Normalize field names to lowercase
            for row in reader:
                norm_row = {k.strip().lower(): v.strip() for k, v in row.items()}
                dates.append(norm_row.get("date", f"bar_{len(dates)}"))
                opens.append(float(norm_row.get("open", norm_row.get("close", 100.0))))
                highs.append(float(norm_row.get("high", norm_row.get("close", 100.0))))
                lows.append(float(norm_row.get("low", norm_row.get("close", 100.0))))
                closes.append(float(norm_row.get("close", 100.0)))
                volumes.append(float(norm_row.get("volume", 100000.0)))

        return cls(
            dates=dates,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            ticker=ticker,
        )

    @classmethod
    def generate_synthetic(
        cls, ticker: str = "AAPL", n_bars: int = 120, start_price: float = 150.0
    ) -> MarketData:
        """Generate realistic synthetic OHLCV daily bars with trending and cycles."""
        dates, opens, highs, lows, closes, volumes = [], [], [], [], [], []
        price = start_price

        for i in range(n_bars):
            # Compound trend + sinusoidal cycle + noise
            trend = 0.0005 * i
            cycle = 5.0 * math.sin(i / 10.0) + 3.0 * math.cos(i / 25.0)
            noise = (math.sin(i * 997) * 1.5)
            open_p = max(10.0, price)
            close_p = max(10.0, start_price + trend * 10 + cycle + noise)
            high_p = max(open_p, close_p) + abs(math.cos(i)) * 1.2
            low_p = min(open_p, close_p) - abs(math.sin(i)) * 1.2
            vol = 1000000 + int(abs(math.sin(i)) * 500000)

            dates.append(f"2026-{(i//28)%12 + 1:02d}-{(i%28)+1:02d}")
            opens.append(round(open_p, 2))
            highs.append(round(high_p, 2))
            lows.append(round(low_p, 2))
            closes.append(round(close_p, 2))
            volumes.append(float(vol))
            price = close_p

        return cls(
            dates=dates,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            ticker=ticker,
        )


# ---------------------------------------------------------------------------
# Technical Indicator Computation Engine
# ---------------------------------------------------------------------------

class IndicatorEngine:
    """Calculates vector technical indicators without external dependencies."""

    @staticmethod
    def compute_sma(series: List[float], period: int) -> List[Optional[float]]:
        """Simple Moving Average."""
        result: List[Optional[float]] = [None] * len(series)
        if period <= 0 or period > len(series):
            return result
        rolling_sum = sum(series[:period])
        result[period - 1] = rolling_sum / period
        for i in range(period, len(series)):
            rolling_sum += series[i] - series[i - period]
            result[i] = rolling_sum / period
        return result

    @staticmethod
    def compute_ema(series: List[float], period: int) -> List[Optional[float]]:
        """Exponential Moving Average."""
        result: List[Optional[float]] = [None] * len(series)
        if period <= 0 or period > len(series):
            return result
        k = 2.0 / (period + 1.0)
        # Seed with initial SMA
        prev_ema = sum(series[:period]) / period
        result[period - 1] = prev_ema
        for i in range(period, len(series)):
            prev_ema = (series[i] * k) + (prev_ema * (1.0 - k))
            result[i] = prev_ema
        return result

    @staticmethod
    def compute_rsi(series: List[float], period: int) -> List[Optional[float]]:
        """Relative Strength Index (0–100) using Wilder's Smoothing."""
        result: List[Optional[float]] = [None] * len(series)
        if period <= 0 or period >= len(series):
            return result

        gains: List[float] = []
        losses: List[float] = []
        for i in range(1, len(series)):
            diff = series[i] - series[i - 1]
            gains.append(max(0.0, diff))
            losses.append(max(0.0, -diff))

        if len(gains) < period:
            return result

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        if avg_loss == 0.0:
            result[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[period] = 100.0 - (100.0 / (1.0 + rs))

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0.0:
                result[i + 1] = 100.0
            else:
                rs = avg_gain / avg_loss
                result[i + 1] = 100.0 - (100.0 / (1.0 + rs))

        return result


# ---------------------------------------------------------------------------
# Portfolio & Trade State
# ---------------------------------------------------------------------------

@dataclass
class Trade:
    """An executed order record in the backtest trade log."""
    trade_id:     int
    bar:          int
    date:         str
    ticker:       str
    action:       str           # BUY, SELL, STOP_LOSS, TAKE_PROFIT
    shares:       float
    price:        float
    total_value:  float
    cash_after:   float
    realized_pnl: Optional[float] = None
    return_pct:   Optional[float] = None
    rule_kind:    str = ""


@dataclass
class Position:
    """Active open position state."""
    ticker:      str
    shares:      float
    entry_price: float
    entry_bar:   int
    entry_date:  str


# ---------------------------------------------------------------------------
# Backtest Performance Report
# ---------------------------------------------------------------------------

@dataclass
class BacktestReport:
    """Quantitative performance report generated from a strategy run."""
    strategy_name:    str
    ticker:           str
    total_bars:       int
    initial_capital:  float
    final_equity:     float
    net_profit:       float
    return_pct:       float
    total_trades:     int
    winning_trades:   int
    losing_trades:    int
    win_rate_pct:     float
    max_drawdown_pct: float
    trades:           List[Trade]
    equity_curve:     List[float]

    def format_summary(self) -> str:
        """Render a clean ASCII performance summary table."""
        w = 64
        sep = "+" + "-" * (w - 2) + "+"
        title = f" BACKTEST EXECUTION REPORT: {self.strategy_name} ({self.ticker}) "
        pad_l = (w - 2 - len(title)) // 2
        pad_r = w - 2 - len(title) - pad_l
        header = f"|{' ' * pad_l}{title}{' ' * pad_r}|"

        lines = [
            sep,
            header,
            sep,
            f"| Simulation Bars:     {str(self.total_bars).rjust(15)} | Trades Executed:   {str(self.total_trades).rjust(12)} |",
            f"| Initial Capital:     {f'${self.initial_capital:,.2f}'.rjust(15)} | Winning Trades:    {str(self.winning_trades).rjust(12)} |",
            f"| Final Equity:        {f'${self.final_equity:,.2f}'.rjust(15)} | Losing Trades:     {str(self.losing_trades).rjust(12)} |",
            f"| Net Profit / Loss:   {f'${self.net_profit:,.2f}'.rjust(15)} | Win Rate:          {f'{self.win_rate_pct:.1f}%'.rjust(12)} |",
            f"| Total Return:        {f'{self.return_pct:+.2f}%'.rjust(15)} | Max Drawdown:      {f'{self.max_drawdown_pct:.2f}%'.rjust(12)} |",
            sep,
        ]

        if self.trades:
            lines.append("\nTrade Execution Log:")
            lines.append("  ID | Date       | Action      | Shares | Price   | Realized PnL | Return %")
            lines.append("  ---+------------+-------------+--------+---------+--------------+---------")
            for t in self.trades:
                pnl_str = f"${t.realized_pnl:+.2f}" if t.realized_pnl is not None else "-"
                ret_str = f"{t.return_pct:+.2f}%" if t.return_pct is not None else "-"
                lines.append(
                    f"  {t.trade_id:02d} | {t.date} | {t.action.ljust(11)} | "
                    f"{t.shares:6.0f} | ${t.price:7.2f} | {pnl_str.rjust(12)} | {ret_str.rjust(8)}"
                )
        else:
            lines.append("\n(No trades triggered during simulation window)")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tree-Walking AST Interpreter & Execution Engine
# ---------------------------------------------------------------------------

class Interpreter:
    """
    Executes an AST ProgramNode against MarketData bar-by-bar,
    maintaining portfolio state and evaluating strategy rules.
    """

    def __init__(self, data: MarketData, initial_capital: float = 100000.0) -> None:
        self.data: MarketData = data
        self.initial_capital: float = initial_capital
        self.cash: float = initial_capital
        self.position: Optional[Position] = None
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []

        # Indicator pre-calculated cache: name -> List[Optional[float]]
        self.indicator_cache: Dict[str, List[Optional[float]]] = {}
        self._current_bar: int = 0
        self._trade_counter: int = 0

    # ------------------------------------------------------------------
    # Public Runner
    # ------------------------------------------------------------------

    def run(self, program: ProgramNode) -> List[BacktestReport]:
        """Execute all strategies in the program and return execution reports."""
        reports: List[BacktestReport] = []
        for strat in program.strategies:
            report = self.run_strategy(strat)
            reports.append(report)
        return reports

    def run_strategy(self, strategy: StrategyNode) -> BacktestReport:
        """Execute a single StrategyNode bar-by-bar."""
        # Reset runtime state
        self.cash = self.initial_capital
        self.position = None
        self.trades.clear()
        self.equity_curve.clear()
        self.indicator_cache.clear()
        self._trade_counter = 0

        # 1. Precompute Indicators
        self._precompute_indicators(strategy.indicators)

        # 2. Main Simulation Loop (Bar-by-Bar)
        max_equity = self.initial_capital
        max_drawdown = 0.0

        for bar_idx in range(len(self.data)):
            self._current_bar = bar_idx
            close_p = self.data.closes[bar_idx]

            # Skip warmup bars where any indicator is not yet computed
            if self._is_warmup_bar(bar_idx):
                current_equity = self.cash + (self.position.shares * close_p if self.position else 0.0)
                self.equity_curve.append(current_equity)
                continue

            # Evaluate Rules with priority:
            # 1. STOP_LOSS & TAKE_PROFIT (Risk management priority)
            # 2. EXIT (Normal exit)
            # 3. ENTRY (Open new position if flat)
            action_taken = False

            if self.position is not None:
                # Check STOP_LOSS
                for rule in strategy.rules:
                    if rule.kind == "STOP_LOSS" and self._eval_condition(rule.condition):
                        self._execute_action(rule.action, "STOP_LOSS", close_p)
                        action_taken = True
                        break

                # Check TAKE_PROFIT
                if not action_taken and self.position is not None:
                    for rule in strategy.rules:
                        if rule.kind == "TAKE_PROFIT" and self._eval_condition(rule.condition):
                            self._execute_action(rule.action, "TAKE_PROFIT", close_p)
                            action_taken = True
                            break

                # Check EXIT
                if not action_taken and self.position is not None:
                    for rule in strategy.rules:
                        if rule.kind == "EXIT" and self._eval_condition(rule.condition):
                            self._execute_action(rule.action, "EXIT", close_p)
                            action_taken = True
                            break

            # If position is flat, check ENTRY
            if not action_taken and self.position is None:
                for rule in strategy.rules:
                    if rule.kind == "ENTRY" and self._eval_condition(rule.condition):
                        self._execute_action(rule.action, "ENTRY", close_p)
                        break

            # Compute and record daily equity
            pos_val = self.position.shares * close_p if self.position else 0.0
            current_equity = self.cash + pos_val
            self.equity_curve.append(current_equity)

            # Drawdown calculation
            if current_equity > max_equity:
                max_equity = current_equity
            dd = (max_equity - current_equity) / max_equity * 100.0 if max_equity > 0 else 0.0
            if dd > max_drawdown:
                max_drawdown = dd

        # Calculate final metrics
        final_equity = self.equity_curve[-1] if self.equity_curve else self.initial_capital
        net_profit = final_equity - self.initial_capital
        return_pct = (net_profit / self.initial_capital) * 100.0

        closed_trades = [t for t in self.trades if t.realized_pnl is not None]
        winning = sum(1 for t in closed_trades if t.realized_pnl > 0)
        losing = sum(1 for t in closed_trades if t.realized_pnl <= 0)
        win_rate = (winning / len(closed_trades) * 100.0) if closed_trades else 0.0

        return BacktestReport(
            strategy_name=strategy.name,
            ticker=self.data.ticker,
            total_bars=len(self.data),
            initial_capital=self.initial_capital,
            final_equity=final_equity,
            net_profit=net_profit,
            return_pct=return_pct,
            total_trades=len(closed_trades),
            winning_trades=winning,
            losing_trades=losing,
            win_rate_pct=win_rate,
            max_drawdown_pct=max_drawdown,
            trades=self.trades,
            equity_curve=self.equity_curve,
        )

    # ------------------------------------------------------------------
    # Indicator Pre-computation
    # ------------------------------------------------------------------

    def _precompute_indicators(self, indicators: List[IndicatorDeclNode]) -> None:
        for ind in indicators:
            fname = ind.func_call.name.upper()
            series_arg = ind.func_call.args[0]
            period_arg = ind.func_call.args[1]

            series = self._resolve_series(series_arg)
            period = int(float(self._resolve_scalar(period_arg)))

            if fname == "SMA":
                vals = IndicatorEngine.compute_sma(series, period)
            elif fname == "EMA":
                vals = IndicatorEngine.compute_ema(series, period)
            elif fname == "RSI":
                vals = IndicatorEngine.compute_rsi(series, period)
            else:
                vals = [None] * len(self.data)

            self.indicator_cache[ind.name] = vals

    def _resolve_series(self, node: ASTNode) -> List[float]:
        if isinstance(node, IdentNode):
            name = node.name.upper()
            if name in ("CLOSE", "PRICE"):
                return self.data.closes
            elif name == "OPEN":
                return self.data.opens
            elif name == "HIGH":
                return self.data.highs
            elif name == "LOW":
                return self.data.lows
            elif name == "VOLUME":
                return self.data.volumes
            elif node.name in self.indicator_cache:
                # Fallback to zeros for None warmup
                return [v or 0.0 for v in self.indicator_cache[node.name]]
        return self.data.closes

    def _resolve_scalar(self, node: ASTNode) -> float:
        if isinstance(node, NumberLitNode):
            return node.value
        return 0.0

    def _is_warmup_bar(self, bar: int) -> bool:
        """Check if any indicator has None value at this bar."""
        for vals in self.indicator_cache.values():
            if bar >= len(vals) or vals[bar] is None:
                return True
        return False

    # ------------------------------------------------------------------
    # AST Condition & Expression Evaluation
    # ------------------------------------------------------------------

    def _eval_condition(self, node: ASTNode) -> bool:
        if isinstance(node, BoolOpNode):
            if node.op == "AND":
                return self._eval_condition(node.left) and self._eval_condition(node.right)
            elif node.op == "OR":
                return self._eval_condition(node.left) or self._eval_condition(node.right)
            return False

        elif isinstance(node, ComparisonNode):
            left_v = self._eval_expr(node.left)
            right_v = self._eval_expr(node.right)

            if node.op == ">":
                return left_v > right_v
            elif node.op == "<":
                return left_v < right_v
            elif node.op == ">=":
                return left_v >= right_v
            elif node.op == "<=":
                return left_v <= right_v
            elif node.op == "==":
                return math.isclose(left_v, right_v, rel_tol=1e-5)
            return False

        return False

    def _eval_expr(self, node: ASTNode) -> float:
        if isinstance(node, NumberLitNode):
            return node.value

        elif isinstance(node, IdentNode):
            name = node.name
            bar = self._current_bar

            # 1. Price fields
            if name.upper() in ("CLOSE", "PRICE"):
                return self.data.closes[bar]
            elif name.upper() == "OPEN":
                return self.data.opens[bar]
            elif name.upper() == "HIGH":
                return self.data.highs[bar]
            elif name.upper() == "LOW":
                return self.data.lows[bar]
            elif name.upper() == "VOLUME":
                return self.data.volumes[bar]

            # 2. Runtime Position variable
            elif name == "ENTRY_PRICE":
                return self.position.entry_price if self.position else 0.0

            # 3. Indicators
            elif name in self.indicator_cache:
                val = self.indicator_cache[name][bar]
                return val if val is not None else 0.0

            return 0.0

        elif isinstance(node, BinOpExprNode):
            l = self._eval_expr(node.left)
            r = self._eval_expr(node.right)
            if node.op == "+":
                return l + r
            elif node.op == "-":
                return l - r
            elif node.op == "*":
                return l * r
            elif node.op == "/":
                return l / r if r != 0.0 else 0.0
            return 0.0

        return 0.0

    # ------------------------------------------------------------------
    # Trade Execution State Machine
    # ------------------------------------------------------------------

    def _execute_action(self, action: ActionNode, rule_kind: str, price: float) -> None:
        bar = self._current_bar
        date_str = self.data.dates[bar]
        ticker = action.ticker or (self.position.ticker if self.position else self.data.ticker)

        if action.action == "BUY" and self.position is None:
            # Determine shares
            if action.all_flag:
                shares = math.floor(self.cash / price)
            else:
                shares = action.quantity or 0.0

            cost = shares * price
            if shares > 0 and self.cash >= cost:
                self.cash -= cost
                self.position = Position(
                    ticker=ticker,
                    shares=shares,
                    entry_price=price,
                    entry_bar=bar,
                    entry_date=date_str,
                )
                self._trade_counter += 1
                self.trades.append(
                    Trade(
                        trade_id=self._trade_counter,
                        bar=bar,
                        date=date_str,
                        ticker=ticker,
                        action=f"BUY_{rule_kind}",
                        shares=shares,
                        price=price,
                        total_value=cost,
                        cash_after=self.cash,
                        realized_pnl=None,
                        return_pct=None,
                        rule_kind=rule_kind,
                    )
                )

        elif (action.action == "SELL" or rule_kind in ("EXIT", "STOP_LOSS", "TAKE_PROFIT")) and self.position is not None:
            # Sell open position
            shares = self.position.shares if action.all_flag else min(action.quantity or self.position.shares, self.position.shares)
            proceeds = shares * price
            entry_cost = shares * self.position.entry_price
            pnl = proceeds - entry_cost
            ret_pct = (pnl / entry_cost * 100.0) if entry_cost > 0 else 0.0

            self.cash += proceeds
            self._trade_counter += 1
            self.trades.append(
                Trade(
                    trade_id=self._trade_counter,
                    bar=bar,
                    date=date_str,
                    ticker=ticker,
                    action=f"SELL_{rule_kind}",
                    shares=shares,
                    price=price,
                    total_value=proceeds,
                    cash_after=self.cash,
                    realized_pnl=pnl,
                    return_pct=ret_pct,
                    rule_kind=rule_kind,
                )
            )

            # Close or reduce position
            if shares >= self.position.shares:
                self.position = None
            else:
                self.position.shares -= shares
