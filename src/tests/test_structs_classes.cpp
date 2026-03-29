#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Struct construction and field access", "[structs]") {
  auto output = vulpes::test::run_capture(
      "struct Point { x: int, y: int }; let p = Point(3, 4); println(p.x); println(p.y);");
  REQUIRE(output == "3\n4\n");
}

TEST_CASE("Class construction with default null fields", "[classes]") {
  auto output = vulpes::test::run_capture(
      "class Foo { val: int; }; let f = Foo(); println(f.val);");
  REQUIRE(output == "null\n");
}

TEST_CASE("Class field mutation", "[classes]") {
  auto output = vulpes::test::run_capture(
      "class Foo { val: int; }; let f = Foo(); f.val = 42; println(f.val);");
  REQUIRE(output == "42\n");
}

TEST_CASE("Enum tags as integers", "[enums]") {
  auto output = vulpes::test::run_capture(
      "enum Color { Red, Green, Blue }; println(Red + Green + Blue);");
  REQUIRE(output == "3\n");
}

TEST_CASE("Struct with type builtin", "[structs]") {
  auto output = vulpes::test::run_capture(
      "struct Point { x: int, y: int }; let p = Point(1, 2); println(type(p));");
  REQUIRE(output == "object\n");
}
