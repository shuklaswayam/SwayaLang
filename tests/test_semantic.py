"""
tests/test_semantic.py — Unit Tests for SwayaLang Semantic Analyzer
====================================================================
Phase 2 test suite for BCSE307P Compiler Design Laboratory.
"""

import pytest

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic import SemanticAnalyzer, SemanticError


def parse_source(source: str):
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def test_valid_golden_cross_strategy():
    """Verify semantic analysis succeeds on canonical golden_cross strategy."""
    src = """
    STRATEGY "GoldenCross" {
        INDICATOR sma_50  = SMA(CLOSE, 50)
        INDICATOR sma_200 = SMA(CLOSE, 200)
        INDICATOR rsi_14  = RSI(CLOSE, 14)

        ENTRY:     BUY 100 SHARES OF "AAPL" IF sma_50 > sma_200 AND rsi_14 < 30
        EXIT:      SELL ALL                  IF sma_50 < sma_200
        STOP_LOSS: SELL ALL                  IF PRICE < ENTRY_PRICE * 0.95
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=True)
    symtab, errors, warnings = analyzer.analyze(ast)

    assert len(errors) == 0
    assert len(warnings) == 0
    assert symtab.lookup_in_scope("GoldenCross", "sma_50") is not None
    assert symtab.lookup_in_scope("GoldenCross", "sma_200") is not None
    assert symtab.lookup_in_scope("GoldenCross", "rsi_14") is not None


def test_duplicate_strategy_name_error():
    """Verify duplicate strategy names in the same program raise SemanticError."""
    src = """
    STRATEGY "Duplicate" {
        INDICATOR sma_10 = SMA(CLOSE, 10)
        ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > sma_10
    }
    STRATEGY "Duplicate" {
        INDICATOR sma_20 = SMA(CLOSE, 20)
        ENTRY: BUY 50 SHARES OF "AAPL" IF CLOSE > sma_20
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=True)
    with pytest.raises(SemanticError) as exc_info:
        analyzer.analyze(ast)
    assert "Duplicate strategy name 'Duplicate'" in str(exc_info.value)


def test_duplicate_indicator_declaration_error():
    """Verify duplicate indicator declarations in the same strategy raise SemanticError."""
    src = """
    STRATEGY "DupInd" {
        INDICATOR sma_50 = SMA(CLOSE, 50)
        INDICATOR sma_50 = SMA(CLOSE, 20)
        ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > sma_50
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=True)
    with pytest.raises(SemanticError) as exc_info:
        analyzer.analyze(ast)
    assert "Duplicate indicator declaration 'sma_50'" in str(exc_info.value)


def test_shadowing_builtin_name_error():
    """Verify declaring an indicator with a built-in price field name raises SemanticError."""
    src = """
    STRATEGY "Shadow" {
        INDICATOR CLOSE = SMA(OPEN, 10)
        ENTRY: BUY 100 SHARES OF "AAPL" IF OPEN > 100
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=True)
    with pytest.raises(SemanticError) as exc_info:
        analyzer.analyze(ast)
    assert "shadows built-in PRICE_FIELD 'CLOSE'" in str(exc_info.value)


def test_unknown_indicator_function_error():
    """Verify calling an undefined indicator function raises SemanticError."""
    src = """
    STRATEGY "UnknownFunc" {
        INDICATOR custom_ind = BOLLINGER(CLOSE, 20)
        ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > custom_ind
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=True)
    with pytest.raises(SemanticError) as exc_info:
        analyzer.analyze(ast)
    assert "Unknown indicator function 'BOLLINGER'" in str(exc_info.value)


def test_indicator_arity_mismatch_error():
    """Verify calling SMA with wrong number of arguments raises SemanticError."""
    src = """
    STRATEGY "ArityFail" {
        INDICATOR bad_sma = SMA(CLOSE, 50, 10)
        ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > bad_sma
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=True)
    with pytest.raises(SemanticError) as exc_info:
        analyzer.analyze(ast)
    assert "expects 2 arguments" in str(exc_info.value)


def test_indicator_invalid_period_error():
    """Verify non-positive indicator period raises SemanticError."""
    src = """
    STRATEGY "ZeroPeriod" {
        INDICATOR bad_sma = SMA(CLOSE, 0)
        ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > bad_sma
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=True)
    with pytest.raises(SemanticError) as exc_info:
        analyzer.analyze(ast)
    assert "Period argument to 'SMA' must be a positive integer > 0" in str(exc_info.value)


def test_missing_entry_rule_error():
    """Verify strategy without an ENTRY rule raises SemanticError."""
    src = """
    STRATEGY "NoEntry" {
        INDICATOR sma_20 = SMA(CLOSE, 20)
        EXIT: SELL ALL IF CLOSE < sma_20
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=True)
    with pytest.raises(SemanticError) as exc_info:
        analyzer.analyze(ast)
    assert "must declare at least one 'ENTRY' rule" in str(exc_info.value)


def test_undeclared_identifier_in_rule_error():
    """Verify referencing an undeclared identifier raises SemanticError."""
    src = """
    STRATEGY "UndeclaredTest" {
        INDICATOR sma_50 = SMA(CLOSE, 50)
        ENTRY: BUY 100 SHARES OF "AAPL" IF sma_50 > nonexistent_indicator
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=True)
    with pytest.raises(SemanticError) as exc_info:
        analyzer.analyze(ast)
    assert "Undeclared identifier 'nonexistent_indicator'" in str(exc_info.value)


def test_entry_price_in_entry_rule_error():
    """Verify referencing ENTRY_PRICE in an ENTRY rule raises SemanticError."""
    src = """
    STRATEGY "BadEntryPrice" {
        ENTRY: BUY 100 SHARES OF "AAPL" IF PRICE < ENTRY_PRICE * 0.95
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=True)
    with pytest.raises(SemanticError) as exc_info:
        analyzer.analyze(ast)
    assert "ENTRY_PRICE cannot be referenced in an 'ENTRY' rule" in str(exc_info.value)


def test_static_division_by_zero_error():
    """Verify dividing by literal zero raises SemanticError."""
    src = """
    STRATEGY "DivZero" {
        ENTRY: BUY 100 SHARES OF "AAPL" IF PRICE > (CLOSE / 0)
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=True)
    with pytest.raises(SemanticError) as exc_info:
        analyzer.analyze(ast)
    assert "Division by zero in arithmetic expression" in str(exc_info.value)


def test_unused_indicator_emits_warning():
    """Verify declaring an indicator but never using it generates a SemanticWarning."""
    src = """
    STRATEGY "UnusedInd" {
        INDICATOR active_sma = SMA(CLOSE, 20)
        INDICATOR unused_rsi = RSI(CLOSE, 14)
        ENTRY: BUY 100 SHARES OF "AAPL" IF CLOSE > active_sma
    }
    """
    ast = parse_source(src)
    analyzer = SemanticAnalyzer(fail_fast=False)
    _, errors, warnings = analyzer.analyze(ast)

    assert len(errors) == 0
    assert len(warnings) == 1
    assert "Indicator 'unused_rsi' is declared but never used" in warnings[0].message
