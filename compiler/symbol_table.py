"""
compiler/symbol_table.py — SwayaLang Scoped Symbol Table
=========================================================
Phase 2 deliverable for BCSE307P Compiler Design Laboratory.

Responsibility:
    Manage identifier declarations, scopes, built-in functions, price fields,
    and type tracking across SwayaLang programs. Supports nested lexical scoping
    (Global scope for built-ins, Strategy scope for per-strategy indicators).

Scope Hierarchy:
    GlobalScope (built-in indicators SMA, EMA, RSI; price fields CLOSE, OPEN, etc.)
    └── StrategyScope("<strategy_name>")
        ├── Indicator symbols declared via INDICATOR
        └── Local variables / runtime bindings (ENTRY_PRICE)

Compiler Concepts:
    - Multi-level hierarchical scoping (parent-pointer tree).
    - Static symbol insertion and resolution (lexical scoping).
    - Scope isolation: indicators in Strategy A are invisible in Strategy B.
    - Symbol classification (built-in function, indicator, price field, variable).
    - ASCII tabular visualization for review and viva inspection.

Usage:
    from compiler.symbol_table import SymbolTable, SymbolKind, DataType
    symtab = SymbolTable()
    symtab.enter_scope("GoldenCross")
    symtab.define_indicator("sma_50", "SMA", ["CLOSE", 50])
    symbol = symtab.lookup("sma_50")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data Types and Symbol Kinds
# ---------------------------------------------------------------------------

class DataType(Enum):
    """Data types supported in SwayaLang's type system."""
    FLOAT   = "FLOAT"     # Numeric scalar or floating-point constant
    INT     = "INT"       # Integer scalar (used for indicator periods, quantities)
    BOOL    = "BOOL"      # Boolean truth value (result of comparisons/conditions)
    STRING  = "STRING"    # Ticker symbols, strategy names
    SERIES  = "SERIES"    # Time-series vector (price fields, indicator outputs)
    VOID    = "VOID"      # Actions / statements without a return value
    UNKNOWN = "UNKNOWN"   # Unresolved / erroneous type

    def __str__(self) -> str:
        return self.value


class SymbolKind(Enum):
    """Classification of symbols in the symbol table."""
    BUILTIN_FUNC = "BUILTIN_FUNC"  # Built-in technical indicator (SMA, EMA, RSI)
    PRICE_FIELD  = "PRICE_FIELD"   # Built-in bar price field (CLOSE, OPEN, etc.)
    INDICATOR    = "INDICATOR"     # User-declared indicator variable
    VARIABLE     = "VARIABLE"      # Runtime variable (e.g. ENTRY_PRICE)
    STRATEGY     = "STRATEGY"      # Strategy block identifier

    def __str__(self) -> str:
        return self.value


# ---------------------------------------------------------------------------
# Symbol Entries
# ---------------------------------------------------------------------------

@dataclass
class Symbol:
    """Base symbol representation in the symbol table."""
    name:       str
    kind:       SymbolKind
    data_type:  DataType
    scope_name: str
    line:       Optional[int] = None
    col:        Optional[int] = None
    extra:      Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"Symbol(name='{self.name}', kind={self.kind.value}, "
            f"type={self.data_type.value}, scope='{self.scope_name}')"
        )


# ---------------------------------------------------------------------------
# Scope Representation
# ---------------------------------------------------------------------------

class Scope:
    """
    A single lexical scope holding a mapping of symbol names to Symbol objects.
    Maintains a reference to its enclosing parent scope.
    """

    def __init__(self, name: str, parent: Optional[Scope] = None) -> None:
        self.name: str = name
        self.parent: Optional[Scope] = parent
        self.symbols: Dict[str, Symbol] = {}
        self.children: List[Scope] = []

    def define(self, symbol: Symbol) -> None:
        """Insert a symbol into the current scope.

        Raises:
            KeyError: if the symbol is already defined in the current local scope.
        """
        if symbol.name in self.symbols:
            existing = self.symbols[symbol.name]
            raise KeyError(
                f"Symbol '{symbol.name}' is already defined in scope '{self.name}' "
                f"(first declared at line {existing.line})"
            )
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str, local_only: bool = False) -> Optional[Symbol]:
        """Look up a symbol by name, walking up the parent chain unless local_only."""
        if name in self.symbols:
            return self.symbols[name]
        if not local_only and self.parent is not None:
            return self.parent.lookup(name, local_only=False)
        return None

    def is_locally_defined(self, name: str) -> bool:
        """Check if a symbol exists directly in this scope."""
        return name in self.symbols

    def get_all_symbols(self) -> List[Symbol]:
        """Return all symbols declared directly within this scope."""
        return list(self.symbols.values())


# ---------------------------------------------------------------------------
# Symbol Table Manager
# ---------------------------------------------------------------------------

