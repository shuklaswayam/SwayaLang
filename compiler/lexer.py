"""
compiler/lexer.py — SwayaLang Lexer
====================================
Phase 1 deliverable for BCSE307P Compiler Design Laboratory.

Responsibility:
    Convert raw SwayaLang source text (.strat files) into a typed, position-
    annotated token stream consumed by the parser.

Token types produced:
    Literals   : STRING_LIT, NUMBER_LIT
    Identifiers: IDENT
    Keywords   : STRATEGY, INDICATOR, ENTRY, EXIT, STOP_LOSS, TAKE_PROFIT,
                 BUY, SELL, SHORT, ALL, SHARES, OF, IF, AND, OR,
                 CLOSE, OPEN, HIGH, LOW, VOLUME, PRICE, ENTRY_PRICE,
                 SMA, EMA, RSI
    Operators  : GT, LT, GTE, LTE, EQEQ, PLUS, MINUS, STAR, SLASH, EQ
    Delimiters : LBRACE, RBRACE, LPAREN, RPAREN, COMMA, COLON
    Control    : EOF

Error handling:
    Raises LexError(message, line, col) on:
      - Unknown character
      - Unterminated string literal

Usage:
    from compiler.lexer import Lexer, LexError
    lexer  = Lexer(source_text)
    tokens = lexer.tokenize()   # → list[Token]
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List


# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------

class TokenType(Enum):
    # Literals
    STRING_LIT  = auto()
    NUMBER_LIT  = auto()

    # Identifiers
    IDENT       = auto()

    # --- Keywords ---
    STRATEGY    = auto()
    INDICATOR   = auto()
    ENTRY       = auto()
    EXIT        = auto()
    STOP_LOSS   = auto()
    TAKE_PROFIT = auto()
    BUY         = auto()
    SELL        = auto()
    SHORT       = auto()
    ALL         = auto()
    SHARES      = auto()
    OF          = auto()
    IF          = auto()
    AND         = auto()
    OR          = auto()

    # --- Price fields ---
    CLOSE       = auto()
    OPEN        = auto()
    HIGH        = auto()
    LOW         = auto()
    VOLUME      = auto()
    PRICE       = auto()
    ENTRY_PRICE = auto()

    # --- Built-in indicator functions ---
    SMA         = auto()
    EMA         = auto()
    RSI         = auto()

    # --- Operators ---
    GT    = auto()   # >
    LT    = auto()   # <
    GTE   = auto()   # >=
    LTE   = auto()   # <=
    EQEQ  = auto()   # ==
    EQ    = auto()   # =  (assignment in INDICATOR decl)
    PLUS  = auto()   # +
    MINUS = auto()   # -
    STAR  = auto()   # *
    SLASH = auto()   # /

    # --- Delimiters ---
    LBRACE  = auto()  # {
    RBRACE  = auto()  # }
    LPAREN  = auto()  # (
    RPAREN  = auto()  # )
    COMMA   = auto()  # ,
    COLON   = auto()  # :

    # --- Control ---
    EOF = auto()


# Map keyword strings → TokenType (case-sensitive; keywords are UPPER)
_KEYWORDS: dict[str, TokenType] = {
    "STRATEGY":    TokenType.STRATEGY,
    "INDICATOR":   TokenType.INDICATOR,
    "ENTRY":       TokenType.ENTRY,
    "EXIT":        TokenType.EXIT,
    "STOP_LOSS":   TokenType.STOP_LOSS,
    "TAKE_PROFIT": TokenType.TAKE_PROFIT,
    "BUY":         TokenType.BUY,
    "SELL":        TokenType.SELL,
    "SHORT":       TokenType.SHORT,
    "ALL":         TokenType.ALL,
    "SHARES":      TokenType.SHARES,
    "OF":          TokenType.OF,
    "IF":          TokenType.IF,
    "AND":         TokenType.AND,
    "OR":          TokenType.OR,
    "CLOSE":       TokenType.CLOSE,
    "OPEN":        TokenType.OPEN,
    "HIGH":        TokenType.HIGH,
    "LOW":         TokenType.LOW,
    "VOLUME":      TokenType.VOLUME,
    "PRICE":       TokenType.PRICE,
    "ENTRY_PRICE": TokenType.ENTRY_PRICE,
    "SMA":         TokenType.SMA,
    "EMA":         TokenType.EMA,
    "RSI":         TokenType.RSI,
}


# ---------------------------------------------------------------------------
# Token dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Token:
    """A single lexical token with its type, raw value, and source position."""

    type:   TokenType
    value:  str
    line:   int   # 1-based
    col:    int   # 1-based, column of first character

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.col})"


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------

class LexError(Exception):
    """Raised by the Lexer on unrecognised input or malformed literals."""

    def __init__(self, message: str, line: int, col: int) -> None:
        super().__init__(f"LexError at line {line}, col {col}: {message}")
        self.line = line
        self.col  = col


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

class Lexer:
    """
    Hand-written, single-pass lexer for SwayaLang.

    Attributes:
        source (str): The full source text to tokenize.

    Example::

        lexer  = Lexer(source_text)
        tokens = lexer.tokenize()
        for tok in tokens:
            print(tok)
    """

    def __init__(self, source: str) -> None:
        self.source: str  = source
        self._pos:   int  = 0      # current character index
        self._line:  int  = 1      # current line number (1-based)
        self._col:   int  = 1      # current column number (1-based)
        self._tokens: List[Token] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def tokenize(self) -> List[Token]:
        """
        Scan the entire source and return the complete token list.

        The final element is always ``Token(TokenType.EOF, '', ...)``.

        Raises:
            LexError: on unknown character or unterminated string literal.
        """
        self._tokens = []
        while not self._at_end():
            self._skip_whitespace_and_comments()
            if self._at_end():
                break
            self._scan_token()
        self._tokens.append(Token(TokenType.EOF, "", self._line, self._col))
        return self._tokens

    # ------------------------------------------------------------------
    # Internal scanning helpers  (to be implemented in Phase 1)
    # ------------------------------------------------------------------

    def _scan_token(self) -> None:
        """
        Scan a single token starting at the current position and append it
        to ``self._tokens``.
        """
        start_line = self._line
        start_col  = self._col
        ch = self._peek()

        if ch.isdigit():
            self._scan_number()
            return

        if ch == '"':
            self._scan_string()
            return

        if ch.isalpha() or ch == "_":
            self._scan_identifier_or_keyword()
            return

        # Advance past the operator / delimiter character
        self._advance()

        if ch == ">":
            if self._match("="):
                self._add_token(TokenType.GTE, ">=", start_line, start_col)
            else:
                self._add_token(TokenType.GT, ">", start_line, start_col)
        elif ch == "<":
            if self._match("="):
                self._add_token(TokenType.LTE, "<=", start_line, start_col)
            else:
                self._add_token(TokenType.LT, "<", start_line, start_col)
        elif ch == "=":
            if self._match("="):
                self._add_token(TokenType.EQEQ, "==", start_line, start_col)
            else:
                self._add_token(TokenType.EQ, "=", start_line, start_col)
        elif ch == "+":
            self._add_token(TokenType.PLUS, "+", start_line, start_col)
        elif ch == "-":
            self._add_token(TokenType.MINUS, "-", start_line, start_col)
        elif ch == "*":
            self._add_token(TokenType.STAR, "*", start_line, start_col)
        elif ch == "/":
            self._add_token(TokenType.SLASH, "/", start_line, start_col)
        elif ch == "{":
            self._add_token(TokenType.LBRACE, "{", start_line, start_col)
        elif ch == "}":
            self._add_token(TokenType.RBRACE, "}", start_line, start_col)
        elif ch == "(":
            self._add_token(TokenType.LPAREN, "(", start_line, start_col)
        elif ch == ")":
            self._add_token(TokenType.RPAREN, ")", start_line, start_col)
        elif ch == ",":
            self._add_token(TokenType.COMMA, ",", start_line, start_col)
        elif ch == ":":
            self._add_token(TokenType.COLON, ":", start_line, start_col)
        else:
            raise LexError(f"Unexpected character: {ch!r}", start_line, start_col)

    def _scan_number(self) -> None:
        """Consume a NUMBER_LIT token (integer or decimal).

        Grammar: DIGIT { DIGIT } [ '.' { DIGIT } ]
        """
        start_line = self._line
        start_col  = self._col
        start_pos  = self._pos

        while not self._at_end() and self._peek().isdigit():
            self._advance()

        if not self._at_end() and self._peek() == "." and self._peek_next().isdigit():
            # Consume '.'
            self._advance()
            while not self._at_end() and self._peek().isdigit():
                self._advance()

        raw = self.source[start_pos:self._pos]
        self._add_token(TokenType.NUMBER_LIT, raw, start_line, start_col)

    def _scan_string(self) -> None:
        """Consume a STRING_LIT token delimited by double quotes.

        Raises LexError if EOF is reached before the closing quote.
        """
        start_line = self._line
        start_col  = self._col

        # Advance past opening quote
        self._advance()

        chars: list[str] = []
        while not self._at_end() and self._peek() != '"':
            if self._peek() == "\n":
                raise LexError("Unterminated string literal (newline before closing quote)", start_line, start_col)
            chars.append(self._advance())

        if self._at_end():
            raise LexError("Unterminated string literal", start_line, start_col)

        # Consume closing quote
        self._advance()
        content = "".join(chars)
        self._add_token(TokenType.STRING_LIT, content, start_line, start_col)

    def _scan_identifier_or_keyword(self) -> None:
        """Consume an IDENT or keyword token.

        Scans LETTER (LETTER | DIGIT | '_')*, then checks _KEYWORDS for
        a match.
        """
        start_line = self._line
        start_col  = self._col
        start_pos  = self._pos

        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()

        word = self.source[start_pos:self._pos]
        ttype = _KEYWORDS.get(word, TokenType.IDENT)
        self._add_token(ttype, word, start_line, start_col)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _peek(self) -> str:
        """Return current character without advancing, or '' at EOF."""
        return self.source[self._pos] if not self._at_end() else ""

    def _peek_next(self) -> str:
        """Return the character one ahead of current, or '' near EOF."""
        return self.source[self._pos + 1] if self._pos + 1 < len(self.source) else ""

    def _advance(self) -> str:
        """Consume and return the current character, updating line/col."""
        ch = self.source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col   = 1
        else:
            self._col += 1
        return ch

    def _match(self, expected: str) -> bool:
        """Consume the next character if it equals *expected*."""
        if self._at_end() or self.source[self._pos] != expected:
            return False
        self._advance()
        return True

    def _at_end(self) -> bool:
        return self._pos >= len(self.source)

    def _add_token(self, ttype: TokenType, value: str, line: int, col: int) -> None:
        self._tokens.append(Token(ttype, value, line, col))

    def _skip_whitespace_and_comments(self) -> None:
        """Skip spaces, tabs, newlines, and '#'-to-end-of-line comments."""
        while not self._at_end():
            ch = self._peek()
            if ch in (" ", "\t", "\r", "\n"):
                self._advance()
            elif ch == "#":
                # Line comment — consume until newline
                while not self._at_end() and self._peek() != "\n":
                    self._advance()
            else:
                break
