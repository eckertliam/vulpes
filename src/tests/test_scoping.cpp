#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Inner block shadows outer variable", "[scope]") {
  auto output = vulpes::test::run_capture(
      "let x = 1; { let x = 2; println(x); } println(x);");
  REQUIRE(output == "2\n1\n");
}

TEST_CASE("Inner block mutation visible in outer", "[scope]") {
  auto output = vulpes::test::run_capture(
      "let x = 1; { x = 2; } println(x);");
  REQUIRE(output == "2\n");
}

TEST_CASE("Variable not visible after block", "[scope]") {
  // y is defined in inner block, x should still be accessible
  auto output = vulpes::test::run_capture(
      "let x = 1; { let y = 2; x = x + y; } println(x);");
  REQUIRE(output == "3\n");
}
