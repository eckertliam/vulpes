#pragma once

#include "location.hpp"

#include <string_view>

namespace vulpes::frontend {

    enum class TokenKind {
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

    struct Token {
        TokenKind kind;
        Location location;

        Token(TokenKind kind, uint32_t start_line, uint32_t start_column, uint32_t end_line,
              uint32_t end_column, std::string_view lexeme)
            : kind(kind), location(start_line, start_column, end_line, end_column, lexeme) {}
    };

    const char* token_kind_to_string(TokenKind kind);

} // namespace vulpes::frontend