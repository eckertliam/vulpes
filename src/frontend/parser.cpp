#include "parser.hpp"

namespace vulpes::frontend {

Parser::Parser(Lexer& lexer) : m_lexer(lexer) {
  m_current = m_lexer.next_token();
  m_previous = m_current;
}

std::vector<std::unique_ptr<Stmt>> Parser::parse() {
  std::vector<std::unique_ptr<Stmt>> statements;
  while (!is_at_end()) {
    statements.push_back(declaration());
  }
  return statements;
}

std::unique_ptr<Stmt> Parser::declaration() {
  if (match({TokenKind::Let})) {
    return let_declaration();
  }
  if (match({TokenKind::Const})) {
    return const_declaration();
  }

  if (match({TokenKind::Fn})) {
    return function_declaration();
  }

  // TODO: implement class parsing

  // TODO: Add error handling and synchronization
  return statement();
}

std::unique_ptr<Stmt> Parser::let_declaration() {
  Token name = consume(TokenKind::Identifier, "Expect variable name.");
  std::unique_ptr<Expr> initializer = nullptr;
  if (match({TokenKind::Eq})) {
    initializer = expression();
  }
  consume(TokenKind::Semicolon, "Expect ';' after variable declaration.");
  return std::make_unique<LetStmt>(name, std::move(initializer));
}

std::unique_ptr<Stmt> Parser::const_declaration() {
  Token name = consume(TokenKind::Identifier, "Expect constant name.");
  consume(TokenKind::Eq, "Expect '=' after constant name.");
  auto initializer = expression();
  consume(TokenKind::Semicolon, "Expect ';' after constant value.");
  return std::make_unique<ConstStmt>(name, std::move(initializer));
}

std::unique_ptr<BlockStmt> Parser::block_statement() {
  std::vector<std::unique_ptr<Stmt>> statements;
  while (!check(TokenKind::RBrace) && !is_at_end()) {
    statements.push_back(declaration());
  }
  return std::make_unique<BlockStmt>(std::move(statements));
}

std::unique_ptr<Stmt> Parser::function_declaration() {
  Token name = consume(TokenKind::Identifier, "Expect a valid function name");
  consume(TokenKind::LParen, "Expect '(' after function name");
  auto parameters = std::vector<std::string_view>();
  while (!check(TokenKind::RParen) && !is_at_end()) {
    auto param =
        consume(TokenKind::Identifier, "Expect a valid parameter name");
    parameters.push_back(param.lexeme());
    if (match({TokenKind::Comma})) {
      continue;
    }
    break;
  }
  consume(TokenKind::RParen, "Expect ')' after function arguments");

  if (match({TokenKind::Colon})) {
    // TODO: Implement more rigorous ret ty parsing
    Token return_type = consume(TokenKind::Type, "Expect a valid return type");
  }

  consume(TokenKind::LBrace, "Expect '{' before function body");
  auto body = block_statement();
  consume(TokenKind::RBrace, "Expect '}' after function body");
  return std::make_unique<FunctionStmt>(name, parameters, std::move(body));
}

std::unique_ptr<Stmt> Parser::return_statement() {
  Token keyword = previous();
  std::unique_ptr<Expr> value = nullptr;
  if (!check(TokenKind::Semicolon)) {
    value = expression();
  }
  consume(TokenKind::Semicolon, "Expect ';' after return statement.");
  return std::make_unique<ReturnStmt>(keyword, std::move(value));
}

std::unique_ptr<Stmt> Parser::statement() {
  if (match({TokenKind::Return})) {
    return return_statement();
  }

  // TODO: implement handling for all statement types

  return expression_statement();
}

std::unique_ptr<Stmt> Parser::expression_statement() {
  auto expr = expression();
  consume(TokenKind::Semicolon, "Expect ';' after expression.");
  return std::make_unique<ExpressionStmt>(std::move(expr));
}

std::unique_ptr<Expr> Parser::expression() {
  return assignment();
}

std::unique_ptr<Expr> Parser::assignment() {
  auto expr = logical_or();

  if (match({TokenKind::Eq})) {
    auto value = assignment();

    if (const auto var_expr = dynamic_cast<VarExpr*>(expr.get())) {
      return std::make_unique<AssignExpr>(var_expr, std::move(value));
    }

    // TODO: Error, invalid assignment target
  }

  return expr;
}

std::unique_ptr<Expr> Parser::logical_or() {
  auto expr = logical_and();

  while (match({TokenKind::BarBar})) {
    Token op = previous();
    auto right = logical_and();
    expr = std::make_unique<LogicalExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
}

std::unique_ptr<Expr> Parser::logical_and() {
  auto expr = equality();

  while (match({TokenKind::AmpAmp})) {
    Token op = previous();
    auto right = equality();
    expr = std::make_unique<LogicalExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
}

std::unique_ptr<Expr> Parser::equality() {
  auto expr = comparison();

  while (match({TokenKind::BangEq, TokenKind::EqEq})) {
    Token op = previous();
    auto right = comparison();
    expr = std::make_unique<BinaryExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
}

std::unique_ptr<Expr> Parser::comparison() {
  auto expr = term();

  while (match({TokenKind::Greater, TokenKind::GreaterEq, TokenKind::Less,
                TokenKind::LessEq})) {
    Token op = previous();
    auto right = term();
    expr = std::make_unique<BinaryExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
}

std::unique_ptr<Expr> Parser::term() {
  auto expr = factor();

  while (match({TokenKind::Minus, TokenKind::Plus})) {
    Token op = previous();
    auto right = factor();
    expr = std::make_unique<BinaryExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
}

std::unique_ptr<Expr> Parser::factor() {
  auto expr = unary();

  while (match({TokenKind::Slash, TokenKind::Star})) {
    Token op = previous();
    auto right = unary();
    expr = std::make_unique<BinaryExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
}

std::unique_ptr<Expr> Parser::unary() {
  if (match({TokenKind::Bang, TokenKind::Minus})) {
    Token op = previous();
    auto right = unary();
    return std::make_unique<UnaryExpr>(op, std::move(right));
  }

  return call();
}

std::unique_ptr<Expr> Parser::call() {
  auto expr = primary();

  while (true) {
    if (match({TokenKind::LParen})) {
      std::vector<std::unique_ptr<Expr>> arguments;
      if (!check(TokenKind::RParen)) {
        do {
          arguments.push_back(expression());
        } while (match({TokenKind::Comma}));
      }
      Token paren = consume(TokenKind::RParen, "Expect ')' after arguments.");
      expr = std::make_unique<CallExpr>(std::move(expr), paren,
                                        std::move(arguments));
    } else {
      break;
    }
  }

  return expr;
}

std::unique_ptr<Expr> Parser::primary() {
  if (match({TokenKind::Integer}))
    return std::make_unique<IntegerLiteral>(previous());
  if (match({TokenKind::Float}))
    return std::make_unique<FloatLiteral>(previous());
  if (match({TokenKind::String}))
    return std::make_unique<StringLiteral>(previous());
  if (match({TokenKind::Char}))
    return std::make_unique<CharLiteral>(previous());
  if (match({TokenKind::True, TokenKind::False}))
    return std::make_unique<BoolLiteral>(previous());
  if (match({TokenKind::Null}))
    return std::make_unique<NullLiteral>(previous());

  if (match({TokenKind::Identifier})) {
    return std::make_unique<VarExpr>(previous());
  }

  if (match({TokenKind::LParen})) {
    auto expr = expression();
    consume(TokenKind::RParen, "Expect ')' after expression.");
    return std::make_unique<GroupingExpr>(std::move(expr));
  }

  // TODO: Error handling
  return nullptr;
}

bool Parser::match(const std::vector<TokenKind>& types) {
  for (const auto type : types) {
    if (check(type)) {
      advance();
      return true;
    }
  }
  return false;
}

Token Parser::consume(const TokenKind type, const char* message) {
  if (check(type)) {
    return advance();
  }

  // TODO: Error handling
  // throw error(peek(), message);
  return advance();  // Should not be reached
}

bool Parser::check(const TokenKind type) const {
  if (is_at_end()) {
    return false;
  }
  return peek().kind == type;
}

Token Parser::advance() {
  if (!is_at_end()) {
    m_previous = m_current;
    m_current = m_lexer.next_token();
  }
  return previous();
}

bool Parser::is_at_end() const {
  return m_current.kind == TokenKind::Eof;
}

Token Parser::peek() const {
  return m_current;
}

Token Parser::previous() const {
  return m_previous;
}

}  // namespace vulpes::frontend
