"""
compiler/semantic.py — SwayaLang Semantic Analyzer
===================================================
Phase 2 deliverable for BCSE307P Compiler Design Laboratory.

Responsibility:
    Perform semantic analysis, type checking, scope validation, declaration
    verification, and domain-specific rule consistency checks on the AST
    produced by the parser.

Key Compiler Checks:
    1. Scope Management & Declarations:
       - No duplicate strategy names within a program.
       - No duplicate indicator declarations within the same strategy scope.
       - No shadowing of built-in keywords, functions, or price fields.
       - Every identifier referenced in rules must be declared in the symbol table.
       - Scope isolation: indicators declared in Strategy A cannot be accessed in Strategy B.
    2. Indicator Function Signatures:
       - Built-in indicator functions (SMA, EMA, RSI) must receive valid argument counts.
       - First argument must be a valid price field or series identifier.
       - Period argument must be a positive integer literal (> 0).
    3. Type Checking:
       - Comparison operators (>, <, >=, <=, ==) require numeric/series operands and produce BOOL.
       - Arithmetic operators (+, -, *, /) require numeric/series operands and produce numeric values.
       - Static division by zero detection on constant denominators.
       - Boolean combinators (AND, OR) require BOOL conditions.
    4. Domain-Specific Trading Semantics:
       - Every strategy must contain at least one ENTRY rule.
       - ENTRY_PRICE reference is invalid in ENTRY rules (position not yet active).
       - Order quantity in BUY/SHORT actions must be strictly positive.
    5. Dead-Code / Unused Identifier Detection:
       - Emits warnings for declared indicators that are never referenced in rule conditions.

Usage:
    from compiler.semantic import SemanticAnalyzer, SemanticError
    analyzer = SemanticAnalyzer()
    symtab, errors, warnings = analyzer.analyze(ast_root)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

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
from compiler.symbol_table import DataType, Scope, Symbol, SymbolKind, SymbolTable


# ---------------------------------------------------------------------------
# Semantic Diagnostics
# ---------------------------------------------------------------------------

class SemanticError(Exception):
    """Raised when a semantic violation or type error is detected."""

    def __init__(
        self,
        message: str,
        strategy_name: Optional[str] = None,
        line: Optional[int] = None,
        col: Optional[int] = None,
    ) -> None:
        loc = f" in strategy '{strategy_name}'" if strategy_name else ""
        pos = f" at line {line}, col {col}" if line is not None else ""
        super().__init__(f"SemanticError{loc}{pos}: {message}")
        self.message = message
        self.strategy_name = strategy_name
        self.line = line
        self.col = col


@dataclass
class SemanticWarning:
    """Represents a non-fatal semantic warning (e.g. unused indicator)."""
    message: str
    strategy_name: Optional[str] = None
    line: Optional[int] = None
    col: Optional[int] = None

    def __str__(self) -> str:
        loc = f" in strategy '{self.strategy_name}'" if self.strategy_name else ""
        pos = f" at line {line}" if (line := self.line) is not None else ""
        return f"SemanticWarning{loc}{pos}: {self.message}"


# ---------------------------------------------------------------------------
# Semantic Analyzer Visitor
# ---------------------------------------------------------------------------

class SemanticAnalyzer:
    """
    Traverses the Abstract Syntax Tree (AST) to populate the symbol table
    and enforce type and semantic invariants.
    """

    def __init__(self, fail_fast: bool = True) -> None:
        """
        Args:
            fail_fast: If True, raises SemanticError on first error encountered.
                       If False, accumulates all errors in self.errors.
        """
        self.fail_fast: bool = fail_fast
        self.symbol_table: SymbolTable = SymbolTable()
        self.errors: List[SemanticError] = []
        self.warnings: List[SemanticWarning] = []
        self._current_strategy: Optional[str] = None
        self._current_rule_kind: Optional[str] = None
        self._used_identifiers: Set[str] = set()

    def error(
        self,
        message: str,
        line: Optional[int] = None,
        col: Optional[int] = None,
    ) -> None:
        """Record a semantic error or immediately raise if fail_fast is True."""
        err = SemanticError(
            message=message,
            strategy_name=self._current_strategy,
            line=line,
            col=col,
        )
        self.errors.append(err)
        if self.fail_fast:
            raise err

    def warn(
        self,
        message: str,
        line: Optional[int] = None,
        col: Optional[int] = None,
    ) -> None:
        """Record a semantic warning."""
        self.warnings.append(
            SemanticWarning(
                message=message,
                strategy_name=self._current_strategy,
                line=line,
                col=col,
            )
        )

    # ------------------------------------------------------------------
    # Top-Level Analysis
    # ------------------------------------------------------------------

    def analyze(
        self, program: ProgramNode
    ) -> Tuple[SymbolTable, List[SemanticError], List[SemanticWarning]]:
        """
        Run the complete semantic analysis pass on a ProgramNode AST.

        Returns:
            (symbol_table, errors, warnings)
        """
        self.errors.clear()
        self.warnings.clear()
        self.symbol_table = SymbolTable()

        seen_strategies: Set[str] = set()
        for strategy in program.strategies:
            if strategy.name in seen_strategies:
                self.error(f"Duplicate strategy name '{strategy.name}'")
            seen_strategies.add(strategy.name)
            self._visit_strategy(strategy)

        return self.symbol_table, self.errors, self.warnings

    # ------------------------------------------------------------------
    # Strategy Block Validation
    # ------------------------------------------------------------------

    def _visit_strategy(self, strategy: StrategyNode) -> None:
        self._current_strategy = strategy.name
        self._used_identifiers.clear()

        # Enter child scope for this strategy
        scope = self.symbol_table.enter_scope(strategy.name)

        # 1. Validate INDICATOR declarations
        declared_indicators: Set[str] = set()
        for ind in strategy.indicators:
            self._visit_indicator(ind, declared_indicators)

        # 2. Validate Rule Blocks
        has_entry = False
        for rule in strategy.rules:
            if rule.kind == "ENTRY":
                has_entry = True
            self._visit_rule_block(rule)

        if not has_entry:
            self.error(f"Strategy '{strategy.name}' must declare at least one 'ENTRY' rule")

        # 3. Check for declared but unused indicators
        for ind_name in declared_indicators:
            if ind_name not in self._used_identifiers:
                self.warn(f"Indicator '{ind_name}' is declared but never used in any rule")

        # Exit child scope
        self.symbol_table.exit_scope()
        self._current_strategy = None

    # ------------------------------------------------------------------
    # Indicator Declarations
    # ------------------------------------------------------------------

    def _visit_indicator(
        self, ind: IndicatorDeclNode, declared_indicators: Set[str]
    ) -> None:
        name = ind.name

        # Check for shadowing built-in keywords/price fields/functions
        global_sym = self.symbol_table.global_scope.lookup(name, local_only=True)
        if global_sym is not None:
            self.error(
                f"Indicator '{name}' shadows built-in {global_sym.kind.value} '{name}'"
            )

        # Check for duplicate declaration in current strategy scope
        if name in declared_indicators or self.symbol_table.lookup(name, local_only=True):
            self.error(f"Duplicate indicator declaration '{name}'")

        declared_indicators.add(name)

        # Validate function call
        func_call = ind.func_call
        self._validate_indicator_call(func_call)

        # Insert symbol into strategy scope
        self.symbol_table.define_indicator(
            name=name,
            func_name=func_call.name,
            args=[self._extract_arg_repr(a) for a in func_call.args],
        )

    def _extract_arg_repr(self, arg: ASTNode) -> str:
        if isinstance(arg, IdentNode):
            return arg.name
        elif isinstance(arg, NumberLitNode):
            return str(int(arg.value) if arg.value.is_integer() else arg.value)
        return str(arg)

    def _validate_indicator_call(self, func_call: FuncCallNode) -> None:
        fname = func_call.name.upper()
        sym = self.symbol_table.lookup(fname)

        if sym is None or sym.kind != SymbolKind.BUILTIN_FUNC:
            self.error(f"Unknown indicator function '{func_call.name}'")
            return

        expected_params: List[DataType] = sym.extra.get("param_types", [])
        if len(func_call.args) != len(expected_params):
            self.error(
                f"Function '{fname}' expects {len(expected_params)} arguments "
                f"({', '.join(p.value for p in expected_params)}), got {len(func_call.args)}"
            )
            return

        # Check first argument: price series
        arg0 = func_call.args[0]
        if isinstance(arg0, IdentNode):
            arg0_sym = self.symbol_table.lookup(arg0.name)
            if arg0_sym is None or arg0_sym.data_type != DataType.SERIES:
                self.error(
                    f"First argument to '{fname}' must be a price series or indicator, "
                    f"got '{arg0.name}'"
                )
        else:
            self.error(f"First argument to '{fname}' must be a price field or series identifier")

        # Check second argument: integer period > 0
        arg1 = func_call.args[1]
        if isinstance(arg1, NumberLitNode):
            if not arg1.value.is_integer() or arg1.value <= 0:
                self.error(
                    f"Period argument to '{fname}' must be a positive integer > 0, "
                    f"got {arg1.raw}"
                )
        elif isinstance(arg1, IdentNode):
            period_sym = self.symbol_table.lookup(arg1.name)
            if period_sym is None or period_sym.data_type != DataType.INT:
                self.error(
                    f"Period argument to '{fname}' must resolve to an integer, got '{arg1.name}'"
                )
        else:
            self.error(f"Second argument to '{fname}' must be a numeric period")

    # ------------------------------------------------------------------
    # Rule Block Validation
    # ------------------------------------------------------------------

    def _visit_rule_block(self, rule: RuleBlockNode) -> None:
        valid_kinds = {"ENTRY", "EXIT", "STOP_LOSS", "TAKE_PROFIT"}
        if rule.kind not in valid_kinds:
            self.error(f"Unknown rule kind '{rule.kind}'")

        self._current_rule_kind = rule.kind

        # 1. Validate Action
        self._visit_action(rule.action, rule.kind)

        # 2. Validate Condition
        cond_type = self._visit_condition(rule.condition)
        if cond_type != DataType.BOOL:
            self.error(f"Rule condition must evaluate to a boolean expression, got {cond_type.value}")

        self._current_rule_kind = None

    def _visit_action(self, action: ActionNode, rule_kind: str) -> None:
        if action.action == "BUY":
            if not action.all_flag and (action.quantity is None or action.quantity <= 0):
                self.error("BUY action requires a positive quantity of shares")
        elif action.action == "SHORT":
            if action.quantity is None or action.quantity <= 0:
                self.error("SHORT action requires a positive quantity of shares")
        elif action.action == "SELL":
            if not action.all_flag and (action.quantity is None or action.quantity <= 0):
                self.error("SELL action requires 'ALL' or a positive quantity of shares")

    # ------------------------------------------------------------------
    # Condition and Expression Type Checking
    # ------------------------------------------------------------------

    def _visit_condition(self, node: ASTNode) -> DataType:
        """Validate boolean condition tree, returning DataType.BOOL."""
        if isinstance(node, BoolOpNode):
            left_t = self._visit_condition(node.left)
            right_t = self._visit_condition(node.right)
            if left_t != DataType.BOOL or right_t != DataType.BOOL:
                self.error(
                    f"Boolean operator '{node.op}' requires boolean operands, "
                    f"got {left_t.value} and {right_t.value}"
                )
            return DataType.BOOL

        elif isinstance(node, ComparisonNode):
            left_t = self._visit_expr(node.left)
            right_t = self._visit_expr(node.right)
            numeric_types = {DataType.FLOAT, DataType.INT, DataType.SERIES}
            if left_t not in numeric_types or right_t not in numeric_types:
                self.error(
                    f"Comparison operator '{node.op}' requires numeric or series operands, "
                    f"got {left_t.value} and {right_t.value}"
                )
            return DataType.BOOL

        else:
            self.error(f"Invalid condition node type '{type(node).__name__}'")
            return DataType.UNKNOWN

    def _visit_expr(self, node: ASTNode) -> DataType:
        """Validate arithmetic expression tree, returning resultant DataType."""
        if isinstance(node, NumberLitNode):
            return DataType.INT if node.value.is_integer() else DataType.FLOAT

        elif isinstance(node, IdentNode):
            name = node.name
            sym = self.symbol_table.lookup(name)

            if sym is None:
                self.error(f"Undeclared identifier '{name}'")
                return DataType.UNKNOWN

            # Check ENTRY_PRICE domain rule
            if name == "ENTRY_PRICE" and self._current_rule_kind == "ENTRY":
                self.error(
                    "ENTRY_PRICE cannot be referenced in an 'ENTRY' rule "
                    "(no trade position exists before entry)"
                )

            self._used_identifiers.add(name)
            return sym.data_type

        elif isinstance(node, BinOpExprNode):
            left_t = self._visit_expr(node.left)
            right_t = self._visit_expr(node.right)

            # Check division by zero on literal constants
            if node.op == "/" and isinstance(node.right, NumberLitNode) and node.right.value == 0:
                self.error("Division by zero in arithmetic expression")

            numeric_types = {DataType.FLOAT, DataType.INT, DataType.SERIES}
            if left_t not in numeric_types or right_t not in numeric_types:
                self.error(
                    f"Arithmetic operator '{node.op}' requires numeric operands, "
                    f"got {left_t.value} and {right_t.value}"
                )
                return DataType.UNKNOWN

            # Series propagation: any operation involving a series yields a series
            if left_t == DataType.SERIES or right_t == DataType.SERIES:
                return DataType.SERIES
            if left_t == DataType.FLOAT or right_t == DataType.FLOAT or node.op == "/":
                return DataType.FLOAT
            return DataType.INT

        else:
            self.error(f"Unexpected expression node type '{type(node).__name__}'")
            return DataType.UNKNOWN
