"""
tests/test_interpreter.py — Unit Tests for SwayaLang Interpreter & Execution Engine
===================================================================================
Phase 2 test suite for BCSE307P Compiler Design Laboratory.
"""

from pathlib import Path

from compiler.interpreter import IndicatorEngine, Interpreter, MarketData
from compiler.lexer import Lexer
from compiler.parser import Parser


def parse_source(source: str):
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def test_indicator_engine_sma():
    """Verify SMA calculation against known manual values."""
    prices = [10.0, 20.0, 30.0, 40.0, 50.0]
    # SMA with period 3:
    # index 0: None, 1: None
    # index 2: (10+20+30)/3 = 20.0
    # index 3: (20+30+40)/3 = 30.0
    # index 4: (30+40+50)/3 = 40.0
    sma = IndicatorEngine.compute_sma(prices, period=3)
    assert sma[0] is None
    assert sma[1] is None
    assert sma[2] == 20.0
    assert sma[3] == 30.0
    assert sma[4] == 40.0


def test_indicator_engine_ema():
    """Verify EMA calculation begins at SMA seed and applies smoothing factor."""
    prices = [10.0, 10.0, 10.0, 20.0]
    # Period 3:
    # SMA seed at index 2 = 10.0
    # k = 2 / (3 + 1) = 0.5
    # index 3: 20.0 * 0.5 + 10.0 * 0.5 = 15.0
    ema = IndicatorEngine.compute_ema(prices, period=3)
    assert ema[0] is None
    assert ema[1] is None
    assert ema[2] == 10.0
    assert ema[3] == 15.0


def test_indicator_engine_rsi_bounds():
    """Verify RSI calculation outputs are bounded between 0 and 100."""
    prices = [10.0, 12.0, 11.0, 14.0, 15.0, 13.0, 16.0, 18.0, 17.0, 19.0, 20.0]
    rsi = IndicatorEngine.compute_rsi(prices, period=5)
    for val in rsi:
        if val is not None:
            assert 0.0 <= val <= 100.0


def test_market_data_synthetic():
    """Verify synthetic market data generation creates complete OHLCV series."""
    data = MarketData.generate_synthetic(ticker="TEST", n_bars=50)
    assert len(data) == 50
    assert len(data.opens) == 50
    assert len(data.highs) == 50
    assert len(data.lows) == 50
    assert len(data.closes) == 50
    assert len(data.volumes) == 50
    for h, l, c in zip(data.highs, data.lows, data.closes):
        assert h >= l
        assert h >= c
        assert l <= c


def test_market_data_csv_loader():
    """Verify loading historical CSV data from disk."""
    csv_file = Path("examples/data/AAPL_daily.csv")
    assert csv_file.is_file()
    data = MarketData.from_csv(csv_file, ticker="AAPL")
    assert len(data) > 0
    assert data.ticker == "AAPL"


def test_interpreter_execution_trades_and_metrics():
    """Verify interpreter executes strategy rules, updates portfolio, and computes metrics."""
    src = """
    STRATEGY "TestExec" {
        INDICATOR sma_5 = SMA(CLOSE, 5)
        ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > sma_5
        EXIT:  SELL ALL                  IF CLOSE < sma_5
    }
    """
    ast = parse_source(src)
    data = MarketData.generate_synthetic(ticker="AAPL", n_bars=60)
    interpreter = Interpreter(data, initial_capital=100000.0)
    reports = interpreter.run(ast)

    assert len(reports) == 1
    rep = reports[0]
    assert rep.strategy_name == "TestExec"
    assert rep.total_bars == 60
    assert rep.initial_capital == 100000.0
    assert len(rep.equity_curve) == 60
    assert rep.max_drawdown_pct >= 0.0

    summary = rep.format_summary()
    assert "BACKTEST EXECUTION REPORT" in summary
    assert "Simulation Bars:" in summary


def test_stop_loss_trigger():
    """Verify STOP_LOSS rule triggers when price drops below threshold."""
    src = """
    STRATEGY "StopLossTest" {
        ENTRY:     BUY 100 SHARES OF "AAPL" IF CLOSE > 90
        STOP_LOSS: SELL ALL                  IF PRICE < ENTRY_PRICE * 0.95
    }
    """
    ast = parse_source(src)
    # Construct prices that drop 15% on bar 1, bar 2 stays low
    dates = ["2026-01-01", "2026-01-02", "2026-01-03"]
    opens = [100.0, 85.0, 80.0]
    highs = [105.0, 90.0, 85.0]
    lows = [95.0, 80.0, 75.0]
    closes = [100.0, 85.0, 80.0]
    volumes = [1000.0, 1000.0, 1000.0]
    data = MarketData(dates=dates, opens=opens, highs=highs, lows=lows, closes=closes, volumes=volumes)

    interpreter = Interpreter(data, initial_capital=100000.0)
    reports = interpreter.run(ast)
    rep = reports[0]

    # Should have entered at bar 0 and stopped out at bar 1
    assert len(rep.trades) == 2
    assert rep.trades[0].action == "BUY_ENTRY"
    assert rep.trades[0].ticker == "AAPL"
    assert rep.trades[1].action == "SELL_STOP_LOSS"
    assert rep.trades[1].ticker == "AAPL"
    assert rep.trades[1].realized_pnl == -1500.0  # (85 - 100) * 100
