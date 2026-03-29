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

  if (match({TokenKind::Enum})) {
    return enum_declaration();
  }

  if (match({TokenKind::Struct})) {
    return struct_declaration();
  }

  if (match({TokenKind::Class})) {
    return class_declaration();
  }

  if (match({TokenKind::From})) {
    return import_statement();
  }

  if (match({TokenKind::Export})) {
    return export_statement();
  }

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
    // Optional type annotation on parameter
    if (match({TokenKind::Colon})) {
      // Consume the type name (ignored at runtime per spec)
      consume(TokenKind::Identifier, "Expect type annotation.");
    }
    if (match({TokenKind::Comma})) {
      continue;
    }
    break;
  }
  consume(TokenKind::RParen, "Expect ')' after function arguments");

  // Optional return type annotation
  if (match({TokenKind::Colon})) {
    consume(TokenKind::Identifier, "Expect a valid return type");
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

  if (match({TokenKind::LBrace})) {
    auto block = block_statement();
    consume(TokenKind::RBrace, "Expect '}' after block.");
    return block;
  }

  if (match({TokenKind::If})) {
    return if_statement();
  }

  if (match({TokenKind::While})) {
    return while_statement();
  }

  if (match({TokenKind::For})) {
    return for_statement();
  }

  if (match({TokenKind::Break})) {
    Token keyword = previous();
    consume(TokenKind::Semicolon, "Expect ';' after 'break'.");
    return std::make_unique<BreakStmt>(keyword);
  }

  if (match({TokenKind::Continue})) {
    Token keyword = previous();
    consume(TokenKind::Semicolon, "Expect ';' after 'continue'.");
    return std::make_unique<ContinueStmt>(keyword);
  }

  return expression_statement();
}

std::unique_ptr<Stmt> Parser::if_statement() {
  auto condition = expression();
  consume(TokenKind::LBrace, "Expect '{' after if condition.");
  auto then_branch = block_statement();
  consume(TokenKind::RBrace, "Expect '}' after if body.");

  std::unique_ptr<Stmt> else_branch = nullptr;
  if (match({TokenKind::Else})) {
    consume(TokenKind::LBrace, "Expect '{' after 'else'.");
    auto else_block = block_statement();
    consume(TokenKind::RBrace, "Expect '}' after else body.");
    else_branch = std::move(else_block);
  }

  return std::make_unique<IfStmt>(std::move(condition), std::move(then_branch), std::move(else_branch));
}

std::unique_ptr<Stmt> Parser::while_statement() {
  auto condition = expression();
  consume(TokenKind::LBrace, "Expect '{' after while condition.");
  auto body = block_statement();
  consume(TokenKind::RBrace, "Expect '}' after while body.");
  return std::make_unique<WhileStmt>(std::move(condition), std::move(body));
}

std::unique_ptr<Stmt> Parser::for_statement() {
  Token var = consume(TokenKind::Identifier, "Expect variable name after 'for'.");
  consume(TokenKind::In, "Expect 'in' after for variable.");
  auto iterable = expression();
  consume(TokenKind::LBrace, "Expect '{' after for iterable.");
  auto body = block_statement();
  consume(TokenKind::RBrace, "Expect '}' after for body.");
  return std::make_unique<ForStmt>(var, std::move(iterable), std::move(body));
}

std::unique_ptr<Stmt> Parser::enum_declaration() {
  Token name = consume(TokenKind::Identifier, "Expect enum name.");
  consume(TokenKind::LBrace, "Expect '{' after enum name.");
  std::vector<std::string_view> tags;
  while (!check(TokenKind::RBrace) && !is_at_end()) {
    Token tag = consume(TokenKind::Identifier, "Expect enum tag name.");
    tags.push_back(tag.lexeme());
    if (!match({TokenKind::Comma})) break;
  }
  consume(TokenKind::RBrace, "Expect '}' after enum tags.");
  consume(TokenKind::Semicolon, "Expect ';' after enum declaration.");
  return std::make_unique<EnumStmt>(name, std::move(tags));
}

