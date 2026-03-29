#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Logical AND", "[logical]") {
  REQUIRE(vulpes::test::run_capture("println(true && true);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(true && false);") == "false\n");
  REQUIRE(vulpes::test::run_capture("println(false && true);") == "false\n");
  REQUIRE(vulpes::test::run_capture("println(false && false);") == "false\n");
}

TEST_CASE("Logical OR", "[logical]") {
  REQUIRE(vulpes::test::run_capture("println(true || true);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(true || false);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(false || true);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(false || false);") == "false\n");
}

TEST_CASE("Short-circuit AND", "[logical]") {
  // false && (side-effect) should NOT evaluate the side-effect
  REQUIRE(vulpes::test::run_capture(
      "let x = 0; if false && true { x = 1; } println(x);") == "0\n");
}

TEST_CASE("Short-circuit OR", "[logical]") {
  // true || (side-effect) should NOT evaluate the side-effect
  REQUIRE(vulpes::test::run_capture(
      "let x = 0; if true || false { x = 1; } println(x);") == "1\n");
}

TEST_CASE("String concatenation", "[string]") {
  REQUIRE(vulpes::test::run_capture("println(\"hello\" + \" world\");") == "hello world\n");
  REQUIRE(vulpes::test::run_capture("println(\"a\" + \"b\" + \"c\");") == "abc\n");
}

TEST_CASE("Modulo operator", "[arithmetic]") {
  REQUIRE(vulpes::test::run_capture("println(10 % 3);") == "1\n");
  REQUIRE(vulpes::test::run_capture("println(7 % 2);") == "1\n");
  REQUIRE(vulpes::test::run_capture("println(6 % 3);") == "0\n");
}
