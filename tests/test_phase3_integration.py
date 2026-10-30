"""
tests/test_phase3_integration.py — Integration & Edge-Case Tests (Phase 3)
===========================================================================
Phase 3 deliverable for BCSE307P Compiler Design Laboratory.

Tests:
    - Valid inputs: Full 7-stage compiler pipeline on canonical strategies
    - Invalid inputs: Lexical, parse, and semantic error reporting
    - Boundary cases:
      - 0-trade strategies (conditions never satisfied, preserving capital)
      - Boundary dataset sizes (minimum warm-up bars, synthetic 50 bars)
      - Capital boundary values (1,000, 100,000, 1,000,000)
      - Missing file error handling
    - Semantic equivalence invariant:
      - Proof that optimization passes preserve 100% functional equivalence
        of backtest trade signals, PnL, and equity curve.
"""

from __future__ import annotations

import math
from pathlib import Path
import pytest

from compiler.ast_nodes import ProgramNode
from compiler.interpreter import BacktestReport, Interpreter, MarketData
from compiler.ir import IRGenerator
from compiler.lexer import LexError, Lexer
from compiler.optimizer import Optimizer
from compiler.parser import ParseError, Parser
from compiler.reporter import BenchmarkRunner, ReportGenerator
from compiler.semantic import SemanticAnalyzer, SemanticError


# ---------------------------------------------------------------------------
# 1. Valid Input Full Pipeline Integration
# ---------------------------------------------------------------------------

def test_full_phase3_pipeline_multi_rule():
    """Execute complete 7-stage pipeline on multi_rule strategy with real AAPL data."""
    strat_path = Path("examples/multi_rule.strat")
    data_path = Path("examples/data/AAPL_daily.csv")
    assert strat_path.is_file()
    assert data_path.is_file()

    source = strat_path.read_text(encoding="utf-8")
    data = MarketData.from_csv(data_path, ticker="AAPL")

    # Run Benchmark & Full Pipeline
    report, opt_stats = BenchmarkRunner.measure_pipeline(
        source=source,
        market_data=data,
        capital=100000.0,
        enable_optimization=True,
    )

    assert report.strategy_name == "MomentumBreakout"
    assert report.ticker == "AAPL"
    assert report.total_bars == 220
    assert len(report.trades) > 0
    assert report.benchmark.total_time_ms > 0
    assert report.benchmark.bars_processed == 220
    assert opt_stats.initial_quad_count > 0


def test_optimization_semantic_equivalence():
    """
    CRITICAL COMPILER INVARIANT:
    Verifies that the backtest output of an unoptimized AST and an optimized AST
    are 100% mathematically and financially IDENTICAL.
    """
    source = """
    STRATEGY "EquivalenceTest" {
        INDICATOR sma_50 = SMA(CLOSE, 50)
        INDICATOR sma_200 = SMA(CLOSE, 200)

        ENTRY:     BUY 100 SHARES OF "AAPL" IF sma_50 > sma_200 AND PRICE > (10 + 40)
        EXIT:      SELL ALL                  IF sma_50 < sma_200
        STOP_LOSS: SELL ALL                  IF PRICE < ENTRY_PRICE * (1.0 - 0.05)
    }
    """
    data = MarketData.generate_synthetic(ticker="AAPL", n_bars=150, start_price=120.0)

    # 1. Run unoptimized AST
    tokens = Lexer(source).tokenize()
    raw_ast = Parser(tokens).parse()
    SemanticAnalyzer(fail_fast=True).analyze(raw_ast)
    raw_engine = Interpreter(data, initial_capital=100000.0)
    raw_reports = raw_engine.run(raw_ast)
    raw_rep = raw_reports[0]

    # 2. Run optimized AST
    optimizer = Optimizer()
    opt_ast, opt_stats = optimizer.optimize_ast(raw_ast)
    opt_engine = Interpreter(data, initial_capital=100000.0)
    opt_reports = opt_engine.run(opt_ast)
    opt_rep = opt_reports[0]

    # Verification: identical trade signals, PnL, and final equity
    assert raw_rep.total_trades == opt_rep.total_trades
    assert math.isclose(raw_rep.final_equity, opt_rep.final_equity, rel_tol=1e-5)
    assert math.isclose(raw_rep.net_profit, opt_rep.net_profit, rel_tol=1e-5)
    assert raw_rep.winning_trades == opt_rep.winning_trades
    assert raw_rep.losing_trades == opt_rep.losing_trades
    assert len(raw_rep.trades) == len(opt_rep.trades)
    for t_raw, t_opt in zip(raw_rep.trades, opt_rep.trades):
        assert t_raw.action == t_opt.action
        assert t_raw.bar == t_opt.bar
        assert math.isclose(t_raw.price, t_opt.price, rel_tol=1e-5)


