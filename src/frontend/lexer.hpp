#pragma once

#include "token.hpp"

#include <string_view>

namespace vulpes::frontend {

class Lexer {
 public:
  Lexer(std::string_view source);

  Token next_token();

 private:
  Token make_token(TokenKind type);
  Token error_token(const char* message);
  bool is_at_end();
  char advance();
  bool match(char expected);
  void skip_whitespace();
  char peek();
  char peek_next();
  Token string();
  Token character();
  Token number();
  Token identifier();

  std::string_view m_source;
  uint32_t m_start = 0;
  uint32_t m_current = 0;
  uint32_t m_line = 1;
  uint32_t m_column = 1;
};

}  // namespace vulpes::frontend
