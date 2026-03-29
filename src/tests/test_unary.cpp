#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Negate integer", "[unary]") {
  REQUIRE(vulpes::test::run_capture("println(-5);") == "-5\n");
  REQUIRE(vulpes::test::run_capture("println(-0);") == "0\n");
}

TEST_CASE("Negate float", "[unary]") {
  REQUIRE(vulpes::test::run_capture("println(-3.14);") == "-3.140000\n");
}

TEST_CASE("Double negate", "[unary]") {
  REQUIRE(vulpes::test::run_capture("println(--5);") == "5\n");
}

TEST_CASE("Unary plus", "[unary]") {
  REQUIRE(vulpes::test::run_capture("println(+5);") == "5\n");
}

TEST_CASE("Logical not", "[unary]") {
  REQUIRE(vulpes::test::run_capture("println(!true);") == "false\n");
  REQUIRE(vulpes::test::run_capture("println(!false);") == "true\n");
}

TEST_CASE("Double logical not", "[unary]") {
  REQUIRE(vulpes::test::run_capture("println(!!true);") == "true\n");
}

TEST_CASE("Negate expression", "[unary]") {
  REQUIRE(vulpes::test::run_capture("println(-(1 + 2));") == "-3\n");
}

TEST_CASE("Not on truthy values", "[unary]") {
  REQUIRE(vulpes::test::run_capture("println(!0);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(!1);") == "false\n");
  REQUIRE(vulpes::test::run_capture("println(!null);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(!\"hello\");") == "false\n");
  REQUIRE(vulpes::test::run_capture("println(!\"\");") == "true\n");
}
