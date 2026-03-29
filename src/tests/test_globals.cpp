#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Top-level const accessible from function", "[globals]") {
  auto output = vulpes::test::run_capture(
      "const X = 42; fn getX() { return X; } println(getX());");
  REQUIRE(output == "42\n");
}

TEST_CASE("Top-level let accessible from function", "[globals]") {
  auto output = vulpes::test::run_capture(
      "let x = 10; fn getX() { return x; } println(getX());");
  REQUIRE(output == "10\n");
}

TEST_CASE("Top-level let mutable from top level", "[globals]") {
  auto output = vulpes::test::run_capture(
      "let x = 1; x = 2; println(x);");
  REQUIRE(output == "2\n");
}

TEST_CASE("Const immutability", "[globals]") {
  REQUIRE_THROWS_WITH(
      vulpes::test::run_capture("const X = 5; X = 10;"),
      Catch::Matchers::ContainsSubstring("Cannot assign to const"));
}

TEST_CASE("Multi-arg print", "[globals]") {
  auto output = vulpes::test::run_capture("print(\"Hello\", \" \", \"World\"); println(\"\");");
  REQUIRE(output == "Hello World\n");
}

TEST_CASE("Spec example: const and function", "[globals]") {
  auto output = vulpes::test::run_capture(
      "const GREETING = \"Hello\"; "
      "fn main() { let name = \"World\"; println(GREETING + \", \" + name + \"!\"); }");
  REQUIRE(output == "Hello, World!\n");
}
