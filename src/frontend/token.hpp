#pragma once

#include <string>
#include <string_view>

namespace vulpes::frontend
{

    enum class TokenKind
    {
        // Literals
        Identifier,
        Number,
        String,

        // Keywords
        Let,
        Fn,
        If,
        Else,
        While,
        Loop,
        Return,
        True,
        False,

        // Punctuation
        LParen,
        RParen,
        LBrace,
        RBrace,
        LBracket,
        RBracket,
        Comma,
        Dot,
        Colon,
        Semicolon,

        // Operators
        Plus,
        Minus,
        Star,
        Slash,
        Percent,
        Eq,
        EqEq,
        Bang,
        BangEq,
        Less,
        LessEq,
        Greater,
        GreaterEq,
        AmpAmp,
        BarBar,

        // Special
        Error,
        Eof,
    };

    struct Token
    {
        TokenKind kind;
        std::string_view lexeme;
        size_t line;
        size_t column;

        Token(TokenKind kind, std::string_view lexeme, size_t line, size_t column)
            : kind(kind), lexeme(lexeme), line(line), column(column) {}

        Token(TokenKind kind, size_t line, size_t column)
            : kind(kind), lexeme(""), line(line), column(column) {}
    };

    const char *token_kind_to_string(TokenKind kind);

} // namespace vulpes::frontend