#define CATCH_CONFIG_MAIN

#include "vm/arena.hpp"
#include "vm/function.hpp"
#include "vm/machine.hpp"
#include "vm/object.hpp"
#include "vm/value.hpp"

#include <catch2/catch_test_macros.hpp>

using namespace vulpes::vm;

TEST_CASE("Machine can push and pop a value", "[vm]") {
    std::vector<Function> dummy_functions; // empty for now
    Machine vm(dummy_functions, 0);

    vm.push_value(Value(int64_t(42)));
    REQUIRE(vm.pop_value() == Value(int64_t(42)));
}