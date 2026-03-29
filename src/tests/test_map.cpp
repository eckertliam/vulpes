#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Map creation and printing", "[map]") {
  auto output = vulpes::test::run_capture("let m = map(); println(m);");
  REQUIRE(output == "{}\n");
}

TEST_CASE("Map set and get", "[map]") {
  auto output = vulpes::test::run_capture(
      "let m = map(); m[\"key\"] = \"value\"; println(m[\"key\"]);");
  REQUIRE(output == "value\n");
}

TEST_CASE("Map with integer keys", "[map]") {
  auto output = vulpes::test::run_capture(
      "let m = map(); m[1] = \"one\"; m[2] = \"two\"; println(m[1]); println(m[2]);");
  REQUIRE(output == "one\ntwo\n");
}

TEST_CASE("Map len", "[map]") {
  auto output = vulpes::test::run_capture(
      "let m = map(); m[\"a\"] = 1; m[\"b\"] = 2; println(len(m));");
  REQUIRE(output == "2\n");
}

TEST_CASE("Map missing key returns null", "[map]") {
  auto output = vulpes::test::run_capture(
      "let m = map(); println(m[\"missing\"]);");
  REQUIRE(output == "null\n");
}

TEST_CASE("Map type check", "[map]") {
  auto output = vulpes::test::run_capture("println(type(map()));");
  REQUIRE(output == "map\n");
}

TEST_CASE("Map update existing key", "[map]") {
  auto output = vulpes::test::run_capture(
      "let m = map(); m[\"x\"] = 1; m[\"x\"] = 2; println(m[\"x\"]);");
  REQUIRE(output == "2\n");
}
