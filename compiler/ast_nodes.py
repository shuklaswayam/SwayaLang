"""
compiler/ast_nodes.py — SwayaLang AST Node Definitions
=======================================================
Phase 1 deliverable for BCSE307P Compiler Design Laboratory.

Responsibility:
    Define the dataclasses that form the Abstract Syntax Tree (AST).
    Each node carries its semantic content and a ``pretty_print`` method
    that renders an indented, human-readable tree representation (2 spaces
    per indentation level).

Node hierarchy:
    ProgramNode
    └── StrategyNode (one per STRATEGY block)
        ├── IndicatorDeclNode  (zero or more INDICATOR declarations)
        └── RuleBlockNode      (one or more ENTRY/EXIT/STOP_LOSS/TAKE_PROFIT rules)
            ├── ActionNode     (BUY / SELL / SHORT)
            └── ConditionNode  (binary comparison or boolean combinator)
                └── ExprNode   (leaf: number, identifier, price field;
                                 or binary arithmetic expression)

Design notes:
    - All nodes are frozen dataclasses for immutability.
    - ``pretty_print(indent, file)`` outputs human-readable indented text.
    - ``to_str(indent)`` returns the pretty-printed string directly.
    - No external dependencies used.

Usage:
    from compiler.ast_nodes import ProgramNode
    program_node.pretty_print()
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any, List, Optional

_INDENT = "  "  # 2-space indent per level


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class ASTNode:
    """Abstract base class for all AST nodes."""

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        """Print a human-readable, indented representation of this node.

        Args:
            indent: Current indentation level (0 = root). Each level adds
                    ``_INDENT`` (2 spaces) of leading whitespace.
            file:   Optional destination stream; defaults to sys.stdout.
        """
        raise NotImplementedError(f"{type(self).__name__}.pretty_print not implemented")

    def to_str(self, indent: int = 0) -> str:
        """Return the pretty-printed representation as a string."""
        buf = io.StringIO()
        self.pretty_print(indent=indent, file=buf)
        return buf.getvalue()

    def _prefix(self, indent: int) -> str:
        return _INDENT * indent


# ---------------------------------------------------------------------------
# Expression nodes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NumberLitNode(ASTNode):
    """A numeric literal (integer or decimal)."""
    value: float
    raw:   str

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        print(f"{self._prefix(indent)}NumberLit({self.raw})", file=file)


@dataclass(frozen=True)
class IdentNode(ASTNode):
    """An identifier (indicator variable name or built-in price field)."""
    name: str

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        print(f"{self._prefix(indent)}Ident({self.name})", file=file)


@dataclass(frozen=True)
class BinOpExprNode(ASTNode):
    """A binary arithmetic expression (e.g. ``ENTRY_PRICE * 0.95``)."""
    op:    str
    left:  ASTNode
    right: ASTNode

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        print(f"{self._prefix(indent)}BinOpExpr(op={self.op!r})", file=file)
        self.left.pretty_print(indent + 1, file=file)
        self.right.pretty_print(indent + 1, file=file)


# ---------------------------------------------------------------------------
# Condition nodes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ComparisonNode(ASTNode):
    """A comparison expression (e.g. ``sma_50 > sma_200``)."""
    op:    str
    left:  ASTNode
    right: ASTNode

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        print(f"{self._prefix(indent)}Comparison(op={self.op!r})", file=file)
        self.left.pretty_print(indent + 1, file=file)
        self.right.pretty_print(indent + 1, file=file)


@dataclass(frozen=True)
class BoolOpNode(ASTNode):
    """A boolean combinator joining two conditions with AND or OR."""
    op:    str
    left:  ASTNode
    right: ASTNode

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        print(f"{self._prefix(indent)}BoolOp(op={self.op!r})", file=file)
        self.left.pretty_print(indent + 1, file=file)
        self.right.pretty_print(indent + 1, file=file)


# ---------------------------------------------------------------------------
# Action node
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FuncCallNode(ASTNode):
    """A built-in indicator function call (e.g. ``SMA(CLOSE, 50)``)."""
    name: str
    args: List[ASTNode]

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        print(f"{self._prefix(indent)}FuncCall(name={self.name!r})", file=file)
        for arg in self.args:
            arg.pretty_print(indent + 1, file=file)


@dataclass(frozen=True)
class ActionNode(ASTNode):
    """A trade action: BUY, SELL, or SHORT."""
    action:   str
    quantity: Optional[float]
    all_flag: bool
    ticker:   Optional[str]

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        qty_str = "ALL" if self.all_flag else str(self.quantity)
        ticker_str = f", ticker={self.ticker!r}" if self.ticker else ""
        print(f"{self._prefix(indent)}Action(action={self.action!r}, qty={qty_str}{ticker_str})", file=file)


# ---------------------------------------------------------------------------
# Declaration and rule nodes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IndicatorDeclNode(ASTNode):
    """An INDICATOR declaration (e.g. ``INDICATOR sma_50 = SMA(CLOSE, 50)``)."""
    name:      str
    func_call: FuncCallNode

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        print(f"{self._prefix(indent)}IndicatorDecl(name={self.name!r})", file=file)
        self.func_call.pretty_print(indent + 1, file=file)


@dataclass(frozen=True)
class RuleBlockNode(ASTNode):
    """A trading rule block: ENTRY, EXIT, STOP_LOSS, or TAKE_PROFIT."""
    kind:      str
    action:    ActionNode
    condition: ASTNode

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        print(f"{self._prefix(indent)}RuleBlock(kind={self.kind!r})", file=file)
        print(f"{self._prefix(indent + 1)}action:", file=file)
        self.action.pretty_print(indent + 2, file=file)
        print(f"{self._prefix(indent + 1)}condition:", file=file)
        self.condition.pretty_print(indent + 2, file=file)


# ---------------------------------------------------------------------------
# Top-level nodes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StrategyNode(ASTNode):
    """A STRATEGY block (the primary top-level construct)."""
    name:       str
    indicators: List[IndicatorDeclNode]
    rules:      List[RuleBlockNode]

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        print(f"{self._prefix(indent)}Strategy(name={self.name!r})", file=file)
        if self.indicators:
            print(f"{self._prefix(indent + 1)}indicators:", file=file)
            for ind in self.indicators:
                ind.pretty_print(indent + 2, file=file)
        if self.rules:
            print(f"{self._prefix(indent + 1)}rules:", file=file)
            for rule in self.rules:
                rule.pretty_print(indent + 2, file=file)


@dataclass(frozen=True)
class ProgramNode(ASTNode):
    """The root node of the AST — represents the entire .strat file."""
    strategies: List[StrategyNode]

    def pretty_print(self, indent: int = 0, file: Any = None) -> None:
        print(f"{self._prefix(indent)}Program (strategies={len(self.strategies)})", file=file)
        for strategy in self.strategies:
            strategy.pretty_print(indent + 1, file=file)