class SymbolTable:
    """
    Symbol Table manager providing scope creation, symbol insertion,
    hierarchical resolution, and ASCII table visualization.
    """

    def __init__(self) -> None:
        self.global_scope = Scope(name="global")
        self.current_scope: Scope = self.global_scope
        self.all_scopes: List[Scope] = [self.global_scope]
        self._init_builtins()

    def _init_builtins(self) -> None:
        """Populate global scope with standard language built-ins."""
        # Built-in price fields (SERIES / FLOAT)
        price_fields = [
            ("CLOSE", "Closing price of current bar"),
            ("OPEN", "Opening price of current bar"),
            ("HIGH", "High price of current bar"),
            ("LOW", "Low price of current bar"),
            ("VOLUME", "Trading volume of current bar"),
            ("PRICE", "Current price (alias to CLOSE)"),
            ("ENTRY_PRICE", "Executed entry price of active trade"),
        ]
        for name, desc in price_fields:
            self.global_scope.define(
                Symbol(
                    name=name,
                    kind=SymbolKind.PRICE_FIELD,
                    data_type=DataType.SERIES,
                    scope_name="global",
                    extra={"description": desc},
                )
            )

        # Built-in indicator functions
        builtin_funcs = [
            (
                "SMA",
                [DataType.SERIES, DataType.INT],
                DataType.SERIES,
                "Simple Moving Average: SMA(series, period)",
            ),
            (
                "EMA",
                [DataType.SERIES, DataType.INT],
                DataType.SERIES,
                "Exponential Moving Average: EMA(series, period)",
            ),
            (
                "RSI",
                [DataType.SERIES, DataType.INT],
                DataType.SERIES,
                "Relative Strength Index: RSI(series, period)",
            ),
        ]
        for func_name, arg_types, ret_type, doc in builtin_funcs:
            self.global_scope.define(
                Symbol(
                    name=func_name,
                    kind=SymbolKind.BUILTIN_FUNC,
                    data_type=ret_type,
                    scope_name="global",
                    extra={"param_types": arg_types, "doc": doc},
                )
            )

    def enter_scope(self, name: str) -> Scope:
        """Create a new child scope under current_scope and enter it."""
        new_scope = Scope(name=name, parent=self.current_scope)
        self.current_scope.children.append(new_scope)
        self.all_scopes.append(new_scope)
        self.current_scope = new_scope
        return new_scope

    def exit_scope(self) -> Scope:
        """Exit the current scope back to its enclosing parent scope."""
        if self.current_scope.parent is None:
            raise RuntimeError("Cannot exit the root global scope")
        parent = self.current_scope.parent
        self.current_scope = parent
        return parent

    def define(self, symbol: Symbol) -> None:
        """Insert a symbol into the current active scope."""
        symbol.scope_name = self.current_scope.name
        self.current_scope.define(symbol)

    def define_indicator(
        self,
        name: str,
        func_name: str,
        args: List[Any],
        line: Optional[int] = None,
        col: Optional[int] = None,
    ) -> Symbol:
        """Helper to define an indicator symbol in the current scope."""
        sym = Symbol(
            name=name,
            kind=SymbolKind.INDICATOR,
            data_type=DataType.SERIES,
            scope_name=self.current_scope.name,
            line=line,
            col=col,
            extra={"func": func_name, "args": args},
        )
        self.define(sym)
        return sym

    def lookup(self, name: str, local_only: bool = False) -> Optional[Symbol]:
        """Look up a symbol by name starting from the current active scope."""
        return self.current_scope.lookup(name, local_only=local_only)

    def lookup_in_scope(self, scope_name: str, name: str) -> Optional[Symbol]:
        """Look up a symbol inside a specifically named scope."""
        for sc in self.all_scopes:
            if sc.name == scope_name:
                return sc.lookup(name, local_only=False)
        return None

    def format_table(self) -> str:
        """
        Generate a comprehensive, beautifully aligned ASCII table
        displaying all scopes and their symbols.
        """
        rows: List[Tuple[str, str, str, str, str]] = []
        for sc in self.all_scopes:
            for sym in sc.get_all_symbols():
                details = ""
                if sym.kind == SymbolKind.BUILTIN_FUNC:
                    types_str = ", ".join(t.value for t in sym.extra.get("param_types", []))
                    details = f"args=({types_str}) -> {sym.data_type.value}"
                elif sym.kind == SymbolKind.INDICATOR:
                    args_str = ", ".join(str(a) for a in sym.extra.get("args", []))
                    details = f"{sym.extra.get('func', '')}({args_str})"
                elif sym.kind == SymbolKind.PRICE_FIELD:
                    details = sym.extra.get("description", "Built-in series")
                else:
                    details = f"Line {sym.line}" if sym.line else "Runtime"

                rows.append((sc.name, sym.name, sym.kind.value, sym.data_type.value, details))

        if not rows:
            return "(Empty Symbol Table)"

        # Calculate column widths
        headers = ("Scope", "Symbol Name", "Kind", "Data Type", "Details / Signature")
        w_scope = max(len(headers[0]), max(len(r[0]) for r in rows))
        w_name  = max(len(headers[1]), max(len(r[1]) for r in rows))
        w_kind  = max(len(headers[2]), max(len(r[2]) for r in rows))
        w_type  = max(len(headers[3]), max(len(r[3]) for r in rows))
        w_det   = max(len(headers[4]), max(len(r[4]) for r in rows))

        sep = f"+-{'-' * w_scope}-+-{'-' * w_name}-+-{'-' * w_kind}-+-{'-' * w_type}-+-{'-' * w_det}-+"
        header_line = (
            f"| {headers[0].ljust(w_scope)} | {headers[1].ljust(w_name)} | "
            f"{headers[2].ljust(w_kind)} | {headers[3].ljust(w_type)} | {headers[4].ljust(w_det)} |"
        )

        lines = [sep, header_line, sep]
        curr_scope = None
        for sc, name, kind, dtype, det in rows:
            if curr_scope is not None and curr_scope != sc:
                lines.append(sep)
            curr_scope = sc
            lines.append(
                f"| {sc.ljust(w_scope)} | {name.ljust(w_name)} | "
                f"{kind.ljust(w_kind)} | {dtype.ljust(w_type)} | {det.ljust(w_det)} |"
            )
        lines.append(sep)
        return "\n".join(lines)
