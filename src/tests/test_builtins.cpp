#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("type() returns int for integer", "[builtins]") {
  auto output = vulpes::test::run_capture("println(type(123));");
  REQUIRE(output == "int\n");
}

TEST_CASE("type() returns float for float", "[builtins]") {
  auto output = vulpes::test::run_capture("println(type(1.5));");
  REQUIRE(output == "float\n");
}

TEST_CASE("type() returns string for string", "[builtins]") {
  auto output = vulpes::test::run_capture("println(type(\"hello\"));");
  REQUIRE(output == "string\n");
}

TEST_CASE("type() returns bool for boolean", "[builtins]") {
  auto output = vulpes::test::run_capture("println(type(true));");
  REQUIRE(output == "bool\n");
}

TEST_CASE("type() returns null for null", "[builtins]") {
  auto output = vulpes::test::run_capture("println(type(null));");
  REQUIRE(output == "null\n");
}

TEST_CASE("throw_err raises runtime error", "[builtins]") {
  REQUIRE_THROWS_WITH(
      vulpes::test::run_capture("throw_err(\"Expected a valid integer\");"),
      "Expected a valid integer");
}
