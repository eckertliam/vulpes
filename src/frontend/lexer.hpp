#pragma once

#include "token.hpp"

#include <string>

namespace vulpes::frontend {

    class Lexer {
      public:
        Lexer(std::string source)
            : source(std::move(source)), start(0), current(0), line(1), column(1) {}

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
        void skip_whitespace();
        std::string_view current_lexeme() const;

        Token make_token(TokenKind kind);

        Token identifier();
        Token number();
        Token string();

        TokenKind keyword_kind(std::string_view lexeme);
    };

} // namespace vulpes::frontend