"""
tests/test_lexer.py — Unit Tests for SwayaLang Lexer
===================================================
Covers tokenization of keywords, identifiers, literals, operators,
delimiters, comments, position tracking, and error handling.
"""

import pytest
from compiler.lexer import Lexer, LexError, Token, TokenType


def test_keywords_and_identifiers():
    source = "STRATEGY INDICATOR ENTRY EXIT STOP_LOSS TAKE_PROFIT BUY SELL SHORT ALL SHARES OF IF AND OR my_var_123"
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    expected_types = [
        TokenType.STRATEGY,
        TokenType.INDICATOR,
        TokenType.ENTRY,
        TokenType.EXIT,
        TokenType.STOP_LOSS,
        TokenType.TAKE_PROFIT,
        TokenType.BUY,
        TokenType.SELL,
        TokenType.SHORT,
        TokenType.ALL,
        TokenType.SHARES,
        TokenType.OF,
        TokenType.IF,
        TokenType.AND,
        TokenType.OR,
        TokenType.IDENT,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected_types
    assert tokens[-2].value == "my_var_123"


def test_price_fields_and_builtins():
    source = "CLOSE OPEN HIGH LOW VOLUME PRICE ENTRY_PRICE SMA EMA RSI"
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    expected_types = [
        TokenType.CLOSE,
        TokenType.OPEN,
        TokenType.HIGH,
        TokenType.LOW,
        TokenType.VOLUME,
        TokenType.PRICE,
        TokenType.ENTRY_PRICE,
        TokenType.SMA,
        TokenType.EMA,
        TokenType.RSI,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected_types


def test_numbers_integers_and_floats():
    source = "100 0.95 42 3.14159"
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    assert len(tokens) == 5
    assert tokens[0].type == TokenType.NUMBER_LIT and tokens[0].value == "100"
    assert tokens[1].type == TokenType.NUMBER_LIT and tokens[1].value == "0.95"
    assert tokens[2].type == TokenType.NUMBER_LIT and tokens[2].value == "42"
    assert tokens[3].type == TokenType.NUMBER_LIT and tokens[3].value == "3.14159"
    assert tokens[4].type == TokenType.EOF


def test_string_literal():
    source = '"GoldenCross" "AAPL"'
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    assert len(tokens) == 3
    assert tokens[0].type == TokenType.STRING_LIT and tokens[0].value == "GoldenCross"
    assert tokens[1].type == TokenType.STRING_LIT and tokens[1].value == "AAPL"
    assert tokens[2].type == TokenType.EOF


def test_operators_and_delimiters():
    source = "> < >= <= == = + - * / { } ( ) , :"
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    expected = [
        (TokenType.GT, ">"),
        (TokenType.LT, "<"),
        (TokenType.GTE, ">="),
        (TokenType.LTE, "<="),
        (TokenType.EQEQ, "=="),
        (TokenType.EQ, "="),
        (TokenType.PLUS, "+"),
        (TokenType.MINUS, "-"),
        (TokenType.STAR, "*"),
        (TokenType.SLASH, "/"),
        (TokenType.LBRACE, "{"),
        (TokenType.RBRACE, "}"),
        (TokenType.LPAREN, "("),
        (TokenType.RPAREN, ")"),
        (TokenType.COMMA, ","),
        (TokenType.COLON, ":"),
        (TokenType.EOF, ""),
    ]
    assert [(t.type, t.value) for t in tokens] == expected


def test_comments_and_whitespace():
    source = """
    # This is a comment
    STRATEGY "Test" { # inline comment
        # Another line
    }
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    types = [t.type for t in tokens]
    assert types == [
        TokenType.STRATEGY,
        TokenType.STRING_LIT,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.EOF,
    ]


def test_line_and_col_tracking():
    source = "STRATEGY\n  \"Golden\"\n    123"
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.STRATEGY
    assert tokens[0].line == 1 and tokens[0].col == 1

    assert tokens[1].type == TokenType.STRING_LIT
    assert tokens[1].line == 2 and tokens[1].col == 3

    assert tokens[2].type == TokenType.NUMBER_LIT
    assert tokens[2].line == 3 and tokens[2].col == 5


def test_unknown_character_raises_lexerror():
    source = "STRATEGY @foo"
    lexer = Lexer(source)
    with pytest.raises(LexError) as excinfo:
        lexer.tokenize()
    assert excinfo.value.line == 1
    assert excinfo.value.col == 10
    assert "Unexpected character: '@'" in str(excinfo.value)


def test_unterminated_string_raises_lexerror():
    source = 'STRATEGY "Unterminated'
    lexer = Lexer(source)
    with pytest.raises(LexError) as excinfo:
        lexer.tokenize()
    assert excinfo.value.line == 1
    assert excinfo.value.col == 10
    assert "Unterminated string literal" in str(excinfo.value)


def test_unterminated_string_newline_raises_lexerror():
    source = 'STRATEGY "Newline\n"'
    lexer = Lexer(source)
    with pytest.raises(LexError) as excinfo:
        lexer.tokenize()
    assert excinfo.value.line == 1
    assert excinfo.value.col == 10


def test_goldencross_sample_snippet():
    snippet = """STRATEGY "GoldenCross" { 
  INDICATOR sma_50 = SMA(CLOSE, 50) 
  INDICATOR sma_200 = SMA(CLOSE, 200) 
  INDICATOR rsi_14 = RSI(CLOSE, 14) 
  
  ENTRY: BUY 100 SHARES OF "AAPL" IF sma_50 > sma_200 AND rsi_14 < 30 
  EXIT: SELL ALL IF sma_50 < sma_200 
  STOP_LOSS: SELL ALL IF PRICE < ENTRY_PRICE * 0.95 
}"""
    lexer = Lexer(snippet)
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.STRATEGY
    assert tokens[1].type == TokenType.STRING_LIT and tokens[1].value == "GoldenCross"
    assert tokens[2].type == TokenType.LBRACE

    # Check that EOF is last
    assert tokens[-1].type == TokenType.EOF

    # Check key tokens appear
    token_types = {t.type for t in tokens}
    assert TokenType.INDICATOR in token_types
    assert TokenType.SMA in token_types
    assert TokenType.RSI in token_types
    assert TokenType.ENTRY in token_types
    assert TokenType.EXIT in token_types
    assert TokenType.STOP_LOSS in token_types
    assert TokenType.BUY in token_types
    assert TokenType.SHARES in token_types
    assert TokenType.OF in token_types
    assert TokenType.IF in token_types
    assert TokenType.AND in token_types
    assert TokenType.GT in token_types
    assert TokenType.LT in token_types
    assert TokenType.STAR in token_types
    assert TokenType.PRICE in token_types
    assert TokenType.ENTRY_PRICE in token_types
