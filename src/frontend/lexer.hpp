#pragma once

#include "token.hpp"

#include <string_view>

namespace vulpes::frontend {

class Lexer {
 public:
  explicit Lexer(const std::string_view source) : m_source(source) {}

  Token next_token();

 private:
  [[nodiscard]] Token make_token(TokenKind type) const;
  Token error_token(const char* message) const;
  [[nodiscard]] bool is_at_end() const;
  char advance();
  bool match(char expected);
  void skip_whitespace();
  [[nodiscard]] char peek() const;
  [[nodiscard]] char peek_next() const;
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
