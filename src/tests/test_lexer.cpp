#include "../frontend/lexer.hpp"
#include <catch2/catch_test_macros.hpp>

TEST_CASE("Lexer simple tokens", "[lexer]") {
    auto source = "let x = 10;";
    vulpes::frontend::Lexer lexer(source);

    auto token = lexer.next_token();
    REQUIRE(token.kind == vulpes::frontend::TokenKind::Let);

    token = lexer.next_token();
    REQUIRE(token.kind == vulpes::frontend::TokenKind::Identifier);
    REQUIRE(token.location.lexeme == "x");

    token = lexer.next_token();
    REQUIRE(token.kind == vulpes::frontend::TokenKind::Eq);

    token = lexer.next_token();
    REQUIRE(token.kind == vulpes::frontend::TokenKind::Integer);
    REQUIRE(token.location.lexeme == "10");

    token = lexer.next_token();
    REQUIRE(token.kind == vulpes::frontend::TokenKind::Semicolon);

    token = lexer.next_token();
    REQUIRE(token.kind == vulpes::frontend::TokenKind::Eof);
}

TEST_CASE("Lexer all tokens", "[lexer]") {
    auto source = R"(
        let const fn return if else while for in break continue
        struct class enum pub from import export true false null type
        ( ) { } [ ] , . : ;
        + - * / % = == != < <= > >= && ||
        "hello" 'c' 123 12.34
    )";
    vulpes::frontend::Lexer lexer(source);

    vulpes::frontend::TokenKind expected[] = {
        vulpes::frontend::TokenKind::Let,       vulpes::frontend::TokenKind::Const,
        vulpes::frontend::TokenKind::Fn,        vulpes::frontend::TokenKind::Return,
        vulpes::frontend::TokenKind::If,        vulpes::frontend::TokenKind::Else,
        vulpes::frontend::TokenKind::While,     vulpes::frontend::TokenKind::For,
        vulpes::frontend::TokenKind::In,        vulpes::frontend::TokenKind::Break,
        vulpes::frontend::TokenKind::Continue,  vulpes::frontend::TokenKind::Struct,
        vulpes::frontend::TokenKind::Class,     vulpes::frontend::TokenKind::Enum,
        vulpes::frontend::TokenKind::Pub,       vulpes::frontend::TokenKind::From,
        vulpes::frontend::TokenKind::Import,    vulpes::frontend::TokenKind::Export,
        vulpes::frontend::TokenKind::True,      vulpes::frontend::TokenKind::False,
        vulpes::frontend::TokenKind::Null,      vulpes::frontend::TokenKind::Type,
        vulpes::frontend::TokenKind::LParen,    vulpes::frontend::TokenKind::RParen,
        vulpes::frontend::TokenKind::LBrace,    vulpes::frontend::TokenKind::RBrace,
        vulpes::frontend::TokenKind::LBracket,  vulpes::frontend::TokenKind::RBracket,
        vulpes::frontend::TokenKind::Comma,     vulpes::frontend::TokenKind::Dot,
        vulpes::frontend::TokenKind::Colon,     vulpes::frontend::TokenKind::Semicolon,
        vulpes::frontend::TokenKind::Plus,      vulpes::frontend::TokenKind::Minus,
        vulpes::frontend::TokenKind::Star,      vulpes::frontend::TokenKind::Slash,
        vulpes::frontend::TokenKind::Percent,   vulpes::frontend::TokenKind::Eq,
        vulpes::frontend::TokenKind::EqEq,      vulpes::frontend::TokenKind::BangEq,
        vulpes::frontend::TokenKind::Less,      vulpes::frontend::TokenKind::LessEq,
        vulpes::frontend::TokenKind::Greater,   vulpes::frontend::TokenKind::GreaterEq,
        vulpes::frontend::TokenKind::AmpAmp,    vulpes::frontend::TokenKind::BarBar,
        vulpes::frontend::TokenKind::String,    vulpes::frontend::TokenKind::Char,
        vulpes::frontend::TokenKind::Integer,   vulpes::frontend::TokenKind::Float,
        vulpes::frontend::TokenKind::Eof,
    };

    for (auto expected_kind : expected) {
        auto token = lexer.next_token();
        REQUIRE(token.kind == expected_kind);
    }
}
