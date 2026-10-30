"""
tests/test_ir.py — Unit Tests for SwayaLang Intermediate Code Generator (TAC)
=============================================================================
Phase 2 test suite for BCSE307P Compiler Design Laboratory.
"""

from compiler.ir import IRGenerator, Quad
from compiler.lexer import Lexer
from compiler.parser import Parser


def parse_source(source: str):
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def test_quadruple_formatting():
    """Verify various Quad opcodes format into standard Three-Address Code."""
    q_assign = Quad(op="ASSIGN", arg1="100", result="t0")
    assert str(q_assign).strip() == "t0 = 100"

    q_bin = Quad(op="+", arg1="t0", arg2="t1", result="t2")
    assert str(q_bin).strip() == "t2 = t0 + t1"

    q_cmp = Quad(op=">", arg1="sma_50", arg2="sma_200", result="t3")
    assert str(q_cmp).strip() == "t3 = sma_50 > sma_200"

    q_call = Quad(op="CALL_IND", arg1="SMA", arg2="CLOSE, 50", result="t4")
    assert str(q_call).strip() == "t4 = CALL SMA(CLOSE, 50)"

    q_label = Quad(op="LABEL", result="L0")
    assert str(q_label).strip() == "L0:"

    q_branch = Quad(op="IF_FALSE", arg1="t3", result="L1")
    assert str(q_branch).strip() == "if not t3 goto L1"


def test_ir_generation_golden_cross():
    """Verify TAC generation for canonical golden_cross strategy."""
    src = """
    STRATEGY "GoldenCross" {
        INDICATOR sma_50 = SMA(CLOSE, 50)
        INDICATOR sma_200 = SMA(CLOSE, 200)

        ENTRY: BUY 100 SHARES OF "AAPL" IF sma_50 > sma_200
        EXIT:  SELL ALL                  IF sma_50 < sma_200
    }
    """
    ast = parse_source(src)
    ir_gen = IRGenerator()
    ir_prog = ir_gen.generate(ast)

    assert len(ir_prog.strategies) == 1
    strat = ir_prog.strategies[0]
    assert strat.name == "GoldenCross"

    # Indicators lowered
    ind_ops = [q.op for q in strat.indicator_quads]
    assert "CALL_IND" in ind_ops
    assert "ASSIGN" in ind_ops

    # Rules lowered
    rule_ops = [q.op for q in strat.rule_quads]
    assert ">" in rule_ops
    assert "<" in rule_ops
    assert "IF_FALSE" in rule_ops
    assert "ACTION" in rule_ops
    assert "LABEL" in rule_ops

    dump_text = ir_prog.dump()
    assert "; --- STRATEGY: GoldenCross ---" in dump_text
    assert "ACTION [ENTRY] BUY 100.0 SHARES OF 'AAPL'" in dump_text
    assert "ACTION [EXIT] SELL ALL" in dump_text


def test_ir_generation_boolean_logic():
    """Verify TAC generation for AND and OR compound conditions."""
    src = """
    STRATEGY "BoolLogic" {
        INDICATOR rsi = RSI(CLOSE, 14)
        ENTRY: BUY 50 SHARES OF "AAPL" IF rsi < 30 OR rsi > 70
    }
    """
    ast = parse_source(src)
    ir_gen = IRGenerator()
    ir_prog = ir_gen.generate(ast)

    strat = ir_prog.strategies[0]
    rule_ops = [q.op for q in strat.rule_quads]
    assert "<" in rule_ops
    assert ">" in rule_ops
    assert "OR" in rule_ops


def test_ir_generation_multiple_strategies():
    """Verify IR generator handles multi-strategy programs."""
    src = """
    STRATEGY "A" {
        ENTRY: BUY 10 SHARES OF "AAPL" IF CLOSE > 100
    }
    STRATEGY "B" {
        ENTRY: BUY 20 SHARES OF "TSLA" IF CLOSE > 200
    }
    """
    ast = parse_source(src)
    ir_gen = IRGenerator()
    ir_prog = ir_gen.generate(ast)

    assert len(ir_prog.strategies) == 2
    assert ir_prog.strategies[0].name == "A"
    assert ir_prog.strategies[1].name == "B"
