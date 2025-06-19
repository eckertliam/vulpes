#include "token.hpp"

const char* token_kind_to_string(TokenKind kind) {
    switch (kind) {
        case TokenKind::Identifier: return "Identifier";
        case TokenKind::Number: return "Number";
        case TokenKind::String: return "String";
        case TokenKind::Let: return "Let";
        case TokenKind::Fn: return "Fn";
        case TokenKind::If: return "If";
        case TokenKind::Else: return "Else";
        case TokenKind::While: return "While";
        case TokenKind::Loop: return "Loop";
        case TokenKind::Return: return "Return";
        case TokenKind::True: return "True";
        case TokenKind::False: return "False";
        case TokenKind::LParen: return "(";
        case TokenKind::RParen: return ")";
        case TokenKind::LBrace: return "{";
        case TokenKind::RBrace: return "}";
        case TokenKind::LBracket: return "[";
        case TokenKind::RBracket: return "]";
        case TokenKind::Comma: return ",";
        case TokenKind::Dot: return ".";
        case TokenKind::Colon: return ":";
        case TokenKind::Semicolon: return ";";
        case TokenKind::Plus: return "+";
        case TokenKind::Minus: return "-";
        case TokenKind::Star: return "*";
        case TokenKind::Slash: return "/";
        case TokenKind::Percent: return "%";
        case TokenKind::Eq: return "=";
        case TokenKind::EqEq: return "==";
        case TokenKind::Bang: return "!";
        case TokenKind::BangEq: return "!=";
        case TokenKind::Less: return "<";
        case TokenKind::LessEq: return "<=";
        case TokenKind::Greater: return ">";
        case TokenKind::GreaterEq: return ">=";
        case TokenKind::AmpAmp: return "&&";
        case TokenKind::BarBar: return "||";
        case TokenKind::Error: return "Error";
        case TokenKind::Eof: return "Eof";
        default: return "Unknown";
    }
}