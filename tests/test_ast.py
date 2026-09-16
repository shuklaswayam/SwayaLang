"""
tests/test_ast.py — Unit Tests & Snapshot Tests for SwayaLang AST Pretty-Printer
================================================================================
Tests:
- pretty_print(indent=0) on all AST node types
- GoldenCross strategy AST snapshot test locking in exact 2-space indented output
- ProgramNode and StrategyNode tree formatting
- caps-sys capture for stdout printing
"""

import io
import pytest
from compiler.ast_nodes import (
    ActionNode,
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
from compiler.lexer import Lexer
from compiler.parser import Parser


def test_goldencross_ast_pretty_print_snapshot():
    """
    Acceptance criterion: pretty_print on GoldenCross AST produces human-readable
    tree with StrategyNode at root; snapshot test locks in exact indented output;
    no external deps used.
    """
    snippet = """STRATEGY "GoldenCross" { 
  INDICATOR sma_50 = SMA(CLOSE, 50) 
  INDICATOR sma_200 = SMA(CLOSE, 200) 
  INDICATOR rsi_14 = RSI(CLOSE, 14) 
  
  ENTRY: BUY 100 SHARES OF "AAPL" IF sma_50 > sma_200 AND rsi_14 < 30 
  EXIT: SELL ALL IF sma_50 < sma_200 
  STOP_LOSS: SELL ALL IF PRICE < ENTRY_PRICE * 0.95 
}"""
    tokens = Lexer(snippet).tokenize()
    prog = Parser(tokens).parse()
    strat = prog.strategies[0]

    expected_snapshot = (
        "Strategy(name='GoldenCross')\n"
        "  indicators:\n"
        "    IndicatorDecl(name='sma_50')\n"
        "      FuncCall(name='SMA')\n"
        "        Ident(CLOSE)\n"
        "        NumberLit(50)\n"
        "    IndicatorDecl(name='sma_200')\n"
        "      FuncCall(name='SMA')\n"
        "        Ident(CLOSE)\n"
        "        NumberLit(200)\n"
        "    IndicatorDecl(name='rsi_14')\n"
        "      FuncCall(name='RSI')\n"
        "        Ident(CLOSE)\n"
        "        NumberLit(14)\n"
        "  rules:\n"
        "    RuleBlock(kind='ENTRY')\n"
        "      action:\n"
        "        Action(action='BUY', qty=100.0, ticker='AAPL')\n"
        "      condition:\n"
        "        BoolOp(op='AND')\n"
        "          Comparison(op='>')\n"
        "            Ident(sma_50)\n"
        "            Ident(sma_200)\n"
        "          Comparison(op='<')\n"
        "            Ident(rsi_14)\n"
        "            NumberLit(30)\n"
        "    RuleBlock(kind='EXIT')\n"
        "      action:\n"
        "        Action(action='SELL', qty=ALL)\n"
        "      condition:\n"
        "        Comparison(op='<')\n"
        "          Ident(sma_50)\n"
        "          Ident(sma_200)\n"
        "    RuleBlock(kind='STOP_LOSS')\n"
        "      action:\n"
        "        Action(action='SELL', qty=ALL)\n"
        "      condition:\n"
        "        Comparison(op='<')\n"
        "          Ident(PRICE)\n"
        "          BinOpExpr(op='*')\n"
        "            Ident(ENTRY_PRICE)\n"
        "            NumberLit(0.95)\n"
    )

    actual = strat.to_str()
    assert actual == expected_snapshot


def test_program_node_pretty_print():
    prog = ProgramNode(
        strategies=[
            StrategyNode(
                name="Minimal",
                indicators=[],
                rules=[
                    RuleBlockNode(
                        kind="ENTRY",
                        action=ActionNode(action="BUY", quantity=10.0, all_flag=False, ticker=None),
                        condition=ComparisonNode(
                            op=">",
                            left=IdentNode("PRICE"),
                            right=NumberLitNode(100.0, "100"),
                        ),
                    )
                ],
            )
        ]
    )

    expected = (
        "Program (strategies=1)\n"
        "  Strategy(name='Minimal')\n"
        "    rules:\n"
        "      RuleBlock(kind='ENTRY')\n"
        "        action:\n"
        "          Action(action='BUY', qty=10.0)\n"
        "        condition:\n"
        "          Comparison(op='>')\n"
        "            Ident(PRICE)\n"
        "            NumberLit(100)\n"
    )

    assert prog.to_str() == expected


def test_stdout_capsys_pretty_print(capsys):
    node = NumberLitNode(42.0, "42")
    node.pretty_print()
    captured = capsys.readouterr()
    assert captured.out == "NumberLit(42)\n"


def test_binop_expression_pretty_print():
    node = BinOpExprNode(
        op="+",
        left=IdentNode("OPEN"),
        right=BinOpExprNode(
            op="*",
            left=NumberLitNode(2.0, "2"),
            right=IdentNode("CLOSE"),
        ),
    )
    expected = (
        "BinOpExpr(op='+')\n"
        "  Ident(OPEN)\n"
        "  BinOpExpr(op='*')\n"
        "    NumberLit(2)\n"
        "    Ident(CLOSE)\n"
    )
    assert node.to_str() == expected
