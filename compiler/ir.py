"""
compiler/ir.py — SwayaLang Intermediate Code Generator (Three-Address Code)
============================================================================
Phase 2 deliverable for BCSE307P Compiler Design Laboratory.

Responsibility:
    Translate the semantically validated Abstract Syntax Tree (AST) into an
    intermediate representation (IR) based on linearized Three-Address Code (TAC)
    using quadruples (op, arg1, arg2, result).

Compiler Concepts:
    - Intermediate Code Generation (ICG) as a machine-independent representation.
    - Quadruple structure: (operator, argument 1, argument 2, result).
    - Temporary variable allocation (t0, t1, t2, ...).
    - Label generation (L0, L1, L2, ...) for control-flow branching.
    - Linearization of nested arithmetic, comparison, and boolean expressions.
    - Action and indicator call lowering.

Example Quadruple Output:
    t0 = CALL SMA(CLOSE, 50)
    sma_50 = t0
    t1 = sma_50 > sma_200
    t2 = rsi_14 < 30
    t3 = t1 AND t2
    if not t3 goto L1
    ACTION BUY 100.0 SHARES OF 'AAPL'
    L1:

Usage:
    from compiler.ir import IRGenerator
    ir_gen = IRGenerator()
    ir_prog = ir_gen.generate(ast_root)
    print(ir_prog.dump())
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

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
# Quadruple Representation
# ---------------------------------------------------------------------------

@dataclass
class Quad:
    """
    A single Three-Address Code instruction in quadruple format:
        result = arg1 op arg2
    """
    op:     str
    arg1:   Optional[str] = None
    arg2:   Optional[str] = None
    result: Optional[str] = None

    def __str__(self) -> str:
        """Format the quadruple into readable Three-Address Code."""
        if self.op.startswith(";"):
            return f"    {self.op} {self.arg1 or ''}"
        elif self.op == "LABEL":
            return f"{self.result}:"
        elif self.op == "GOTO":
            return f"    goto {self.result}"
        elif self.op == "IF_TRUE":
            return f"    if {self.arg1} goto {self.result}"
        elif self.op == "IF_FALSE":
            return f"    if not {self.arg1} goto {self.result}"
        elif self.op == "ASSIGN":
            return f"    {self.result} = {self.arg1}"
        elif self.op == "CALL_IND":
            return f"    {self.result} = CALL {self.arg1}({self.arg2})"
        elif self.op == "ACTION":
            return f"    ACTION {self.arg1} {self.arg2}" + (f" OF {self.result!r}" if self.result else "")
        elif self.op in ("+", "-", "*", "/", ">", "<", ">=", "<=", "==", "AND", "OR"):
            return f"    {self.result} = {self.arg1} {self.op} {self.arg2}"
        else:
            return f"    {self.result} = {self.op} {self.arg1}, {self.arg2}"


# ---------------------------------------------------------------------------
# IR Strategy and Program Containers
# ---------------------------------------------------------------------------

@dataclass
class IRStrategy:
    """Intermediate code for a single strategy block."""
    name: str
    indicator_quads: List[Quad]
    rule_quads:      List[Quad]

    @property
    def all_quads(self) -> List[Quad]:
        return self.indicator_quads + self.rule_quads

    def dump(self) -> str:
        lines: List[str] = [f"; --- STRATEGY: {self.name} ---"]
        if self.indicator_quads:
            lines.append("; [Indicator Setup]")
            for q in self.indicator_quads:
                lines.append(str(q))
        if self.rule_quads:
            lines.append("; [Rule Execution Flow]")
            for q in self.rule_quads:
                lines.append(str(q))
        return "\n".join(lines)


@dataclass
class IRProgram:
    """Root container holding all lowered strategies in Three-Address Code."""
    strategies: List[IRStrategy]

    def dump(self) -> str:
        lines: List[str] = [
            "; ==========================================================================",
            "; SwayaLang Intermediate Representation — Three-Address Code (TAC)",
            "; ==========================================================================",
        ]
        for strat in self.strategies:
            lines.append("")
            lines.append(strat.dump())
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# IR Generator Visitor
# ---------------------------------------------------------------------------

class IRGenerator:
    """
    Translates AST into Three-Address Code quadruples with synthetic temporaries
    (t0, t1, ...) and control labels (L0, L1, ...).
    """

    def __init__(self) -> None:
        self._temp_count: int = 0
        self._label_count: int = 0

    def new_temp(self) -> str:
        """Allocate a fresh temporary variable identifier."""
        name = f"t{self._temp_count}"
        self._temp_count += 1
        return name

    def new_label(self) -> str:
        """Allocate a fresh jump label."""
        name = f"L{self._label_count}"
        self._label_count += 1
        return name

    def generate(self, program: ProgramNode) -> IRProgram:
        """Generate intermediate code for an entire ProgramNode."""
        self._temp_count = 0
        self._label_count = 0
        ir_strategies: List[IRStrategy] = []

        for strat in program.strategies:
            ir_strategies.append(self._generate_strategy(strat))

        return IRProgram(strategies=ir_strategies)

    def _generate_strategy(self, strategy: StrategyNode) -> IRStrategy:
        indicator_quads: List[Quad] = []
        rule_quads: List[Quad] = []

        # 1. Lower Indicators
        for ind in strategy.indicators:
            args_str = ", ".join(self._arg_to_str(a) for a in ind.func_call.args)
            t_call = self.new_temp()
            indicator_quads.append(
                Quad(
                    op="CALL_IND",
                    arg1=ind.func_call.name,
                    arg2=args_str,
                    result=t_call,
                )
            )
            indicator_quads.append(
                Quad(
                    op="ASSIGN",
                    arg1=t_call,
                    result=ind.name,
                )
            )

        # 2. Lower Rules
        for rule in strategy.rules:
            quads = self._generate_rule(rule)
            rule_quads.extend(quads)

        return IRStrategy(
            name=strategy.name,
            indicator_quads=indicator_quads,
            rule_quads=rule_quads,
        )

    def _generate_rule(self, rule: RuleBlockNode) -> List[Quad]:
        quads: List[Quad] = []
        quads.append(Quad(op="; RULE_START", arg1=rule.kind))

        # Evaluate condition expression -> returns temp holding boolean result
        cond_temp, cond_quads = self._lower_condition(rule.condition)
        quads.extend(cond_quads)

        # Skip label if condition evaluates to False
        skip_label = self.new_label()
        quads.append(Quad(op="IF_FALSE", arg1=cond_temp, result=skip_label))

        # Action emission
        action = rule.action
        qty_str = "ALL" if action.all_flag else f"{action.quantity} SHARES"
        quads.append(
            Quad(
                op="ACTION",
                arg1=f"[{rule.kind}] {action.action}",
                arg2=qty_str,
                result=action.ticker,
            )
        )

        # Label target for false condition
        quads.append(Quad(op="LABEL", result=skip_label))
        return quads

    # ------------------------------------------------------------------
    # Condition Lowering
    # ------------------------------------------------------------------

    def _lower_condition(self, node: ASTNode) -> Tuple[str, List[Quad]]:
        quads: List[Quad] = []

        if isinstance(node, BoolOpNode):
            left_t, left_q = self._lower_condition(node.left)
            right_t, right_q = self._lower_condition(node.right)
            quads.extend(left_q)
            quads.extend(right_q)
            res_t = self.new_temp()
            quads.append(
                Quad(
                    op=node.op,
                    arg1=left_t,
                    arg2=right_t,
                    result=res_t,
                )
            )
            return res_t, quads

        elif isinstance(node, ComparisonNode):
            left_t, left_q = self._lower_expr(node.left)
            right_t, right_q = self._lower_expr(node.right)
            quads.extend(left_q)
            quads.extend(right_q)
            res_t = self.new_temp()
            quads.append(
                Quad(
                    op=node.op,
                    arg1=left_t,
                    arg2=right_t,
                    result=res_t,
                )
            )
            return res_t, quads

        else:
            res_t = self.new_temp()
            quads.append(Quad(op="ASSIGN", arg1=str(node), result=res_t))
            return res_t, quads

    # ------------------------------------------------------------------
    # Arithmetic Expression Lowering
    # ------------------------------------------------------------------

    def _lower_expr(self, node: ASTNode) -> Tuple[str, List[Quad]]:
        quads: List[Quad] = []

        if isinstance(node, NumberLitNode):
            val_str = str(int(node.value) if node.value.is_integer() else node.value)
            return val_str, []

        elif isinstance(node, IdentNode):
            return node.name, []

        elif isinstance(node, BinOpExprNode):
            left_t, left_q = self._lower_expr(node.left)
            right_t, right_q = self._lower_expr(node.right)
            quads.extend(left_q)
            quads.extend(right_q)
            res_t = self.new_temp()
            quads.append(
                Quad(
                    op=node.op,
                    arg1=left_t,
                    arg2=right_t,
                    result=res_t,
                )
            )
            return res_t, quads

        else:
            res_t = self.new_temp()
            quads.append(Quad(op="ASSIGN", arg1=str(node), result=res_t))
            return res_t, quads

    def _arg_to_str(self, arg: ASTNode) -> str:
        if isinstance(arg, IdentNode):
            return arg.name
        elif isinstance(arg, NumberLitNode):
            return str(int(arg.value) if arg.value.is_integer() else arg.value)
        return str(arg)
