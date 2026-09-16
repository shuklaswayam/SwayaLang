"""
tests/test_driver.py — End-to-End Subprocess Tests for driver.py CLI
====================================================================
Tests:
- Running driver.py on examples/golden_cross.strat as subprocess
- Verifying token stream contains STRATEGY and INDICATOR tokens
- Verifying AST section contains Strategy and IndicatorDecl nodes
- Handling missing file (exit code 1, stderr message)
- Handling missing arguments (exit code 1, usage message)
- Handling syntax/lexical errors (exit code 1, error on stderr)
"""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def run_driver(*args: str) -> subprocess.CompletedProcess[str]:
    """Helper to run driver.py with given arguments."""
    cmd = [sys.executable, str(PROJECT_ROOT / "driver.py"), *args]
    return subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )


def test_driver_golden_cross_e2e():
    """
    Acceptance criterion: python driver.py examples/golden_cross.strat prints
    token stream then AST without error; pytest e2e test runs driver as
    subprocess and asserts output contains STRATEGY and INDICATOR tokens.
    """
    res = run_driver("examples/golden_cross.strat")

    assert res.returncode == 0
    stdout = res.stdout

    # Asserts token stream section and key tokens
    assert "── Token Stream ──" in stdout
    assert "Token(STRATEGY, 'STRATEGY'" in stdout
    assert "Token(INDICATOR, 'INDICATOR'" in stdout
    assert "Token(ENTRY, 'ENTRY'" in stdout
    assert "Token(BUY, 'BUY'" in stdout

    # Asserts AST section
    assert "── Abstract Syntax Tree ──" in stdout
    assert "Strategy(name='GoldenCross')" in stdout
    assert "IndicatorDecl(name='sma_50')" in stdout
    assert "RuleBlock(kind='ENTRY')" in stdout


def test_driver_rsi_oversold_e2e():
    """Verify driver on second example strategy."""
    res = run_driver("examples/rsi_oversold.strat")
    assert res.returncode == 0
    assert "Strategy(name='RSIOverSold')" in res.stdout
    assert "TAKE_PROFIT" in res.stdout


def test_driver_missing_file_exits_1():
    """
    Acceptance criterion: missing file exits 1 with clear message.
    """
    res = run_driver("examples/nonexistent_file.strat")
    assert res.returncode == 1
    assert "Error: File not found" in res.stderr


def test_driver_no_args_exits_1():
    """Running driver without arguments prints usage and exits 1."""
    res = run_driver()
    assert res.returncode == 1
    assert "Usage: python driver.py" in res.stderr


def test_driver_syntax_error_exits_1(tmp_path):
    """Running driver on a file with syntax error exits 1 with ParseError."""
    bad_strat = tmp_path / "bad.strat"
    bad_strat.write_text('STRATEGY "Bad" { ENTRY: BUY ALL sma_50 > 10 }')

    res = run_driver(str(bad_strat))
    assert res.returncode == 1
    assert "ParseError" in res.stderr


def test_driver_lex_error_exits_1(tmp_path):
    """Running driver on a file with invalid characters exits 1 with LexError."""
    bad_strat = tmp_path / "bad_lex.strat"
    bad_strat.write_text('STRATEGY "Bad" @')

    res = run_driver(str(bad_strat))
    assert res.returncode == 1
    assert "LexError" in res.stderr
