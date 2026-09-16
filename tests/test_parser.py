"""
tests/test_parser.py — Unit Tests for SwayaLang Recursive-Descent Parser
========================================================================
Tests parser functionality:
- Hand-crafted token streams directly fed to Parser (isolation testing)
- Parsing single ENTRY rule with binary condition
- Parsing full GoldenCross strategy AST
- Error handling (missing IF keyword, missing delimiters, line/col reporting)
"""

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
from compiler.lexer import Lexer, Token, TokenType
from compiler.parser import Parser, ParseError


def test_hand_crafted_token_stream_without_lexer():
    """
    Module boundary test (§9): Feed hand-crafted tokens directly to the Parser
    without invoking Lexer. Verifies complete isolation of parser unit tests.
    """
    tokens = [
        Token(TokenType.STRATEGY, "STRATEGY", 1, 1),
        Token(TokenType.STRING_LIT, "MinimalStrategy", 1, 10),
        Token(TokenType.LBRACE, "{", 1, 28),
        # ENTRY: BUY 100 SHARES OF "AAPL" IF sma_50 > 200
        Token(TokenType.ENTRY, "ENTRY", 2, 3),
        Token(TokenType.COLON, ":", 2, 8),
        Token(TokenType.BUY, "BUY", 2, 10),
        Token(TokenType.NUMBER_LIT, "100", 2, 14),
        Token(TokenType.SHARES, "SHARES", 2, 18),
        Token(TokenType.OF, "OF", 2, 25),
        Token(TokenType.STRING_LIT, "AAPL", 2, 28),
        Token(TokenType.IF, "IF", 2, 35),
        Token(TokenType.IDENT, "sma_50", 2, 38),
        Token(TokenType.GT, ">", 2, 45),
        Token(TokenType.NUMBER_LIT, "200", 2, 47),
        Token(TokenType.RBRACE, "}", 3, 1),
        Token(TokenType.EOF, "", 3, 2),
    ]

    parser = Parser(tokens)
    prog = parser.parse()

    assert isinstance(prog, ProgramNode)
    assert len(prog.strategies) == 1

    strat = prog.strategies[0]
    assert strat.name == "MinimalStrategy"
    assert len(strat.indicators) == 0
    assert len(strat.rules) == 1

    rule = strat.rules[0]
    assert rule.kind == "ENTRY"
    assert isinstance(rule.action, ActionNode)
    assert rule.action.action == "BUY"
    assert rule.action.quantity == 100.0
    assert rule.action.ticker == "AAPL"

    assert isinstance(rule.condition, ComparisonNode)
    assert rule.condition.op == ">"
    assert isinstance(rule.condition.left, IdentNode)
    assert rule.condition.left.name == "sma_50"
    assert isinstance(rule.condition.right, NumberLitNode)
    assert rule.condition.right.value == 200.0


def test_missing_if_keyword_raises_parse_error_with_pos():
    """
    Acceptance criterion: ParseError raised with line+col on missing IF keyword.
    """
    tokens = [
        Token(TokenType.STRATEGY, "STRATEGY", 1, 1),
        Token(TokenType.STRING_LIT, "BadRule", 1, 10),
        Token(TokenType.LBRACE, "{", 1, 20),
        Token(TokenType.ENTRY, "ENTRY", 2, 3),
        Token(TokenType.COLON, ":", 2, 8),
        Token(TokenType.BUY, "BUY", 2, 10),
        Token(TokenType.ALL, "ALL", 2, 14),
        # Missing IF keyword! Next token is IDENT instead of IF
        Token(TokenType.IDENT, "sma_50", 2, 18),
        Token(TokenType.GT, ">", 2, 25),
        Token(TokenType.NUMBER_LIT, "100", 2, 27),
        Token(TokenType.RBRACE, "}", 3, 1),
        Token(TokenType.EOF, "", 3, 2),
    ]

    parser = Parser(tokens)
    with pytest.raises(ParseError) as excinfo:
        parser.parse()

    err = excinfo.value
    assert err.line == 2
    assert err.col == 18
    assert "expected 'IF'" in str(err)


