#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("If true executes body", "[if]") {
  REQUIRE(vulpes::test::run_capture("let x = 0; if true { x = 1; } println(x);") == "1\n");
}

TEST_CASE("If false skips body", "[if]") {
  REQUIRE(vulpes::test::run_capture("let x = 0; if false { x = 1; } println(x);") == "0\n");
}

TEST_CASE("If-else picks else branch", "[if]") {
  REQUIRE(vulpes::test::run_capture("let x = 0; if false { x = 1; } else { x = 2; } println(x);") == "2\n");
}

TEST_CASE("If-else picks then branch", "[if]") {
  REQUIRE(vulpes::test::run_capture("let x = 0; if true { x = 1; } else { x = 2; } println(x);") == "1\n");
}

TEST_CASE("If with comparison condition", "[if]") {
  REQUIRE(vulpes::test::run_capture("let x = 0; if 1 < 2 { x = 10; } println(x);") == "10\n");
}

TEST_CASE("Nested if", "[if]") {
  auto output = vulpes::test::run_capture(
      "let x = 0; "
      "if true { "
      "  if false { x = 1; } else { x = 2; } "
      "} "
      "println(x);");
  REQUIRE(output == "2\n");
}

TEST_CASE("If with integer truthiness", "[if]") {
  REQUIRE(vulpes::test::run_capture("let x = 0; if 1 { x = 1; } println(x);") == "1\n");
  REQUIRE(vulpes::test::run_capture("let x = 0; if 0 { x = 1; } println(x);") == "0\n");
}
