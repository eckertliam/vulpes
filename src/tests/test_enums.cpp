#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Enum tags get integer values", "[enums]") {
  auto output = vulpes::test::run_capture(
      "enum Color { Red, Green, Blue }; println(Red); println(Green); println(Blue);");
  REQUIRE(output == "0\n1\n2\n");
}

TEST_CASE("Enum tags can be compared", "[enums]") {
  auto output = vulpes::test::run_capture(
      "enum Dir { Up, Down }; println(Up == 0); println(Down == 1);");
  REQUIRE(output == "true\ntrue\n");
}
