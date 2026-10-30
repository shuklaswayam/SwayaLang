"""
tests/test_optimizer.py — Unit Tests for SwayaLang Optimizer (Phase 3)
=======================================================================
Phase 3 deliverable for BCSE307P Compiler Design Laboratory.

Tests:
    - AST Constant Folding (arithmetic expressions, identities, boolean laws, comparisons)
    - TAC Constant Folding & Propagation (literal folding in quadruples)
    - Common Subexpression Elimination (CSE via value numbering for arithmetic & indicators)
    - Dead Code Elimination (pruning unused temporaries)
    - Redundant Jump Elimination (fall-through branches and static condition pruning)
    - OptimizationStats tracking & reduction percentage
    - Optimization preserves semantic equivalence of strategy logic
"""

from __future__ import annotations

import pytest

from compiler.ast_nodes import (
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
from compiler.ir import IRGenerator, IRProgram, Quad
from compiler.lexer import Lexer
from compiler.optimizer import (
    ASTConstantFolder,
    OptimizationStats,
    Optimizer,
    TACOptimizer,
)
from compiler.parser import Parser


def test_ast_constant_folding_arithmetic():
    """Verify that arithmetic constants like (100 * 0.95) and (10 - 8) fold to constants."""
    # (100 * 0.95) + (10 - 8) -> 95.0 + 2.0 -> 97.0
    sub_expr = BinOpExprNode(
        op="+",
        left=BinOpExprNode(
            op="*",
            left=NumberLitNode(value=100.0, raw="100"),
            right=NumberLitNode(value=0.95, raw="0.95"),
        ),
        right=BinOpExprNode(
            op="-",
            left=NumberLitNode(value=10.0, raw="10"),
            right=NumberLitNode(value=8.0, raw="8"),
        ),
    )
    stats = OptimizationStats()
    folder = ASTConstantFolder(stats)
    folded = folder.fold_expr(sub_expr)

    assert isinstance(folded, NumberLitNode)
    assert folded.value == 97.0
    assert stats.constant_folds == 3


def test_ast_constant_folding_algebraic_identities():
    """Verify algebraic identities: x * 1.0 -> x, x + 0.0 -> x, x - 0.0 -> x."""
    x_ident = IdentNode(name="PRICE")
    expr_mul = BinOpExprNode(op="*", left=x_ident, right=NumberLitNode(value=1.0, raw="1.0"))
    expr_add = BinOpExprNode(op="+", left=x_ident, right=NumberLitNode(value=0.0, raw="0.0"))
    expr_sub = BinOpExprNode(op="-", left=x_ident, right=NumberLitNode(value=0.0, raw="0.0"))

    stats = OptimizationStats()
    folder = ASTConstantFolder(stats)

    assert folder.fold_expr(expr_mul) == x_ident
    assert folder.fold_expr(expr_add) == x_ident
    assert folder.fold_expr(expr_sub) == x_ident
    assert stats.constant_folds == 3


def test_ast_constant_folding_boolean_laws():
    """Verify boolean identities: True AND x -> x, False AND x -> False, True OR x -> True."""
    cond = ComparisonNode(op=">", left=IdentNode(name="sma_50"), right=IdentNode(name="sma_200"))
    true_node = NumberLitNode(value=1.0, raw="1")
    false_node = NumberLitNode(value=0.0, raw="0")

    stats = OptimizationStats()
    folder = ASTConstantFolder(stats)

    # True AND cond -> cond
    and_true = BoolOpNode(op="AND", left=true_node, right=cond)
    res1 = folder.fold_condition(and_true)
    assert res1 == cond

    # False AND cond -> False
    and_false = BoolOpNode(op="AND", left=false_node, right=cond)
    res2 = folder.fold_condition(and_false)
    assert isinstance(res2, NumberLitNode)
    assert res2.value == 0.0

    # True OR cond -> True
    or_true = BoolOpNode(op="OR", left=true_node, right=cond)
    res3 = folder.fold_condition(or_true)
    assert isinstance(res3, NumberLitNode)
    assert res3.value == 1.0


def test_tac_constant_folding_and_propagation():
    """Verify TAC optimizer folds constant quads and propagates literal values."""
    source = """
    STRATEGY "ConstFold" {
        INDICATOR sma_50 = SMA(CLOSE, 50)
        ENTRY: BUY 100 SHARES OF "AAPL" IF PRICE < (100 * 0.95)
    }
    """
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    ir_prog = IRGenerator().generate(ast)

    optimizer = Optimizer()
    opt_prog, stats = optimizer.optimize_ir(ir_prog)

    # Assert that (100 * 0.95) was folded and propagated
    assert stats.constant_folds >= 1
    dump = opt_prog.dump()
    assert "95" in dump
    assert stats.optimized_quad_count < stats.initial_quad_count


def test_common_subexpression_elimination_cse():
    """Verify CSE deduplicates repeated computations across multiple rules."""
    source = """
    STRATEGY "CSEDemo" {
        INDICATOR sma_50 = SMA(CLOSE, 50)
        INDICATOR sma_200 = SMA(CLOSE, 200)
        ENTRY: BUY 100 SHARES OF "AAPL" IF sma_50 > sma_200
        EXIT:  SELL ALL IF sma_50 > sma_200
    }
    """
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    ir_prog = IRGenerator().generate(ast)

    optimizer = Optimizer()
    opt_prog, stats = optimizer.optimize_ir(ir_prog)

    assert stats.cse_eliminations >= 1
    assert "replaces redundant" in " ".join(stats.transformation_log)


def test_dead_code_elimination():
    """Verify dead temporary registers that are never referenced get pruned."""
    strat_quads = [
        Quad(op="ASSIGN", arg1="100", result="t0"),      # dead temp
        Quad(op="ASSIGN", arg1="200", result="t1"),      # used temp
        Quad(op=">", arg1="t1", arg2="50", result="t2"), # used temp
        Quad(op="IF_FALSE", arg1="t2", result="L1"),
        Quad(op="ACTION", arg1="[ENTRY] BUY", arg2="ALL", result="AAPL"),
        Quad(op="LABEL", result="L1"),
    ]
    strat = IRProgram(strategies=[from_quads("DeadCodeTest", strat_quads)])

    stats = OptimizationStats()
    opt_prog = TACOptimizer(stats).optimize_program(strat)

    assert stats.dead_code_eliminations >= 1
    dump = opt_prog.dump()
    assert "t0 = 100" not in dump


def test_redundant_jump_elimination():
    """Verify fall-through jumps to immediately adjacent labels are removed."""
    strat_quads = [
        Quad(op="ASSIGN", arg1="CLOSE", result="t0"),
        Quad(op="GOTO", result="L1"),                     # redundant jump to adjacent L1
        Quad(op="LABEL", result="L1"),
        Quad(op="ACTION", arg1="[ENTRY] BUY", arg2="ALL", result="AAPL"),
    ]
    strat = IRProgram(strategies=[from_quads("JumpTest", strat_quads)])

    stats = OptimizationStats()
    opt_prog = TACOptimizer(stats).optimize_program(strat)

    assert stats.redundant_jumps_eliminated >= 1
    dump = opt_prog.dump()
    assert "goto L1" not in dump


def test_optimizer_end_to_end_stats_summary():
    """Verify Optimizer returns valid OptimizationStats with summary formatting."""
    source = """
    STRATEGY "GoldenCrossOpt" {
        INDICATOR sma_50  = SMA(CLOSE, 50)
        INDICATOR sma_200 = SMA(CLOSE, 200)
        INDICATOR rsi_14  = RSI(CLOSE, 14)

        ENTRY:     BUY 100 SHARES OF "AAPL" IF sma_50 > sma_200 AND rsi_14 < (10 + 20)
        EXIT:      SELL ALL                  IF sma_50 < sma_200
        STOP_LOSS: SELL ALL                  IF PRICE < ENTRY_PRICE * (1.0 - 0.05)
    }
    """
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    ir_prog = IRGenerator().generate(ast)

    optimizer = Optimizer()
    opt_ast, opt_ir, stats = optimizer.optimize(ast, ir_prog)

    assert stats.initial_quad_count > 0
    assert stats.optimized_quad_count <= stats.initial_quad_count
    assert stats.reduction_pct >= 0.0
    summary = stats.format_summary()
    assert "SWAYALANG COMPILER OPTIMIZATION AUDIT" in summary
    assert "Code Size Reduction:" in summary


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def from_quads(name: str, quads: list[Quad]):
    from compiler.ir import IRStrategy
    return IRStrategy(name=name, indicator_quads=[], rule_quads=quads)
