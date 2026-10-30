"""
tests/test_symbol_table.py — Unit Tests for SwayaLang Scoped Symbol Table
=========================================================================
Phase 2 test suite for BCSE307P Compiler Design Laboratory.
"""

import pytest

from compiler.symbol_table import DataType, Scope, Symbol, SymbolKind, SymbolTable


def test_global_scope_builtins():
    """Verify global scope is populated with price fields and indicator functions."""
    symtab = SymbolTable()

    # Price fields
    for field_name in ["CLOSE", "OPEN", "HIGH", "LOW", "VOLUME", "PRICE", "ENTRY_PRICE"]:
        sym = symtab.lookup(field_name)
        assert sym is not None, f"Expected {field_name} in global scope"
        assert sym.kind == SymbolKind.PRICE_FIELD
        assert sym.data_type == DataType.SERIES

    # Built-in technical indicators
    for func_name in ["SMA", "EMA", "RSI"]:
        sym = symtab.lookup(func_name)
        assert sym is not None, f"Expected {func_name} in global scope"
        assert sym.kind == SymbolKind.BUILTIN_FUNC
        assert sym.data_type == DataType.SERIES
        assert "param_types" in sym.extra


def test_enter_and_exit_scope():
    """Verify scope hierarchy and parent-pointer transitions."""
    symtab = SymbolTable()
    assert symtab.current_scope.name == "global"

    strat_scope = symtab.enter_scope("StrategyA")
    assert symtab.current_scope.name == "StrategyA"
    assert strat_scope.parent.name == "global"

    parent = symtab.exit_scope()
    assert symtab.current_scope.name == "global"
    assert parent.name == "global"


def test_define_and_resolve_local_symbol():
    """Verify defining and looking up local indicators in strategy scope."""
    symtab = SymbolTable()
    symtab.enter_scope("TrendStrategy")

    symtab.define_indicator("sma_50", "SMA", ["CLOSE", 50], line=6, col=5)
    sym = symtab.lookup("sma_50")

    assert sym is not None
    assert sym.name == "sma_50"
    assert sym.kind == SymbolKind.INDICATOR
    assert sym.data_type == DataType.SERIES
    assert sym.scope_name == "TrendStrategy"
    assert sym.line == 6


def test_hierarchical_resolution_from_child_to_global():
    """Verify child scope can resolve global symbols without local redeclaration."""
    symtab = SymbolTable()
    symtab.enter_scope("ChildScope")

    # Should find global built-in CLOSE and SMA from inside ChildScope
    close_sym = symtab.lookup("CLOSE")
    assert close_sym is not None
    assert close_sym.scope_name == "global"

    sma_sym = symtab.lookup("SMA")
    assert sma_sym is not None
    assert sma_sym.scope_name == "global"


def test_scope_isolation_between_strategies():
    """Verify symbols declared in Strategy A are invisible in Strategy B."""
    symtab = SymbolTable()

    symtab.enter_scope("StrategyA")
    symtab.define_indicator("alpha_ind", "SMA", ["CLOSE", 20])
    symtab.exit_scope()

    symtab.enter_scope("StrategyB")
    # alpha_ind should NOT be visible in StrategyB
    assert symtab.lookup("alpha_ind") is None
    # Can define an identically named indicator in StrategyB without collision
    symtab.define_indicator("alpha_ind", "EMA", ["CLOSE", 10])
    sym_b = symtab.lookup("alpha_ind")
    assert sym_b is not None
    assert sym_b.scope_name == "StrategyB"
    assert sym_b.extra["func"] == "EMA"


def test_duplicate_definition_raises_key_error():
    """Verify re-declaring the same symbol in the same scope raises KeyError."""
    symtab = SymbolTable()
    symtab.enter_scope("DupScope")

    symtab.define_indicator("my_rsi", "RSI", ["CLOSE", 14], line=5)
    with pytest.raises(KeyError) as exc_info:
        symtab.define_indicator("my_rsi", "RSI", ["CLOSE", 7], line=10)

    assert "already defined in scope 'DupScope'" in str(exc_info.value)


def test_cannot_exit_global_scope():
    """Verify exiting the root global scope raises RuntimeError."""
    symtab = SymbolTable()
    with pytest.raises(RuntimeError):
        symtab.exit_scope()


def test_format_table_output():
    """Verify ASCII symbol table formatting produces readable columns."""
    symtab = SymbolTable()
    symtab.enter_scope("MyStrategy")
    symtab.define_indicator("fast_ema", "EMA", ["CLOSE", 9])

    table_str = symtab.format_table()
    assert "Scope" in table_str
    assert "Symbol Name" in table_str
    assert "Data Type" in table_str
    assert "global" in table_str
    assert "MyStrategy" in table_str
    assert "fast_ema" in table_str
