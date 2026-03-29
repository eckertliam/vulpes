#include <catch2/catch_test_macros.hpp>

#include "tests/test_helpers.hpp"

TEST_CASE("Closure captures local by reference", "[closures]") {
  auto output = vulpes::test::run_capture(
      "fn make_counter() { let count = 0; "
      "let inc = fn() { count = count + 1; return count; }; "
      "return inc; } "
      "let c = make_counter(); println(c()); println(c()); println(c());");
  REQUIRE(output == "1\n2\n3\n");
}

TEST_CASE("Closure captures function argument", "[closures]") {
  auto output = vulpes::test::run_capture(
      "fn make_adder(x) { return fn(y) { return x + y; }; } "
      "let add5 = make_adder(5); println(add5(3)); println(add5(10));");
  REQUIRE(output == "8\n15\n");
}

TEST_CASE("Closure in let binding", "[closures]") {
  auto output = vulpes::test::run_capture(
      "fn test() { let x = 10; let f = fn() { return x; }; println(f()); } test();");
  REQUIRE(output == "10\n");
}

TEST_CASE("Closure mutation visible", "[closures]") {
  auto output = vulpes::test::run_capture(
      "fn test() { let x = 1; let set = fn(v) { x = v; }; "
      "let get = fn() { return x; }; "
      "println(get()); set(42); println(get()); } test();");
  REQUIRE(output == "1\n42\n");
}
