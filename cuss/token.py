from enum import Enum, auto
from typing import Optional
import location

class TokenType(Enum):
    # simple textual tokens
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"
    COMMA = ","
    DOT = "."
    COLON = ":"
    # arithmetic operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    MOD = "%"
    PLUS_EQ = "+="
    MINUS_EQ = "-="
    STAR_EQ = "*="
    SLASH_EQ = "/="
    MOD_EQ = "%="
    # comparison operators
    EQ_EQ = "=="
    NEQ = "!="
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    # logical operators
    LOGICAL_AND = "&&"
    LOGICAL_OR = "||"
    LOGICAL_NOT = "!"
    # bitwise operators
    BITWISE_AND = "&"
    BITWISE_OR = "|"
    # assignment operators
    EQ = "="
    # keywords
    IF = "if"
    ELSE = "else"
    LOOP = "loop"
    WHILE = "while"
    FOR = "for"
    IN = "in"
    RETURN = "return"
    BREAK = "break"
    CONTINUE = "continue"
    TRUE = "true"
    FALSE = "false"
    FN = "fn"
    CONST = "const"
    VAR = "var"
    TYPE = "type"
    STRUCT = "struct"
    ENUM = "enum"
    # literals
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    CHAR = "char"
    IDENT = "ident"
    # special tokens
    EOF = "eof"
    ERROR = "error"
    INDENT = "indent"
    DEDENT = "dedent"
    NEWLINE = "newline"
    

class Token:
    def __init__(self, type: TokenType, loc: location.Location, lexeme: Optional[str] = None) -> None:
        self.type = type
        self.lexeme = lexeme
        self.loc = loc
        
        
class SimpleToken(Token):
    def __init__(self, type: TokenType, lexeme: str, location: location.Location) -> None:
        super().__init__(type, lexeme, location)
        