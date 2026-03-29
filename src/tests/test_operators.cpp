#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_string.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Power operator", "[operators]") {
  auto output = vulpes::test::run_capture("println(2 ** 10);");
  REQUIRE(output == "1024\n");
}

TEST_CASE("Bitwise AND", "[operators]") {
  auto output = vulpes::test::run_capture("println(0xFF & 0x0F);");
  REQUIRE(output == "15\n");
}

TEST_CASE("Bitwise OR", "[operators]") {
  auto output = vulpes::test::run_capture("println(0xF0 | 0x0F);");
  REQUIRE(output == "255\n");
}

TEST_CASE("Bitwise XOR", "[operators]") {
  auto output = vulpes::test::run_capture("println(0xFF ^ 0x0F);");
  REQUIRE(output == "240\n");
}

TEST_CASE("Left shift", "[operators]") {
  auto output = vulpes::test::run_capture("println(1 << 8);");
  REQUIRE(output == "256\n");
}

TEST_CASE("Right shift", "[operators]") {
  auto output = vulpes::test::run_capture("println(256 >> 4);");
  REQUIRE(output == "16\n");
}

TEST_CASE("Hex literal", "[operators]") {
  auto output = vulpes::test::run_capture("println(0xFF);");
  REQUIRE(output == "255\n");
}

TEST_CASE("Binary literal", "[operators]") {
  auto output = vulpes::test::run_capture("println(0b1010);");
  REQUIRE(output == "10\n");
}

TEST_CASE("Underscore separator in number", "[operators]") {
  auto output = vulpes::test::run_capture("println(1_000_000);");
  REQUIRE(output == "1000000\n");
}

TEST_CASE("DivideByZero throws", "[operators]") {
  REQUIRE_THROWS_WITH(
      vulpes::test::run_capture("println(1 / 0);"),
      "DivideByZero");
}

TEST_CASE("Modulo by zero throws", "[operators]") {
  REQUIRE_THROWS_WITH(
      vulpes::test::run_capture("println(1 % 0);"),
      "DivideByZero");
}
