#pragma once

#include <cstdint>
#include <string>
#include <string_view>
namespace vulpes::frontend {
struct Location {
  uint32_t start_line;
  uint32_t start_column;
  uint32_t end_line;
  uint32_t end_column;
  std::string_view lexeme;

  Location() {
    start_line = 0;
    start_column = 0;
    end_line = 0;
    end_column = 0;
    lexeme = "";
  }

  Location(const uint32_t start_line, const uint32_t start_column,
           const uint32_t end_line, const uint32_t end_column,
           const std::string_view lexeme)
      : start_line(start_line),
        start_column(start_column),
        end_line(end_line),
        end_column(end_column),
        lexeme(lexeme) {}

  [[nodiscard]] std::string toString() const {
    return "[" + std::to_string(start_line) + ":" +
           std::to_string(start_column) + " - " + std::to_string(end_line) +
           ":" + std::to_string(end_column) + "] " + std::string(lexeme);
  }
};
}  // namespace vulpes::frontend