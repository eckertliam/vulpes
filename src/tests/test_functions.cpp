#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Function with arguments", "[functions]") {
  auto output = vulpes::test::run_capture(
      "fn add(a, b) { return a + b; } println(add(2, 3));");
  REQUIRE(output == "5\n");
}

TEST_CASE("Function with multiple calls", "[functions]") {
  auto output = vulpes::test::run_capture(
      "fn square(x) { return x * x; } println(square(3)); println(square(4));");
  REQUIRE(output == "9\n16\n");
}

TEST_CASE("Nested function calls", "[functions]") {
  auto output = vulpes::test::run_capture(
      "fn add(a, b) { return a + b; } println(add(add(1, 2), add(3, 4)));");
  REQUIRE(output == "10\n");
}

TEST_CASE("Anonymous function", "[functions]") {
  auto output = vulpes::test::run_capture(
      "let double = fn(x) { return x * 2; }; println(double(5));");
  REQUIRE(output == "10\n");
}

TEST_CASE("Anonymous function as argument", "[functions]") {
  auto output = vulpes::test::run_capture(
      "fn apply(f, x) { return f(x); } "
      "println(apply(fn(x) { return x + 1; }, 41));");
  REQUIRE(output == "42\n");
}

TEST_CASE("Function implicit return null", "[functions]") {
  auto output = vulpes::test::run_capture(
      "fn noop() { } println(noop());");
  REQUIRE(output == "null\n");
}

TEST_CASE("Recursive function", "[functions]") {
  auto output = vulpes::test::run_capture(
      "fn fact(n) { if n <= 1 { return 1; } return n * fact(n - 1); } "
      "println(fact(5));");
  REQUIRE(output == "120\n");
}