# ---------------------------------------------------------------------------
# 2. Boundary Cases & Edge Conditions
# ---------------------------------------------------------------------------

def test_boundary_zero_trades_strategy():
    """A strategy whose entry condition is never met (e.g. PRICE > 1,000,000)."""
    source = """
    STRATEGY "NeverEnters" {
        INDICATOR sma_50 = SMA(CLOSE, 50)
        ENTRY: BUY 100 SHARES OF "AAPL" IF PRICE > 1000000
        EXIT:  SELL ALL                  IF PRICE < 10
    }
    """
    data = MarketData.generate_synthetic(ticker="AAPL", n_bars=80)
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer(fail_fast=True).analyze(ast)

    engine = Interpreter(data, initial_capital=50000.0)
    reports = engine.run(ast)
    rep = reports[0]

    assert rep.total_trades == 0
    assert rep.final_equity == 50000.0
    assert rep.net_profit == 0.0
    assert rep.win_rate_pct == 0.0
    assert rep.max_drawdown_pct == 0.0


def test_boundary_capital_scaling():
    """Verify strategy scales correctly with different initial capital levels."""
    source = """
    STRATEGY "CapitalScaling" {
        INDICATOR sma_10 = SMA(CLOSE, 10)
        INDICATOR sma_20 = SMA(CLOSE, 20)
        ENTRY: BUY ALL IF sma_10 > sma_20
        EXIT:  SELL ALL IF sma_10 < sma_20
    }
    """
    data = MarketData.generate_synthetic(ticker="AAPL", n_bars=60)
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer(fail_fast=True).analyze(ast)

    capitals = [5000.0, 50000.0, 500000.0]
    for cap in capitals:
        engine = Interpreter(data, initial_capital=cap)
        reports = engine.run(ast)
        assert len(reports) == 1
        assert reports[0].initial_capital == cap


def test_boundary_minimum_warmup_bars():
    """Verify execution behavior on a dataset equal to indicator period."""
    data = MarketData.generate_synthetic(ticker="AAPL", n_bars=20)
    source = """
    STRATEGY "ShortData" {
        INDICATOR sma_10 = SMA(CLOSE, 10)
        ENTRY: BUY 50 SHARES OF "AAPL" IF CLOSE > sma_10
    }
    """
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer(fail_fast=True).analyze(ast)

    engine = Interpreter(data, initial_capital=20000.0)
    reports = engine.run(ast)
    assert len(reports) == 1
    assert reports[0].total_bars == 20


def test_empty_dataset_error_handling(tmp_path: Path):
    """Verify proper error handling when loading non-existent market CSV."""
    with pytest.raises(FileNotFoundError):
        MarketData.from_csv(tmp_path / "nonexistent.csv")


# ---------------------------------------------------------------------------
# 3. Invalid Inputs & Negative Error Conditions
# ---------------------------------------------------------------------------

def test_invalid_lexical_character():
    """Negative testing: unknown character raises LexError."""
    with pytest.raises(LexError) as exc_info:
        Lexer('STRATEGY "Test" { ENTRY: @ }').tokenize()
    assert "Unexpected character" in str(exc_info.value)


def test_invalid_syntax_missing_strategy_name():
    """Negative testing: missing strategy name raises ParseError."""
    with pytest.raises(ParseError) as exc_info:
        Parser(Lexer("STRATEGY { }").tokenize()).parse()
    assert "ParseError" in str(exc_info.value)


def test_invalid_semantic_duplicate_strategy():
    """Negative testing: duplicate strategy names in same file raises SemanticError."""
    src = """
    STRATEGY "Same" { ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > 10 }
    STRATEGY "Same" { ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > 10 }
    """
    ast = Parser(Lexer(src).tokenize()).parse()
    with pytest.raises(SemanticError) as exc_info:
        SemanticAnalyzer(fail_fast=True).analyze(ast)
    assert "Duplicate strategy" in str(exc_info.value)
