#include "vm/instruction.hpp"
#include "vm/opcode.hpp"
#define CATCH_CONFIG_MAIN

#include "vm/function.hpp"
#include "vm/machine.hpp"
#include "vm/value.hpp"

#include <catch2/catch_test_macros.hpp>

using namespace vulpes::vm;

TEST_CASE("Machine can push and pop a value", "[vm]") {
    std::vector<Function> dummy_functions{Function({}, {}, 0)}; // dummy function
    Machine vm(dummy_functions, 0);

    vm.push_value(Value(int64_t(42)));
    REQUIRE(vm.pop_value() == Value(int64_t(42)));
}

TEST_CASE("Machine can instantiate a string", "[vm]") {
    std::vector<Function> dummy_functions{Function({}, {}, 0)}; // dummy function
    Machine vm(dummy_functions, 0);

    std::string str = "Hello, World!";

    for (char c : str) {
        vm.push_value(Value(c));
    }

    vm.push_value(Value(int64_t(str.size())));
    String* string = vm.make_string();
    REQUIRE(string->str() == str);
}

TEST_CASE("Machine can instantiate a list", "[vm]") {
    Function function{
        {
            // push the false value
            Instruction(OpCode::LoadConst, 0, 0, 0),
            // make the list
            Instruction(OpCode::MakeList, 0, 0, 0),
            Instruction(OpCode::Halt, 0, 0, 0),
        },
        {FALSE_VALUE},
        0,
    };

    Machine vm({function}, 0);

    // expected list: [1, 2, 3]
    std::vector<Value> expected{};
    INFO("About to run VM");
    vm.run();
    auto result = vm.pop_value();
    INFO("Result type: " << static_cast<int>(result.type_of()));
    INFO("Is object: " << result.is_object());
    INFO("Result: " << result.to_string());

    REQUIRE(result.is_object());
    auto list = static_cast<List*>(result.as_object());
    REQUIRE(list->length().as_int() == 3);
    REQUIRE(list->get(Value(int64_t(0))) == Value(int64_t(1)));
    REQUIRE(list->get(Value(int64_t(1))) == Value(int64_t(2)));
    REQUIRE(list->get(Value(int64_t(2))) == Value(int64_t(3)));
}