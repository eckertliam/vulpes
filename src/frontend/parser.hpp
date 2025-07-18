#pragma once

#include "ast.hpp"
#include "lexer.hpp"

#include <vector>

namespace vulpes::frontend {

class Parser {
public:
    Parser(Lexer& lexer);

    std::vector<std::unique_ptr<Stmt>> parse();

private:
    std::unique_ptr<Stmt> declaration();
    std::unique_ptr<Stmt> let_declaration();
    std::unique_ptr<Stmt> const_declaration();
    std::unique_ptr<Stmt> statement();
    std::unique_ptr<Stmt> expression_statement();
    std::unique_ptr<Expr> expression();
    std::unique_ptr<Expr> assignment();
    std::unique_ptr<Expr> logical_or();
    std::unique_ptr<Expr> logical_and();
    std::unique_ptr<Expr> equality();
    std::unique_ptr<Expr> comparison();
    std::unique_ptr<Expr> term();
    std::unique_ptr<Expr> factor();
    std::unique_ptr<Expr> unary();
    std::unique_ptr<Expr> call();
    std::unique_ptr<Expr> primary();

    bool match(const std::vector<TokenKind>& types);
    Token consume(TokenKind type, const char* message);
    bool check(TokenKind type);
    Token advance();
    bool is_at_end();
    Token peek();
    Token previous();

    Lexer& m_lexer;
    Token m_current;
    Token m_previous;
    bool m_had_error = false;
};

} // namespace vulpes::frontend
