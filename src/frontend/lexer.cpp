#include "lexer.hpp"

namespace vulpes::frontend
{
    bool Lexer::is_at_end() const
    {
        return current >= source.length();
    }

    char Lexer::advance()
    {
        char c = source[current];
        if (c == '\n')
        {
            line++;
            column = 1;
        }
        else if (c == '\t')
        {
            column += 4;
        }
        else
        {
            column++;
        }
        current++;
        return c;
    }

    char Lexer::peek() const
    {
        return source[current];
    }

    char Lexer::peek_next() const
    {
        return source[current + 1];
    }

    bool Lexer::match(char expected)
    {
        if (is_at_end())
            return false;
        if (source[current] != expected)
            return false;
        current++;
        return true;
    }

    void Lexer::skip_whitespace()
    {
        while (!is_at_end())
        {
            char c = peek();
            if (c == ' ' || c == '\r' || c == '\t' || c == '\n')
            {
                advance();
            }
            else
            {
                break;
            }
        }
    }

    std::string_view Lexer::current_lexeme() const
    {
        return std::string_view(source).substr(start, current - start);
    }

    Token Lexer::make_token(TokenKind kind)
    {
        return Token(kind, current_lexeme(), line, column);
    }
} // namespace vulpes::frontend
