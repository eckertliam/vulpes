from cuss.token import SimpleToken, Token, TokenType
from cuss.location import Location
from collections import deque

class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.start = 0
        self.current = 0
        self.loc = Location(1, 1)
        self.line = 1
        self.column = 1
        self.tokens = []
        self.indent_stack = deque()
        self.indent_stack.append(0)
        
    def peek(self) -> str:
        if self.current < len(self.source):
            return self.source[self.current]
        return "\0"
    
    def advance(self) -> str:
        c = self.peek()
        self.current += 1
        if c == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return c
        
    def get_lexeme(self) -> str:
        return self.source[self.start:self.current]
    
    def simple_token(self, type: TokenType) -> None:
        self.tokens.append(SimpleToken(type, self.loc))
        
    def token(self, type: TokenType) -> None:
        lexeme = self.get_lexeme()
        self.tokens.append(Token(type, self.loc, lexeme))
        
    def simple_branch(self, c: str, then: TokenType, else_: TokenType) -> None:
        if c == self.peek():
            self.advance()
            self.simple_token(then)
        else:
            self.simple_token(else_)
            
    def handle_newline(self) -> None:
        self.simple_token(TokenType.NEWLINE)
        self.start = self.current
        self.loc = Location(self.line, self.column)
        last_indent = self.indent_stack[-1]
        # compare to the current indent
        current_indent = 0
        while self.peek() == " ":
            current_indent += 1
        if current_indent < last_indent:
            # if the current indent is less than the last indent, we need to dedent 
            # and pop the last indent from the stack
            self.simple_token(TokenType.DEDENT)
            self.indent_stack.pop()
        elif current_indent > last_indent:
            # if the current indent is greater than the last indent, we need to indent
            # and push the current indent onto the stack
            self.indent_stack.append(current_indent)
            self.simple_token(TokenType.INDENT)
        
    def next_token(self) -> None:
        self.start = self.current
        self.loc = Location(self.line, self.column)
        c = self.advance()
        
        match c:
            case "(":
                self.simple_token(TokenType.LEFT_PAREN)
            case ")":
                self.simple_token(TokenType.RIGHT_PAREN)
            case "{":
                self.simple_token(TokenType.LEFT_BRACE)
            case "}":
                self.simple_token(TokenType.RIGHT_BRACE)
            case "[":
                self.simple_token(TokenType.LEFT_BRACKET)
            case "]":
                self.simple_token(TokenType.RIGHT_BRACKET)
            case ",":
                self.simple_token(TokenType.COMMA)
            case ".":
                self.simple_token(TokenType.DOT)
            case ":":
                self.simple_token(TokenType.COLON)
            case "+":
                self.simple_branch("=", TokenType.PLUS_EQ, TokenType.PLUS)
            case "-":
                self.simple_branch("=", TokenType.MINUS_EQ, TokenType.MINUS)
            case "*":
                self.simple_branch("=", TokenType.STAR_EQ, TokenType.STAR)
            case "/":
                self.simple_branch("=", TokenType.SLASH_EQ, TokenType.SLASH)
            case "%":
                self.simple_branch("=", TokenType.MOD_EQ, TokenType.MOD)
            case "=":
                self.simple_branch("=", TokenType.EQ_EQ, TokenType.EQ)
            case "!":
                self.simple_branch("=", TokenType.NEQ, TokenType.LOGICAL_NOT)
            case "<":
                self.simple_branch("=", TokenType.LTE, TokenType.LT)
            case ">":
                self.simple_branch("=", TokenType.GTE, TokenType.GT)
            case "&":
                self.simple_branch("&", TokenType.LOGICAL_AND, TokenType.BITWISE_AND)
            case "|":
                self.simple_branch("|", TokenType.LOGICAL_OR, TokenType.BITWISE_OR)
            case "\n":
                self.handle_newline()
            case " ":
                # ignore whitespaces occurring in the middle of a line
                pass
            case "\"":
                # TODO: handle strings
                pass
            case "'":
                # TODO: handle characters
                pass
            case "\0":
                self.simple_token(TokenType.EOF)
            case _:
                if c.isdigit():
                    # TODO: handle numbers
                    pass
                elif c.isalpha() or c == "_":
                    # TODO: handle identifiers
                    pass
                else:
                    error_token = Token(TokenType.ERROR, self.loc, f"Unexpected character: {c}")
                    self.tokens.append(error_token)
