#include "lexer.hpp"
#include "token.hpp"

#include <unordered_map>

namespace vulpes::frontend {

static const std::unordered_map<std::string_view, TokenKind> keywords = {
    {"let", TokenKind::Let},
    {"const", TokenKind::Const},
    {"fn", TokenKind::Fn},
    {"return", TokenKind::Return},
    {"if", TokenKind::If},
    {"else", TokenKind::Else},
    {"while", TokenKind::While},
    {"for", TokenKind::For},
    {"in", TokenKind::In},
    {"break", TokenKind::Break},
    {"continue", TokenKind::Continue},
    {"struct", TokenKind::Struct},
    {"class", TokenKind::Class},
    {"enum", TokenKind::Enum},
    {"pub", TokenKind::Pub},
    {"from", TokenKind::From},
    {"import", TokenKind::Import},
    {"export", TokenKind::Export},
    {"true", TokenKind::True},
    {"false", TokenKind::False},
    {"null", TokenKind::Null},
    {"type", TokenKind::Type},
};

Lexer::Lexer(std::string_view source) : m_source(source) {}

Token Lexer::next_token() {
  skip_whitespace();

  m_start = m_current;

  if (is_at_end()) {
    return make_token(TokenKind::Eof);
  }

  char c = advance();

  if (std::isalpha(c) || c == '_') {
    return identifier();
  }

  if (std::isdigit(c)) {
    return number();
  }

  switch (c) {
    case '(':
      return make_token(TokenKind::LParen);
    case ')':
      return make_token(TokenKind::RParen);
    case '{':
      return make_token(TokenKind::LBrace);
    case '}':
      return make_token(TokenKind::RBrace);
    case '[':
      return make_token(TokenKind::LBracket);
    case ']':
      return make_token(TokenKind::RBracket);
    case ',':
      return make_token(TokenKind::Comma);
    case '.':
      return make_token(TokenKind::Dot);
    case ':':
      return make_token(TokenKind::Colon);
    case ';':
      return make_token(TokenKind::Semicolon);
    case '+':
      return make_token(TokenKind::Plus);
    case '-':
      return make_token(TokenKind::Minus);
    case '*':
      return make_token(TokenKind::Star);
    case '/':
      return make_token(TokenKind::Slash);
    case '%':
      return make_token(TokenKind::Percent);
    case '=':
      return make_token(match('=') ? TokenKind::EqEq : TokenKind::Eq);
    case '!':
      return make_token(match('=') ? TokenKind::BangEq : TokenKind::Bang);
    case '<':
      return make_token(match('=') ? TokenKind::LessEq : TokenKind::Less);
    case '>':
      return make_token(match('=') ? TokenKind::GreaterEq : TokenKind::Greater);
    case '&':
      if (match('&')) {
        return make_token(TokenKind::AmpAmp);
      }
      break;
    case '|':
      if (match('|')) {
        return make_token(TokenKind::BarBar);
      }
      break;
    case '"':
      return string();
    case '\'':
      return character();
  }

  return error_token("Unexpected character.");
}

Token Lexer::make_token(TokenKind type) {
  return Token(type, m_line, m_column - (m_current - m_start), m_line, m_column,
               m_source.substr(m_start, m_current - m_start));
}

Token Lexer::error_token(const char* message) {
  return Token(TokenKind::Error, m_line, m_column, m_line, m_column, message);
}

bool Lexer::is_at_end() {
  return m_current >= m_source.length();
}

char Lexer::advance() {
  m_current++;
  m_column++;
  return m_source[m_current - 1];
}

bool Lexer::match(char expected) {
  if (is_at_end()) {
    return false;
  }
  if (m_source[m_current] != expected) {
    return false;
  }
  m_current++;
  m_column++;
  return true;
}

void Lexer::skip_whitespace() {
  for (;;) {
    char c = peek();
    switch (c) {
      case ' ':
      case '\r':
      case '\t':
        advance();
        break;
      case '\n':
        m_line++;
        m_column = 1;
        advance();
        break;
      case '/':
        if (peek_next() == '/') {
          while (peek() != '\n' && !is_at_end()) {
            advance();
          }
        } else {
          return;
        }
        break;
      default:
        return;
    }
  }
}

char Lexer::peek() {
  if (is_at_end()) {
    return '\0';
  }
  return m_source[m_current];
}

char Lexer::peek_next() {
  if (m_current + 1 >= m_source.length()) {
    return '\0';
  }
  return m_source[m_current + 1];
}

Token Lexer::string() {
  while (peek() != '"' && !is_at_end()) {
    if (peek() == '\n') {
      m_line++;
      m_column = 1;
    }
    advance();
  }

  if (is_at_end()) {
    return error_token("Unterminated string.");
  }

  advance();
  return make_token(TokenKind::String);
}

Token Lexer::character() {
  if (peek() != '\'' && !is_at_end()) {
    advance();
  }

  if (is_at_end() || peek() != '\'') {
    return error_token("Unterminated character literal.");
  }

  advance();
  return make_token(TokenKind::Char);
}

Token Lexer::number() {
  while (std::isdigit(peek())) {
    advance();
  }

  if (peek() == '.' && std::isdigit(peek_next())) {
    advance();
    while (std::isdigit(peek())) {
      advance();
    }
    return make_token(TokenKind::Float);
  }

  return make_token(TokenKind::Integer);
}

Token Lexer::identifier() {
  while (std::isalnum(peek()) || peek() == '_') {
    advance();
  }

  auto text = m_source.substr(m_start, m_current - m_start);
  auto it = keywords.find(text);
  if (it != keywords.end()) {
    return make_token(it->second);
  }

  return make_token(TokenKind::Identifier);
}

}  // namespace vulpes::frontend
