#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"
#include "vm/object/boolean.hpp"

TEST_CASE("Boolean literal true", "[boolean]") {
  auto output = vulpes::test::run_capture("println(true);");
  REQUIRE(output == "true\n");
}

TEST_CASE("Boolean literal false", "[boolean]") {
  auto output = vulpes::test::run_capture("println(false);");
  REQUIRE(output == "false\n");
}

TEST_CASE("Boolean toString", "[boolean]") {
  vulpes::vm::Machine vm;
  auto* t = vm.allocate<vulpes::vm::object::Boolean>(true);
  auto* f = vm.allocate<vulpes::vm::object::Boolean>(false);
  REQUIRE(t->toString() == "true");
  REQUIRE(f->toString() == "false");
  REQUIRE(t->value() == true);
  REQUIRE(f->value() == false);
}
