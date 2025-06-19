#pragma once

#include "token.hpp"

#include <string>

class Lexer {
public:
    Lexer(std::string source);

    Token next_token();

private:
    std::string source;
    size_t start;
    size_t current;
    size_t line;
    size_t column;

    bool is_at_end() const;
    char advance();
    char peek() const;
    char peek_next() const;
    bool match(char expected);
    void skip_whitespace_and_comments();
    std::string_view current_lexeme() const;

    Token make_token(TokenKind kind);

    Token identifier();
    Token number();
    Token string();

    TokenKind keyword_kind(std::string_view lexeme);
};