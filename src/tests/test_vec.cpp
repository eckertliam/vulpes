#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Vec creation and printing", "[vec]") {
  auto output = vulpes::test::run_capture("let v = vec(1, 2, 3); println(v);");
  REQUIRE(output == "[1, 2, 3]\n");
}

TEST_CASE("Vec indexing", "[vec]") {
  auto output = vulpes::test::run_capture("let v = vec(10, 20, 30); println(v[1]);");
  REQUIRE(output == "20\n");
}

TEST_CASE("Vec index assignment", "[vec]") {
  auto output = vulpes::test::run_capture("let v = vec(1, 2, 3); v[0] = 99; println(v);");
  REQUIRE(output == "[99, 2, 3]\n");
}

TEST_CASE("Vec push and len", "[vec]") {
  auto output = vulpes::test::run_capture(
      "let v = vec(); push(v, 1); push(v, 2); println(len(v)); println(v);");
  REQUIRE(output == "2\n[1, 2]\n");
}

TEST_CASE("Vec pop", "[vec]") {
  auto output = vulpes::test::run_capture(
      "let v = vec(1, 2, 3); let x = pop(v); println(x); println(v);");
  REQUIRE(output == "3\n[1, 2]\n");
}

TEST_CASE("Vec out of bounds throws", "[vec]") {
  REQUIRE_THROWS_WITH(
      vulpes::test::run_capture("let v = vec(1, 2); println(v[5]);"),
      Catch::Matchers::ContainsSubstring("IndexOutOfBounds"));
}

TEST_CASE("String indexing", "[vec]") {
  auto output = vulpes::test::run_capture("println(\"hello\"[0]);");
  REQUIRE(output == "h\n");
}

TEST_CASE("String length", "[vec]") {
  auto output = vulpes::test::run_capture("println(len(\"hello\"));");
  REQUIRE(output == "5\n");
}

TEST_CASE("Vec type check", "[vec]") {
  auto output = vulpes::test::run_capture("println(type(vec(1, 2)));");
  REQUIRE(output == "vec\n");
}

TEST_CASE("Struct immutability enforced", "[structs]") {
  REQUIRE_THROWS_WITH(
      vulpes::test::run_capture("struct Point { x: int, y: int }; let p = Point(1, 2); p.x = 5;"),
      Catch::Matchers::ContainsSubstring("immutable"));
}
