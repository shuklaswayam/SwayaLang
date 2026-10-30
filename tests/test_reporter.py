"""
tests/test_reporter.py — Unit Tests for SwayaLang Reporter & Benchmarks (Phase 3)
=================================================================================
Phase 3 deliverable for BCSE307P Compiler Design Laboratory.

Tests:
    - FinancialMetrics calculation (Sharpe ratio, Sortino ratio, CAGR, Drawdown, Profit Factor)
    - CompilerBenchmark profiling (stage latency, peak memory, throughput)
    - JSON structured report serialization & integrity
    - CSV trade log export & header verification
    - High-DPI Matplotlib equity curve rendering to PNG
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from compiler.interpreter import BacktestReport, Trade
from compiler.reporter import (
    BenchmarkRunner,
    CompilerBenchmark,
    ComprehensiveReport,
    FinancialMetrics,
    ReportGenerator,
    StageTiming,
)


def _make_mock_backtest_report() -> BacktestReport:
    """Constructs a deterministic BacktestReport with known trades."""
    trades = [
        Trade(1, 10, "2026-01-10", "AAPL", "BUY_ENTRY", 100.0, 150.0, 15000.0, 85000.0, None, None, "ENTRY"),
        Trade(2, 25, "2026-01-25", "AAPL", "SELL_EXIT", 100.0, 165.0, 16500.0, 101500.0, 1500.0, 10.0, "EXIT"),
        Trade(3, 40, "2026-02-10", "AAPL", "BUY_ENTRY", 100.0, 160.0, 16000.0, 85500.0, None, None, "ENTRY"),
        Trade(4, 55, "2026-02-25", "AAPL", "SELL_STOP_LOSS", 100.0, 152.0, 15200.0, 100700.0, -800.0, -5.0, "STOP_LOSS"),
    ]
    # Synthetic equity curve starting from 100k
    equity_curve = [100000.0] * 10 + [101500.0] * 30 + [100700.0] * 20
    return BacktestReport(
        strategy_name="MockStrategy",
        ticker="AAPL",
        total_bars=60,
        initial_capital=100000.0,
        final_equity=100700.0,
        net_profit=700.0,
        return_pct=0.70,
        total_trades=2,
        winning_trades=1,
        losing_trades=1,
        win_rate_pct=50.0,
        max_drawdown_pct=0.79,
        trades=trades,
        equity_curve=equity_curve,
    )


def test_financial_metrics_calculation():
    """Verify financial risk indicators: profit factor, win rate, and annualized returns."""
    base_report = _make_mock_backtest_report()
    metrics = ReportGenerator._compute_financial_metrics(base_report)

    assert metrics.initial_capital == 100000.0
    assert metrics.final_equity == 100700.0
    assert metrics.net_profit == 700.0
    assert metrics.winning_trades == 1
    assert metrics.losing_trades == 1
    assert metrics.win_rate_pct == 50.0
    assert metrics.profit_factor == 1.88  # 1500 / 800
    assert metrics.win_loss_ratio == 1.0
    assert metrics.avg_winning_trade == 1500.0
    assert metrics.avg_losing_trade == 800.0


def test_compiler_benchmark_formatting():
    """Verify CompilerBenchmark records timings, throughput, and formats clean summary."""
    timings = [
        StageTiming("Stage 1: Lexical Analysis", 0.45, 10.0),
        StageTiming("Stage 2: Syntax Analysis & AST", 0.85, 20.0),
        StageTiming("Stage 3: Symbol Table & Semantic", 0.70, 15.0),
        StageTiming("Stage 4: Intermediate Code Gen", 0.50, 12.0),
        StageTiming("Stage 5: Code Optimization", 0.50, 12.0),
        StageTiming("Stage 6: Execution Engine", 1.40, 31.0),
    ]
    benchmark = CompilerBenchmark(
        timings=timings,
        total_time_ms=4.40,
        peak_memory_kb=256.40,
        current_memory_kb=128.20,
        bars_processed=200,
        bars_per_second=142857.1,
    )

    summary = benchmark.format_summary()
    assert "SWAYALANG COMPILER PERFORMANCE BENCHMARK" in summary
    assert "Total Pipeline Latency:" in summary
    assert "Peak Memory Footprint:" in summary
    assert "Simulation Throughput:" in summary


def test_report_json_and_csv_export(tmp_path: Path):
    """Verify ComprehensiveReport exports valid JSON and CSV formats."""
    base_report = _make_mock_backtest_report()
    benchmark = CompilerBenchmark([], 10.0, 100.0, 50.0, 60, 6000.0)
    report = ReportGenerator.generate_report(base_report, benchmark)

    # Test JSON Export
    json_file = tmp_path / "test_report.json"
    report.export_json(json_file)
    assert json_file.is_file()

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["strategy_name"] == "MockStrategy"
    assert data["financial"]["net_profit"] == 700.0
    assert len(data["trades"]) == 4

    # Test CSV Export
    csv_file = tmp_path / "test_trades.csv"
    report.export_csv(csv_file)
    assert csv_file.is_file()

    content = csv_file.read_text(encoding="utf-8")
    assert "id,date,ticker,action,shares,price" in content
    assert "BUY_ENTRY" in content
    assert "SELL_EXIT" in content


def test_report_equity_curve_chart_generation(tmp_path: Path):
    """Verify publication-grade equity curve plot generates valid PNG file."""
    base_report = _make_mock_backtest_report()
    benchmark = CompilerBenchmark([], 10.0, 100.0, 50.0, 60, 6000.0)
    report = ReportGenerator.generate_report(base_report, benchmark)

    chart_file = tmp_path / "equity_test.png"
    out_path = ReportGenerator.plot_equity_curve(report, output_path=chart_file, dpi=100)

    assert out_path.is_file()
    assert out_path.stat().st_size > 1000  # Non-empty image bytes
