#include "frontend/parser.hpp"
#include "frontend/lexer.hpp"

#include <catch2/catch_test_macros.hpp>

using namespace vulpes::frontend;

TEST_CASE("Parser parses simple expressions", "[parser]") {
    std::string source = "1 + 2 * 3;";
    Lexer lexer(source);
    Parser parser(lexer);
    auto statements = parser.parse();

    REQUIRE(statements.size() == 1);
    auto* expr_stmt = dynamic_cast<ExpressionStmt*>(statements[0].get());
    REQUIRE(expr_stmt != nullptr);

    auto* binary_expr = dynamic_cast<BinaryExpr*>(expr_stmt->expr.get());
    REQUIRE(binary_expr != nullptr);
    REQUIRE(binary_expr->op.kind == TokenKind::Plus);

    auto* literal_expr = dynamic_cast<IntegerLiteral*>(binary_expr->left.get());
    REQUIRE(literal_expr != nullptr);

    auto* mul_expr = dynamic_cast<BinaryExpr*>(binary_expr->right.get());
    REQUIRE(mul_expr != nullptr);
    REQUIRE(mul_expr->op.kind == TokenKind::Star);
}

TEST_CASE("Parser parses let statements", "[parser]") {
    std::string source = "let x = 10;";
    Lexer lexer(source);
    Parser parser(lexer);
    auto statements = parser.parse();

    REQUIRE(statements.size() == 1);
    auto* let_stmt = dynamic_cast<LetStmt*>(statements[0].get());
    REQUIRE(let_stmt != nullptr);
    REQUIRE(let_stmt->name.location.lexeme == "x");

    auto* literal_expr = dynamic_cast<IntegerLiteral*>(let_stmt->initializer.get());
    REQUIRE(literal_expr != nullptr);
}

TEST_CASE("Parser parses const statements", "[parser]") {
    std::string source = "const y = \"hello\";";
    Lexer lexer(source);
    Parser parser(lexer);
    auto statements = parser.parse();

    REQUIRE(statements.size() == 1);
    auto* const_stmt = dynamic_cast<ConstStmt*>(statements[0].get());
    REQUIRE(const_stmt != nullptr);
    REQUIRE(const_stmt->name.location.lexeme == "y");

    auto* literal_expr = dynamic_cast<StringLiteral*>(const_stmt->initializer.get());
    REQUIRE(literal_expr != nullptr);
}