std::unique_ptr<Stmt> Parser::struct_declaration() {
  Token name = consume(TokenKind::Identifier, "Expect struct name.");
  consume(TokenKind::LBrace, "Expect '{' after struct name.");
  std::vector<StructField> fields;
  while (!check(TokenKind::RBrace) && !is_at_end()) {
    Token field_name = consume(TokenKind::Identifier, "Expect field name.");
    consume(TokenKind::Colon, "Expect ':' after field name.");
    Token type_name = consume(TokenKind::Identifier, "Expect type annotation.");
    fields.push_back({field_name.lexeme(), type_name.lexeme()});
    if (!match({TokenKind::Comma})) break;
  }
  consume(TokenKind::RBrace, "Expect '}' after struct fields.");
  consume(TokenKind::Semicolon, "Expect ';' after struct declaration.");
  return std::make_unique<StructStmt>(name, std::move(fields));
}

std::unique_ptr<Stmt> Parser::class_declaration() {
  Token name = consume(TokenKind::Identifier, "Expect class name.");
  consume(TokenKind::LBrace, "Expect '{' after class name.");
  std::vector<ClassField> fields;
  std::vector<std::unique_ptr<FunctionStmt>> methods;
  while (!check(TokenKind::RBrace) && !is_at_end()) {
    if (match({TokenKind::Fn})) {
      auto method = function_declaration();
      methods.push_back(std::unique_ptr<FunctionStmt>(
          static_cast<FunctionStmt*>(method.release())));
    } else {
      bool is_pub = match({TokenKind::Pub});
      Token field_name = consume(TokenKind::Identifier, "Expect field or method name.");
      consume(TokenKind::Colon, "Expect ':' after field name.");
      Token type_name = consume(TokenKind::Identifier, "Expect type annotation.");
      consume(TokenKind::Semicolon, "Expect ';' after field declaration.");
      fields.push_back({is_pub, field_name.lexeme(), type_name.lexeme()});
    }
  }
  consume(TokenKind::RBrace, "Expect '}' after class body.");
  consume(TokenKind::Semicolon, "Expect ';' after class declaration.");
  return std::make_unique<ClassStmt>(name, std::move(fields), std::move(methods));
}

std::unique_ptr<Stmt> Parser::import_statement() {
  Token from_tok = previous();
  Token module = consume(TokenKind::Identifier, "Expect module path.");
  consume(TokenKind::Import, "Expect 'import' after module path.");
  consume(TokenKind::LBrace, "Expect '{' after 'import'.");
  std::vector<std::string_view> names;
  while (!check(TokenKind::RBrace) && !is_at_end()) {
    Token ident = consume(TokenKind::Identifier, "Expect import name.");
    names.push_back(ident.lexeme());
    if (!match({TokenKind::Comma})) break;
  }
  consume(TokenKind::RBrace, "Expect '}' after import names.");
  consume(TokenKind::Semicolon, "Expect ';' after import statement.");
  return std::make_unique<ImportStmt>(from_tok, module.lexeme(), std::move(names));
}

