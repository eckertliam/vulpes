#include "lexer.hpp"

Lexer::Lexer(std::string source) {
    this->source = source;
    this->start = 0;
    this->current = 0;
    this->line = 1;
    this->column = 1;
}
