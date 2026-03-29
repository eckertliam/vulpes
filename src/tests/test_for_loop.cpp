#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("For loop iterates over integer range", "[for]") {
  auto output = vulpes::test::run_capture(
      "for i in 5 { println(i); }");
  REQUIRE(output == "0\n1\n2\n3\n4\n");
}

TEST_CASE("For loop with break", "[for]") {
  auto output = vulpes::test::run_capture(
      "for i in 10 { if i == 3 { break; } println(i); }");
  REQUIRE(output == "0\n1\n2\n");
}

TEST_CASE("For loop with continue", "[for]") {
  auto output = vulpes::test::run_capture(
      "for i in 5 { if i == 2 { continue; } println(i); }");
  REQUIRE(output == "0\n1\n3\n4\n");
}

TEST_CASE("For loop with accumulator", "[for]") {
  auto output = vulpes::test::run_capture(
      "let sum = 0; for i in 5 { sum = sum + i; } println(sum);");
  REQUIRE(output == "10\n");
}

TEST_CASE("Nested for loops", "[for]") {
  auto output = vulpes::test::run_capture(
      "for i in 3 { for j in 2 { print(i); print(j); print(\" \"); } } println(\"\");");
  REQUIRE(output == "00 01 10 11 20 21 \n");
}
