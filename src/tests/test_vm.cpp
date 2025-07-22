#define CATCH_CONFIG_MAIN

#include "vm/object/function.hpp"
#include "vm/machine.hpp"

#include <cstdint>
#include <catch2/catch_test_macros.hpp>

#include "vm/object/integer.hpp"
#include "vm/instruction.hpp"

TEST_CASE("Machine can push and pop a value", "[vm]") {
  vulpes::vm::Machine vm;
  auto* function = vm.buildFunction("dummy", 0);
  vm.pushCallFrame(function);

  auto* int_obj = vm.allocate<vulpes::vm::object::Integer>(1);
  vm.push(int_obj);
  REQUIRE(vm.pop() == int_obj);
}

TEST_CASE("Machine can add two ints", "[vm]") {
  vulpes::vm::Machine vm;
  auto* function = vm.buildFunction("dummy", 0);

  auto* lhs_int = vm.allocate<vulpes::vm::object::Integer>(1);
  auto* rhs_int = vm.allocate<vulpes::vm::object::Integer>(2);

  auto lhs_ref = function->addConstant(lhs_int);
  auto rhs_ref = function->addConstant(rhs_int);

  function->addInstruction({vulpes::vm::Opcode::LOAD_CONST, rhs_ref});
  function->addInstruction({vulpes::vm::Opcode::LOAD_CONST, lhs_ref});

  function->addInstruction({vulpes::vm::Opcode::ADD});
  function->addInstruction({vulpes::vm::Opcode::EOP});

  vm.pushCallFrame(function);
  vm.run();

  auto* result = vm.pop();

  auto* as_int = dynamic_cast<vulpes::vm::object::Integer*>(result);
  REQUIRE(as_int != nullptr);
  REQUIRE(as_int->value() == static_cast<int64_t>(3));

}