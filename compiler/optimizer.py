"""
compiler/optimizer.py — SwayaLang Intermediate Representation & AST Optimizer
==============================================================================
Phase 3 deliverable for BCSE307P Compiler Design Laboratory.

Responsibility:
    Perform machine-independent code optimization passes on both the Abstract
    Syntax Tree (AST) and linearized Three-Address Code (TAC) Quadruples.

Compiler Optimization Passes Implemented:
    1. Constant Folding:
       - Compile-time evaluation of constant arithmetic operations:
         e.g., (100 * 0.95) -> 95.0, (10 - 8) -> 2.0, (2 * 50) -> 100.0.
       - Compile-time evaluation of constant comparison expressions:
         e.g., (100 > 50) -> True, (10 == 20) -> False.
       - Compile-time evaluation of boolean logic with identity and annihilator laws:
         e.g., True AND x -> x, False AND x -> False,
               True OR x -> True, False OR x -> x.
    2. Constant Propagation:
       - Tracking literal values assigned to temporary registers and substituting
         known constants into subsequent quadruples.
    3. Common Subexpression Elimination (CSE):
       - Value numbering / DAG-based common subexpression detection across
         quadruples within each strategy.
       - Deduplication of identical arithmetic, comparison, and technical indicator
         calls (e.g. repeated SMA(CLOSE, 50) or shared comparison expressions).
       - Commutative operator normalization (+, *, ==, AND, OR).
    4. Dead Code & Redundant Jump Elimination:
       - Removal of dead temporary assignments whose results are never read.
       - Elimination of conditional jumps with statically resolved conditions.
       - Removal of jumps to immediately following labels (fall-through optimization).
       - Elimination of unreachable labels.

Usage:
    from compiler.optimizer import Optimizer
    optimizer = Optimizer()
    # Optimize AST:
    opt_ast, ast_stats = optimizer.optimize_ast(ast_root)
    # Optimize TAC IR:
    opt_ir, ir_stats = optimizer.optimize_ir(ir_prog)
    print(ir_stats.format_summary())
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

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
from compiler.ir import IRProgram, IRStrategy, Quad


# ---------------------------------------------------------------------------
# Optimization Statistics Model
# ---------------------------------------------------------------------------

@dataclass
class OptimizationStats:
    """Quantitative tracking of transformations performed during optimization."""
    pass_name:                  str = "TAC & AST Optimization"
    initial_quad_count:         int = 0
    optimized_quad_count:       int = 0
    constant_folds:             int = 0
    constant_propagations:      int = 0
    cse_eliminations:           int = 0
    dead_code_eliminations:     int = 0
    redundant_jumps_eliminated: int = 0
    transformation_log:         List[str] = field(default_factory=list)

    @property
    def instructions_eliminated(self) -> int:
        return max(0, self.initial_quad_count - self.optimized_quad_count)

    @property
    def reduction_pct(self) -> float:
        if self.initial_quad_count == 0:
            return 0.0
        return (self.instructions_eliminated / self.initial_quad_count) * 100.0

    def log(self, message: str) -> None:
        self.transformation_log.append(message)

    def format_summary(self) -> str:
        """Format an ASCII table summarizing the optimization impact."""
        lines = [
            "+" + "-" * 62 + "+",
            "|      SWAYALANG COMPILER OPTIMIZATION AUDIT (PHASE 3)         |",
            "+" + "-" * 62 + "+",
            f"|  Initial TAC Quadruples:          {self.initial_quad_count:<25} |",
            f"|  Optimized TAC Quadruples:        {self.optimized_quad_count:<25} |",
            f"|  Instructions Eliminated:         {self.instructions_eliminated:<25} |",
            f"|  Code Size Reduction:             {self.reduction_pct:.2f}%{'':<21} |",
            "+" + "-" * 62 + "+",
            f"|  Constant Folding Passes:         {self.constant_folds:<25} |",
            f"|  Constant Propagations:           {self.constant_propagations:<25} |",
            f"|  Common Subexpressions (CSE):     {self.cse_eliminations:<25} |",
            f"|  Dead Code Instructions Pruned:   {self.dead_code_eliminations:<25} |",
            f"|  Redundant Jumps Eliminated:      {self.redundant_jumps_eliminated:<25} |",
            "+" + "-" * 62 + "+",
        ]
        if self.transformation_log:
            lines.append("| Transformations Applied:")
            for item in self.transformation_log[:8]:
                lines.append(f"|   * {item[:56]:<56} |")
            if len(self.transformation_log) > 8:
                lines.append(f"|   ... and {len(self.transformation_log) - 8} more transformation(s).{'':<18} |")
            lines.append("+" + "-" * 62 + "+")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# AST-Level Constant Folding (Constructing Fresh Frozen Nodes)
# ---------------------------------------------------------------------------

class ASTConstantFolder:
    """
    Recursively inspects and folds compile-time constant arithmetic,
    comparisons, and boolean expressions in the Abstract Syntax Tree.
    Constructs fresh immutable AST node instances.
    """

    def __init__(self, stats: OptimizationStats) -> None:
        self.stats = stats

    def fold_program(self, program: ProgramNode) -> ProgramNode:
        new_strategies: List[StrategyNode] = []
        for strat in program.strategies:
            new_strategies.append(self.fold_strategy(strat))
        return ProgramNode(strategies=new_strategies)

    def fold_strategy(self, strat: StrategyNode) -> StrategyNode:
        new_indicators: List[IndicatorDeclNode] = []
        for ind in strat.indicators:
            new_args = [self.fold_expr(arg) for arg in ind.func_call.args]
            new_func = FuncCallNode(name=ind.func_call.name, args=new_args)
            new_indicators.append(IndicatorDeclNode(name=ind.name, func_call=new_func))

        new_rules: List[RuleBlockNode] = []
        for rule in strat.rules:
            new_rules.append(self.fold_rule(rule))

        return StrategyNode(name=strat.name, indicators=new_indicators, rules=new_rules)

    def fold_rule(self, rule: RuleBlockNode) -> RuleBlockNode:
        new_cond = self.fold_condition(rule.condition)
        return RuleBlockNode(kind=rule.kind, action=rule.action, condition=new_cond)

    def fold_condition(self, node: ASTNode) -> ASTNode:
        if isinstance(node, BoolOpNode):
            left = self.fold_condition(node.left)
            right = self.fold_condition(node.right)

            left_bool = self._as_bool_const(left)
            right_bool = self._as_bool_const(right)

            if left_bool is not None and right_bool is not None:
                self.stats.constant_folds += 1
                val = (left_bool and right_bool) if node.op == "AND" else (left_bool or right_bool)
                self.stats.log(f"Folded BoolOp: {left_bool} {node.op} {right_bool} -> {val}")
                return self._make_num_node(1.0 if val else 0.0)

            if node.op == "AND":
                if left_bool is True:
                    self.stats.constant_folds += 1
                    self.stats.log("Folded True AND P -> P")
                    return right
                if right_bool is True:
                    self.stats.constant_folds += 1
                    self.stats.log("Folded P AND True -> P")
                    return left
                if left_bool is False or right_bool is False:
                    self.stats.constant_folds += 1
                    self.stats.log("Folded False AND P -> False")
                    return self._make_num_node(0.0)

            elif node.op == "OR":
                if left_bool is False:
                    self.stats.constant_folds += 1
                    self.stats.log("Folded False OR P -> P")
                    return right
                if right_bool is False:
                    self.stats.constant_folds += 1
                    self.stats.log("Folded P OR False -> P")
                    return left
                if left_bool is True or right_bool is True:
                    self.stats.constant_folds += 1
                    self.stats.log("Folded True OR P -> True")
                    return self._make_num_node(1.0)

            return BoolOpNode(op=node.op, left=left, right=right)

        elif isinstance(node, ComparisonNode):
            left = self.fold_expr(node.left)
            right = self.fold_expr(node.right)

            if isinstance(left, NumberLitNode) and isinstance(right, NumberLitNode):
                l_val = left.value
                r_val = right.value
                self.stats.constant_folds += 1
                res: bool
                if node.op == ">":
                    res = l_val > r_val
                elif node.op == "<":
                    res = l_val < r_val
                elif node.op == ">=":
                    res = l_val >= r_val
                elif node.op == "<=":
                    res = l_val <= r_val
                elif node.op == "==":
                    res = math.isclose(l_val, r_val, rel_tol=1e-5)
                else:
                    res = False
                self.stats.log(f"Folded Comparison: {l_val} {node.op} {r_val} -> {res}")
                return self._make_num_node(1.0 if res else 0.0)

            return ComparisonNode(op=node.op, left=left, right=right)

        return node

    def fold_expr(self, node: ASTNode) -> ASTNode:
        if isinstance(node, BinOpExprNode):
            left = self.fold_expr(node.left)
            right = self.fold_expr(node.right)

            if isinstance(left, NumberLitNode) and isinstance(right, NumberLitNode):
                l_val = left.value
                r_val = right.value
                res_val: Optional[float] = None
                if node.op == "+":
                    res_val = l_val + r_val
                elif node.op == "-":
                    res_val = l_val - r_val
                elif node.op == "*":
                    res_val = l_val * r_val
                elif node.op == "/":
                    if r_val != 0.0:
                        res_val = l_val / r_val

                if res_val is not None:
                    self.stats.constant_folds += 1
                    folded_val = round(res_val, 6)
                    self.stats.log(f"Folded Arithmetic: {l_val} {node.op} {r_val} -> {folded_val}")
                    return self._make_num_node(folded_val)

            # Algebraic identities: x * 1 -> x, x + 0 -> x, x - 0 -> x
            if node.op == "*" and isinstance(right, NumberLitNode) and math.isclose(right.value, 1.0):
                self.stats.constant_folds += 1
                self.stats.log("Folded Identity: x * 1.0 -> x")
                return left
            if node.op == "*" and isinstance(left, NumberLitNode) and math.isclose(left.value, 1.0):
                self.stats.constant_folds += 1
                self.stats.log("Folded Identity: 1.0 * x -> x")
                return right
            if node.op == "+" and isinstance(right, NumberLitNode) and math.isclose(right.value, 0.0):
                self.stats.constant_folds += 1
                self.stats.log("Folded Identity: x + 0.0 -> x")
                return left
            if node.op == "-" and isinstance(right, NumberLitNode) and math.isclose(right.value, 0.0):
                self.stats.constant_folds += 1
                self.stats.log("Folded Identity: x - 0.0 -> x")
                return left

            return BinOpExprNode(op=node.op, left=left, right=right)

        return node

    def _as_bool_const(self, node: ASTNode) -> Optional[bool]:
        if isinstance(node, NumberLitNode):
            return node.value != 0.0
        return None

    @staticmethod
    def _make_num_node(val: float) -> NumberLitNode:
        raw_str = str(int(val)) if val.is_integer() else str(val)
        return NumberLitNode(value=val, raw=raw_str)


# ---------------------------------------------------------------------------
# TAC Intermediate Representation Optimizer
# ---------------------------------------------------------------------------

class TACOptimizer:
    """
    Performs multi-pass optimization over Three-Address Code Quadruples.
    Implements:
      - Pass 1: Constant Folding & Local Propagation
      - Pass 2: Common Subexpression Elimination (CSE via Value Numbering)
      - Pass 3: Dead Code Elimination (DCE) for unreferenced temporaries
      - Pass 4: Redundant Jump and Label Optimization
    """

    COMMUTATIVE_OPS = {"+", "*", "==", "AND", "OR"}

    def __init__(self, stats: OptimizationStats) -> None:
        self.stats = stats

    def optimize_program(self, ir_prog: IRProgram) -> IRProgram:
        cloned_strategies: List[IRStrategy] = []
        total_initial = sum(len(s.all_quads) for s in ir_prog.strategies)
        self.stats.initial_quad_count = total_initial

        for strat in ir_prog.strategies:
            opt_strat = self.optimize_strategy(strat)
            cloned_strategies.append(opt_strat)

        total_opt = sum(len(s.all_quads) for s in cloned_strategies)
        self.stats.optimized_quad_count = total_opt
        return IRProgram(strategies=cloned_strategies)

    def optimize_strategy(self, strat: IRStrategy) -> IRStrategy:
        quads = [copy.deepcopy(q) for q in strat.all_quads]

        # Iterate multiple optimization passes until convergence or max iterations
        max_passes = 4
        for _ in range(max_passes):
            prev_len = len(quads)
            quads = self._pass_constant_folding_and_propagation(quads)
            quads = self._pass_common_subexpression_elimination(quads)
            quads = self._pass_dead_code_elimination(quads)
            quads = self._pass_redundant_jumps(quads)
            if len(quads) == prev_len:
                break

        # Partition back into indicator and rule quads
        ind_quads: List[Quad] = []
        rule_quads: List[Quad] = []
        is_rule_section = False
        for q in quads:
            if q.op.startswith("; RULE_START") or (q.op == "ACTION"):
                is_rule_section = True
            if is_rule_section:
                rule_quads.append(q)
            else:
                ind_quads.append(q)

        return IRStrategy(
            name=strat.name,
            indicator_quads=ind_quads,
            rule_quads=rule_quads,
        )

    # ------------------------------------------------------------------
    # Pass 1: Constant Folding & Propagation
    # ------------------------------------------------------------------

    def _pass_constant_folding_and_propagation(self, quads: List[Quad]) -> List[Quad]:
        new_quads: List[Quad] = []
        constants: Dict[str, float] = {}

        for q in quads:
            arg1 = q.arg1
            arg2 = q.arg2

            if arg1 in constants:
                arg1 = self._format_num(constants[arg1])
                self.stats.constant_propagations += 1
            if arg2 in constants:
                arg2 = self._format_num(constants[arg2])
                self.stats.constant_propagations += 1

            folded = False

            if q.op in ("+", "-", "*", "/") and self._is_num(arg1) and self._is_num(arg2):
                v1 = float(arg1)
                v2 = float(arg2)
                res: Optional[float] = None
                if q.op == "+":
                    res = v1 + v2
                elif q.op == "-":
                    res = v1 - v2
                elif q.op == "*":
                    res = v1 * v2
                elif q.op == "/" and v2 != 0.0:
                    res = v1 / v2

                if res is not None:
                    res_val = round(res, 6)
                    self.stats.constant_folds += 1
                    self.stats.log(f"TAC Constant Fold: {q.result} = {v1} {q.op} {v2} -> {res_val}")
                    new_quads.append(Quad(op="ASSIGN", arg1=self._format_num(res_val), result=q.result))
                    if q.result:
                        constants[q.result] = res_val
                    folded = True

            elif q.op in (">", "<", ">=", "<=", "==") and self._is_num(arg1) and self._is_num(arg2):
                v1 = float(arg1)
                v2 = float(arg2)
                cmp_res: bool
                if q.op == ">":
                    cmp_res = v1 > v2
                elif q.op == "<":
                    cmp_res = v1 < v2
                elif q.op == ">=":
                    cmp_res = v1 >= v2
                elif q.op == "<=":
                    cmp_res = v1 <= v2
                elif q.op == "==":
                    cmp_res = math.isclose(v1, v2, rel_tol=1e-5)
                else:
                    cmp_res = False

                self.stats.constant_folds += 1
                bool_val = 1.0 if cmp_res else 0.0
                self.stats.log(f"TAC Comparison Fold: {q.result} = {v1} {q.op} {v2} -> {bool_val}")
                new_quads.append(Quad(op="ASSIGN", arg1=self._format_num(bool_val), result=q.result))
                if q.result:
                    constants[q.result] = bool_val
                folded = True

            elif q.op == "ASSIGN":
                if self._is_num(arg1) and q.result:
                    constants[q.result] = float(arg1)
                elif q.result in constants:
                    del constants[q.result]
                new_quads.append(Quad(op=q.op, arg1=arg1, arg2=arg2, result=q.result))
                folded = True

            if not folded:
                new_quads.append(Quad(op=q.op, arg1=arg1, arg2=arg2, result=q.result))

        return new_quads

    # ------------------------------------------------------------------
    # Pass 2: Common Subexpression Elimination (CSE)
    # ------------------------------------------------------------------

    def _pass_common_subexpression_elimination(self, quads: List[Quad]) -> List[Quad]:
        new_quads: List[Quad] = []
        expr_to_temp: Dict[str, str] = {}
        alias_map: Dict[str, str] = {}

        for q in quads:
            arg1 = alias_map.get(q.arg1, q.arg1) if q.arg1 else q.arg1
            arg2 = alias_map.get(q.arg2, q.arg2) if q.arg2 else q.arg2

            is_pure_expr = q.op in ("+", "-", "*", "/", ">", "<", ">=", "<=", "==", "AND", "OR", "CALL_IND")

            if is_pure_expr and q.result:
                if q.op in self.COMMUTATIVE_OPS and arg1 and arg2 and arg1 > arg2:
                    k_arg1, k_arg2 = arg2, arg1
                else:
                    k_arg1, k_arg2 = arg1, arg2

                key = f"{q.op}:{k_arg1}:{k_arg2}"

                if key in expr_to_temp:
                    prev_temp = expr_to_temp[key]
                    self.stats.cse_eliminations += 1
                    self.stats.log(f"CSE Deduplicated: {q.result} replaces redundant {q.op} with {prev_temp}")
                    new_quads.append(Quad(op="ASSIGN", arg1=prev_temp, result=q.result))
                    alias_map[q.result] = prev_temp
                    continue
                else:
                    expr_to_temp[key] = q.result

            # Pure expressions of indicators, constants, and price fields
            # remain immutable and valid across all basic blocks in the strategy.

            new_quads.append(Quad(op=q.op, arg1=arg1, arg2=arg2, result=q.result))

        return new_quads

    # ------------------------------------------------------------------
    # Pass 3: Dead Code Elimination (DCE)
    # ------------------------------------------------------------------

    def _pass_dead_code_elimination(self, quads: List[Quad]) -> List[Quad]:
        used_symbols: Set[str] = set()
        for q in quads:
            if q.arg1:
                used_symbols.add(q.arg1)
            if q.arg2:
                for sub in q.arg2.split(","):
                    used_symbols.add(sub.strip())

        new_quads: List[Quad] = []
        for q in quads:
            is_temp = q.result and q.result.startswith("t") and q.result[1:].isdigit()
            is_pure = q.op in ("ASSIGN", "+", "-", "*", "/", ">", "<", ">=", "<=", "==", "AND", "OR")

            if is_temp and is_pure and q.result not in used_symbols:
                self.stats.dead_code_eliminations += 1
                self.stats.log(f"Dead Code Pruned: unused temporary {q.result}")
                continue

            new_quads.append(q)

        return new_quads

    # ------------------------------------------------------------------
    # Pass 4: Redundant Jump and Label Optimization
    # ------------------------------------------------------------------

    def _pass_redundant_jumps(self, quads: List[Quad]) -> List[Quad]:
        result_quads: List[Quad] = []
        i = 0
        n = len(quads)

        while i < n:
            q = quads[i]

            if q.op in ("GOTO", "IF_FALSE") and i + 1 < n:
                next_q = quads[i + 1]
                if next_q.op == "LABEL" and next_q.result == q.result:
                    self.stats.redundant_jumps_eliminated += 1
                    self.stats.log(f"Fall-through jump eliminated: {q.op} to {q.result}")
                    i += 1
                    continue

            if q.op == "IF_FALSE" and self._is_num(q.arg1):
                val = float(q.arg1)
                if val != 0.0:
                    self.stats.redundant_jumps_eliminated += 1
                    self.stats.log(f"Dead branch eliminated: IF_FALSE {q.arg1} never branches")
                    i += 1
                    continue

            result_quads.append(q)
            i += 1

        jump_targets: Set[str] = set()
        for q in result_quads:
            if q.op in ("GOTO", "IF_TRUE", "IF_FALSE") and q.result:
                jump_targets.add(q.result)

        cleaned_quads: List[Quad] = []
        for q in result_quads:
            if q.op == "LABEL" and q.result not in jump_targets:
                self.stats.redundant_jumps_eliminated += 1
                self.stats.log(f"Unreferenced label pruned: {q.result}")
                continue
            cleaned_quads.append(q)

        return cleaned_quads

    @staticmethod
    def _is_num(val: Optional[str]) -> bool:
        if not val:
            return False
        try:
            float(val)
            return True
        except ValueError:
            return False

    @staticmethod
    def _format_num(val: float) -> str:
        if val.is_integer():
            return str(int(val))
        return str(round(val, 6))


# ---------------------------------------------------------------------------
# Main Public Interface
# ---------------------------------------------------------------------------

class Optimizer:
    """
    Unified SwayaLang Code Optimizer.
    Coordinates AST-level and TAC-level optimization passes.
    """

    def __init__(self) -> None:
        self.stats = OptimizationStats()

    def optimize(self, program: ProgramNode, ir_prog: Optional[IRProgram] = None) -> Tuple[ProgramNode, Optional[IRProgram], OptimizationStats]:
        """
        Run complete two-tier optimization:
          1. AST Constant Folding
          2. TAC Constant Propagation, CSE, DCE, and Branch Optimization
        """
        self.stats = OptimizationStats()

        # Step 1: AST Optimization
        ast_folder = ASTConstantFolder(self.stats)
        opt_ast = ast_folder.fold_program(program)

        # Step 2: TAC IR Optimization (if provided)
        opt_ir: Optional[IRProgram] = None
        if ir_prog is not None:
            tac_opt = TACOptimizer(self.stats)
            opt_ir = tac_opt.optimize_program(ir_prog)

        return opt_ast, opt_ir, self.stats

    def optimize_ast(self, program: ProgramNode) -> Tuple[ProgramNode, OptimizationStats]:
        self.stats = OptimizationStats()
        folder = ASTConstantFolder(self.stats)
        opt_ast = folder.fold_program(program)
        return opt_ast, self.stats

    def optimize_ir(self, ir_prog: IRProgram) -> Tuple[IRProgram, OptimizationStats]:
        self.stats = OptimizationStats()
        tac_opt = TACOptimizer(self.stats)
        opt_ir = tac_opt.optimize_program(ir_prog)
        return opt_ir, self.stats
