#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Integer equality", "[comparison]") {
  REQUIRE(vulpes::test::run_capture("println(1 == 1);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(1 == 2);") == "false\n");
}

TEST_CASE("Integer inequality", "[comparison]") {
  REQUIRE(vulpes::test::run_capture("println(1 != 2);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(1 != 1);") == "false\n");
}

TEST_CASE("Integer less than", "[comparison]") {
  REQUIRE(vulpes::test::run_capture("println(1 < 2);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(2 < 1);") == "false\n");
  REQUIRE(vulpes::test::run_capture("println(1 < 1);") == "false\n");
}

TEST_CASE("Integer greater than", "[comparison]") {
  REQUIRE(vulpes::test::run_capture("println(2 > 1);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(1 > 2);") == "false\n");
}

TEST_CASE("Integer less than or equal", "[comparison]") {
  REQUIRE(vulpes::test::run_capture("println(1 <= 1);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(1 <= 2);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(2 <= 1);") == "false\n");
}

TEST_CASE("Integer greater than or equal", "[comparison]") {
  REQUIRE(vulpes::test::run_capture("println(1 >= 1);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(2 >= 1);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(1 >= 2);") == "false\n");
}

TEST_CASE("Float comparisons", "[comparison]") {
  REQUIRE(vulpes::test::run_capture("println(1.5 < 2.0);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(3.14 == 3.14);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(1.0 != 2.0);") == "true\n");
}

TEST_CASE("String equality", "[comparison]") {
  REQUIRE(vulpes::test::run_capture("println(\"hello\" == \"hello\");") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(\"hello\" == \"world\");") == "false\n");
  REQUIRE(vulpes::test::run_capture("println(\"hello\" != \"world\");") == "true\n");
}

TEST_CASE("Boolean equality", "[comparison]") {
  REQUIRE(vulpes::test::run_capture("println(true == true);") == "true\n");
  REQUIRE(vulpes::test::run_capture("println(true == false);") == "false\n");
}

TEST_CASE("Null equality", "[comparison]") {
  REQUIRE(vulpes::test::run_capture("println(null == null);") == "true\n");
}