def test_goldencross_sample_ast():
    """
    Acceptance criterion: parser builds correct AST for GoldenCross sample.
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
    parser = Parser(tokens)
    prog = parser.parse()

    assert len(prog.strategies) == 1
    strat = prog.strategies[0]
    assert strat.name == "GoldenCross"

    # Verify 3 indicators
    assert len(strat.indicators) == 3
    assert strat.indicators[0].name == "sma_50"
    assert strat.indicators[0].func_call.name == "SMA"
    assert len(strat.indicators[0].func_call.args) == 2
    assert isinstance(strat.indicators[0].func_call.args[0], IdentNode)
    assert strat.indicators[0].func_call.args[0].name == "CLOSE"
    assert isinstance(strat.indicators[0].func_call.args[1], NumberLitNode)
    assert strat.indicators[0].func_call.args[1].value == 50.0

    assert strat.indicators[1].name == "sma_200"
    assert strat.indicators[2].name == "rsi_14"

    # Verify 3 rules
    assert len(strat.rules) == 3

    # Rule 1: ENTRY
    entry = strat.rules[0]
    assert entry.kind == "ENTRY"
    assert entry.action.action == "BUY"
    assert entry.action.quantity == 100.0
    assert entry.action.ticker == "AAPL"
    assert isinstance(entry.condition, BoolOpNode)
    assert entry.condition.op == "AND"
    assert isinstance(entry.condition.left, ComparisonNode)
    assert entry.condition.left.op == ">"
    assert isinstance(entry.condition.right, ComparisonNode)
    assert entry.condition.right.op == "<"

    # Rule 2: EXIT
    exit_rule = strat.rules[1]
    assert exit_rule.kind == "EXIT"
    assert exit_rule.action.action == "SELL"
    assert exit_rule.action.all_flag is True
    assert isinstance(exit_rule.condition, ComparisonNode)
    assert exit_rule.condition.op == "<"

    # Rule 3: STOP_LOSS
    stop_loss = strat.rules[2]
    assert stop_loss.kind == "STOP_LOSS"
    assert stop_loss.action.action == "SELL"
    assert stop_loss.action.all_flag is True
    assert isinstance(stop_loss.condition, ComparisonNode)
    assert stop_loss.condition.op == "<"
    assert isinstance(stop_loss.condition.right, BinOpExprNode)
    assert stop_loss.condition.right.op == "*"
    assert isinstance(stop_loss.condition.right.left, IdentNode)
    assert stop_loss.condition.right.left.name == "ENTRY_PRICE"
    assert isinstance(stop_loss.condition.right.right, NumberLitNode)
    assert stop_loss.condition.right.right.value == 0.95


def test_missing_strategy_keyword():
    tokens = [
        Token(TokenType.IDENT, "foo", 1, 1),
        Token(TokenType.EOF, "", 1, 4),
    ]
    with pytest.raises(ParseError) as excinfo:
        Parser(tokens).parse()
    assert "expected 'STRATEGY' keyword" in str(excinfo.value)


def test_missing_strategy_body_rules():
    tokens = [
        Token(TokenType.STRATEGY, "STRATEGY", 1, 1),
        Token(TokenType.STRING_LIT, "Empty", 1, 10),
        Token(TokenType.LBRACE, "{", 1, 18),
        Token(TokenType.RBRACE, "}", 1, 19),
        Token(TokenType.EOF, "", 1, 20),
    ]
    with pytest.raises(ParseError) as excinfo:
        Parser(tokens).parse()
    assert "expected at least one rule block" in str(excinfo.value)


def test_parenthesized_condition():
    snippet = """STRATEGY "Paren" {
      ENTRY: BUY ALL IF (sma_50 > sma_200) AND rsi_14 < 30
    }"""
    tokens = Lexer(snippet).tokenize()
    prog = Parser(tokens).parse()
    rule = prog.strategies[0].rules[0]
    assert isinstance(rule.condition, BoolOpNode)
    assert rule.condition.op == "AND"
    assert isinstance(rule.condition.left, ComparisonNode)