std::unique_ptr<Stmt> Parser::export_statement() {
  Token export_tok = previous();
  consume(TokenKind::LBrace, "Expect '{' after 'export'.");
  std::vector<std::string_view> names;
  while (!check(TokenKind::RBrace) && !is_at_end()) {
    Token ident = consume(TokenKind::Identifier, "Expect export name.");
    names.push_back(ident.lexeme());
    if (!match({TokenKind::Comma})) break;
  }
  consume(TokenKind::RBrace, "Expect '}' after export names.");
  consume(TokenKind::Semicolon, "Expect ';' after export statement.");
  return std::make_unique<ExportStmt>(export_tok, std::move(names));
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
  auto expr = bitwise_or();

  while (match({TokenKind::Greater, TokenKind::GreaterEq, TokenKind::Less,
                TokenKind::LessEq})) {
    Token op = previous();
    auto right = bitwise_or();
    expr = std::make_unique<BinaryExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
}

std::unique_ptr<Expr> Parser::bitwise_or() {
  auto expr = bitwise_xor();

  while (match({TokenKind::Bar})) {
    Token op = previous();
    auto right = bitwise_xor();
    expr = std::make_unique<BinaryExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
}

std::unique_ptr<Expr> Parser::bitwise_xor() {
  auto expr = bitwise_and();

  while (match({TokenKind::Caret})) {
    Token op = previous();
    auto right = bitwise_and();
    expr = std::make_unique<BinaryExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
}

std::unique_ptr<Expr> Parser::bitwise_and() {
  auto expr = shift();

  while (match({TokenKind::Amp})) {
    Token op = previous();
    auto right = shift();
    expr = std::make_unique<BinaryExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
}

std::unique_ptr<Expr> Parser::shift() {
  auto expr = term();

  while (match({TokenKind::LessLess, TokenKind::GreaterGreater})) {
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

  while (match({TokenKind::Slash, TokenKind::Star, TokenKind::Percent})) {
    Token op = previous();
    auto right = unary();
    expr = std::make_unique<BinaryExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
}

std::unique_ptr<Expr> Parser::unary() {
  if (match({TokenKind::Bang, TokenKind::Minus, TokenKind::Plus})) {
    Token op = previous();
    auto right = unary();
    return std::make_unique<UnaryExpr>(op, std::move(right));
  }

  return power();
}

std::unique_ptr<Expr> Parser::power() {
  auto expr = call();

  if (match({TokenKind::StarStar})) {
    Token op = previous();
    // Right-associative: recurse into power() not call()
    auto right = power();
    expr = std::make_unique<BinaryExpr>(std::move(expr), op, std::move(right));
  }

  return expr;
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
    } else if (match({TokenKind::Dot})) {
      Token name = consume(TokenKind::Identifier, "Expect property name after '.'.");
      if (match({TokenKind::Eq})) {
        auto value = expression();
        expr = std::make_unique<SetExpr>(std::move(expr), name, std::move(value));
      } else {
        expr = std::make_unique<GetExpr>(std::move(expr), name);
      }
    } else if (match({TokenKind::LBracket})) {
      auto index = expression();
      Token bracket = consume(TokenKind::RBracket, "Expect ']' after index.");
      if (match({TokenKind::Eq})) {
        auto value = expression();
        expr = std::make_unique<IndexSetExpr>(std::move(expr), std::move(index),
                                              std::move(value));
      } else {
        expr = std::make_unique<IndexExpr>(std::move(expr), bracket,
                                           std::move(index));
      }
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

  if (match({TokenKind::Identifier, TokenKind::Type})) {
    return std::make_unique<VarExpr>(previous());
  }

  if (match({TokenKind::Fn})) {
    Token fn_tok = previous();
    consume(TokenKind::LParen, "Expect '(' after 'fn' in anonymous function.");
    std::vector<std::string_view> params;
    while (!check(TokenKind::RParen) && !is_at_end()) {
      auto param = consume(TokenKind::Identifier, "Expect parameter name.");
      params.push_back(param.lexeme());
      if (match({TokenKind::Colon})) {
        consume(TokenKind::Identifier, "Expect type annotation.");
      }
      if (!match({TokenKind::Comma})) break;
    }
    consume(TokenKind::RParen, "Expect ')' after parameters.");
    if (match({TokenKind::Colon})) {
      consume(TokenKind::Identifier, "Expect return type.");
    }
    consume(TokenKind::LBrace, "Expect '{' before function body.");
    auto body = block_statement();
    consume(TokenKind::RBrace, "Expect '}' after function body.");
    return std::make_unique<FunctionExpr>(fn_tok, params, std::move(body));
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

Token Parser::consume(const TokenKind type, [[maybe_unused]] const char* message) {
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
