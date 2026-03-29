#include "machine.hpp"

#include <functional>
#include <iostream>
#include <string>
#include "instruction.hpp"
#include "object/integer.hpp"
#include "object/native_function.hpp"
#include "object/boolean.hpp"
#include "object/null.hpp"
#include "object/string.hpp"
#include "object/base.hpp"
#include "object/instance.hpp"
#include "object/vec.hpp"
#include "object/map.hpp"
#include "object/upvalue.hpp"
#include "object/byte.hpp"
#include "object/list.hpp"

namespace vulpes::vm {

using namespace object;

Function* Machine::getCurrentFunction() const {
  return call_frames_.back().function;
}

void Machine::run() {
  while (true) {
    Instruction instr = nextInstruction();

    if (instr.opcode == Opcode::EOP) break;

    executeInstruction(instr);
  }
}

Function* Machine::buildFunction(const std::string_view name, size_t arity) {
  // create a new function
  auto* function = allocate<Function>(name, arity);
  // push the function to the global table
  const auto index = addGlobal(function);
  // add the function to the function table
  function_table_[function->name()] = index;
  // return the function
  return function;
}

uint32_t Machine::getStackPointer() const {
  if (call_frames_.empty()) {
    return 0;
  } else {
    return static_cast<uint32_t>(call_frames_.back().sp);
  }
}

void Machine::incrStackPointer() {
  call_frames_.back().sp++;
}

void Machine::decrStackPointer() {
  call_frames_.back().sp--;
}

void Machine::push(BaseObject* object) {
  if (getStackPointer() == STACK_SIZE) {
    throw std::runtime_error("Stack overflow");
  }
  stack_[getStackPointer()] = object;
  incrStackPointer();
}

BaseObject* Machine::pop() {
  if (getStackPointer() == 0) [[unlikely]] {
    throw std::runtime_error("Stack underflow");
  }
  decrStackPointer();
  auto* object = stack_[getStackPointer()];
  return object;
}

BaseObject* Machine::peek(const size_t offset) const {
  if (offset > getStackPointer()) [[unlikely]] {
    throw std::runtime_error("Stack underflow");
  }
  return stack_[getStackPointer() - offset];
}
BaseObject* Machine::peek() const {
  return peek(0);
}

// BEGIN INSTRUCTION EXECUTION
[[noreturn]] static inline void throwWithLocation(const std::string& message,
                                     const std::optional<Location>& src_loc) {
  if (src_loc.has_value()) {
    throw std::runtime_error(message + ": " + src_loc.value().toString());
  }
  throw std::runtime_error(message);
}

static inline void loadGlobal(Machine& machine,
                              const Instruction& instruction) {
  const auto global = machine.getGlobal(instruction.imm);
  if (global == nullptr) {
    throwWithLocation("Global not found", instruction.src_loc);
  }
  machine.push(global);
}

static inline void storeGlobal(Machine& machine,
                               const Instruction& instruction) {
  // pop the value from the stack
  const auto value = machine.pop();
  // store the value at the global index
  machine.setGlobal(instruction.imm, value);
}

static inline void loadConst(Machine& machine, const Instruction& instruction) {
  const auto constant = machine.getCurrentFunction()->getConstant(instruction.imm);
  if (constant == nullptr) {
    throwWithLocation("Constant not found", instruction.src_loc);
  }
  machine.push(constant);
}

static inline void storeLocal(Machine& machine,
                              const Instruction& instruction) {
  const auto value = machine.pop();
  machine.getCurrentFunction()->setLocal(instruction.imm, value);
}

static inline void loadLocal(Machine& machine, const Instruction& instruction) {
  // get the local from the function
  const auto local = machine.getCurrentFunction()->getLocal(instruction.imm);
  if (local == nullptr) {
    throwWithLocation("Local not found", instruction.src_loc);
  }
  // push the local to the stack
  machine.push(local);
}

static inline void callFunction(Machine& machine,
                                const Instruction& instruction) {
  const auto functionObj = machine.pop();

  if (functionObj->type() == ObjectType::NativeFunction) {
    auto* native = dynamic_cast<NativeFunction*>(functionObj);
    // Use the actual arg count from the CALL instruction
    const auto arg_count = instruction.imm;
    std::vector<BaseObject*> native_args(arg_count);
    for (uint32_t i = 0; i < arg_count; i++) {
      native_args[i] = machine.pop();
    }
    auto* result = native->call(machine, native_args);
    if (result == nullptr) {
      result = machine.allocate<Null>();
    }
    machine.push(result);
    return;
  }

  if (functionObj->type() != ObjectType::Function) {
    throwWithLocation("Expected function object", instruction.src_loc);
  }
  const auto function = dynamic_cast<Function*>(functionObj);
  const auto arity = function->getArity();
  // Collect args from stack first
  std::vector<BaseObject*> call_args(arity);
  for (size_t i = 0; i < arity; i++) {
    call_args[i] = machine.pop();
  }
  // Push call frame, then store args in the callee's locals
  machine.pushCallFrame(function);
  for (size_t i = 0; i < arity; i++) {
    function->setLocal(static_cast<uint32_t>(i), call_args[i]);
  }
}

static inline void returnConst(Machine& machine,
                               const Instruction& instruction) {
  // pop the constant from the stack
  const auto constant = machine.getCurrentFunction()->getConstant(instruction.imm);
  if (constant == nullptr) {
    throwWithLocation("Constant not found", instruction.src_loc);
  }
  // pop back to the previous call frame
  machine.popCallFrame();
  // push the constant to the stack
  machine.push(constant);
}

static inline void returnLocal(Machine& machine,

                               const Instruction& instruction) {
  // pop the local from the stack
  const auto local = machine.getCurrentFunction()->getLocal(instruction.imm);
  if (local == nullptr) {
    throwWithLocation("Local not found", instruction.src_loc);
  }
  // pop back to the previous call frame
  machine.popCallFrame();
  // push the local to the stack
  machine.push(local);
}

static inline void returnValue(Machine& machine,
                               [[maybe_unused]] const Instruction& instruction) {
  // pop the value from the stack
  const auto value = machine.pop();
  // pop back to the previous call frame
  machine.popCallFrame();
  // push the value to the stack
  machine.push(value);
}

static inline void add(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->add(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type", instruction.src_loc);
  }
  machine.push(result);
}

static inline void sub(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->sub(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type", instruction.src_loc);
  }
  machine.push(result);
}

static inline void mul(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->mul(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type", instruction.src_loc);
  }
  machine.push(result);
}

static inline void div(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->div(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type", instruction.src_loc);
  }
  machine.push(result);
}

static inline void mod(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->mod(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type", instruction.src_loc);
  }
  machine.push(result);
}

static inline void power(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->pow(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type for **", instruction.src_loc);
  }
  machine.push(result);
}

static inline void shl(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->shl(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type for <<", instruction.src_loc);
  }
  machine.push(result);
}

static inline void shr(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->shr(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type for >>", instruction.src_loc);
  }
  machine.push(result);
}

static inline void bitAnd(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->bit_and(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type for &", instruction.src_loc);
  }
  machine.push(result);
}

static inline void bitXor(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->bit_xor(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type for ^", instruction.src_loc);
  }
  machine.push(result);
}

static inline void bitOr(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->bit_or(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type for |", instruction.src_loc);
  }
  machine.push(result);
}

static inline void getField(Machine& machine, const Instruction& instruction) {
  auto* obj = machine.pop();
  if (obj->type() != ObjectType::Object) {
    throwWithLocation("NullAccess: cannot access field on non-object", instruction.src_loc);
  }
  auto* instance = dynamic_cast<Instance*>(obj);
  auto* name_obj = machine.getCurrentFunction()->getConstant(instruction.imm);
  auto* name_str = dynamic_cast<String*>(name_obj);
  auto* value = instance->getField(name_str->value());
  if (value == nullptr) {
    throwWithLocation("Field not found: " + name_str->value(), instruction.src_loc);
  }
  machine.push(value);
}

static inline void setField(Machine& machine, const Instruction& instruction) {
  auto* value = machine.pop();
  auto* obj = machine.pop();
  if (obj->type() != ObjectType::Object) {
    throwWithLocation("NullAccess: cannot set field on non-object", instruction.src_loc);
  }
  auto* instance = dynamic_cast<Instance*>(obj);
  if (instance->isImmutable()) {
    auto* name_obj = machine.getCurrentFunction()->getConstant(instruction.imm);
    auto* name_str = dynamic_cast<String*>(name_obj);
    throwWithLocation("TypeError: cannot mutate immutable struct field '" + name_str->value() + "'", instruction.src_loc);
  }
  auto* name_obj = machine.getCurrentFunction()->getConstant(instruction.imm);
  auto* name_str = dynamic_cast<String*>(name_obj);
  instance->setField(name_str->value(), value);
  machine.push(value);
}

static inline void indexGet(Machine& machine, const Instruction& instruction) {
  auto* index = machine.pop();
  auto* obj = machine.pop();
  if (obj->type() == ObjectType::Vec) {
    auto* vec = dynamic_cast<Vec*>(obj);
    if (index->type() != ObjectType::Integer) {
      throwWithLocation("TypeError: vec index must be an integer", instruction.src_loc);
    }
    auto idx = dynamic_cast<Integer*>(index)->value();
    machine.push(vec->get(idx));
  } else if (obj->type() == ObjectType::String) {
    auto* str = dynamic_cast<String*>(obj);
    if (index->type() != ObjectType::Integer) {
      throwWithLocation("TypeError: string index must be an integer", instruction.src_loc);
    }
    auto idx = dynamic_cast<Integer*>(index)->value();
    if (idx < 0 || static_cast<size_t>(idx) >= str->value().size()) {
      throwWithLocation("IndexOutOfBounds", instruction.src_loc);
    }
    machine.push(machine.allocate<String>(std::string(1, str->value()[static_cast<size_t>(idx)])));
  } else if (obj->type() == ObjectType::Map) {
    auto* map = dynamic_cast<Map*>(obj);
    auto* value = map->get(machine, index);
    if (value == nullptr) {
      machine.push(machine.allocate<Null>());
    } else {
      machine.push(value);
    }
  } else if (obj->type() == ObjectType::Null) {
    throwWithLocation("NullAccess: cannot index null", instruction.src_loc);
  } else {
    throwWithLocation("TypeError: cannot index this type", instruction.src_loc);
  }
}

static inline void indexSet(Machine& machine, const Instruction& instruction) {
  auto* value = machine.pop();
  auto* index = machine.pop();
  auto* obj = machine.pop();
  if (obj->type() == ObjectType::Vec) {
    auto* vec = dynamic_cast<Vec*>(obj);
    if (index->type() != ObjectType::Integer) {
      throwWithLocation("TypeError: vec index must be an integer", instruction.src_loc);
    }
    auto idx = dynamic_cast<Integer*>(index)->value();
    vec->set(idx, value);
    machine.push(value);
  } else if (obj->type() == ObjectType::Map) {
    auto* map = dynamic_cast<Map*>(obj);
    map->set(machine, index, value);
    machine.push(value);
  } else if (obj->type() == ObjectType::Null) {
    throwWithLocation("NullAccess: cannot index null", instruction.src_loc);
  } else {
    throwWithLocation("TypeError: cannot index-assign this type", instruction.src_loc);
  }
}

static inline void pop(Machine& machine, [[maybe_unused]] const Instruction& instruction) {
  machine.pop();
}

static inline void loadUpvalue(Machine& machine, const Instruction& instruction) {
  auto* upval = machine.getCurrentFunction()->getUpvalue(instruction.imm);
  if (upval == nullptr || upval->type() != ObjectType::Upvalue) {
    throwWithLocation("Upvalue not found", instruction.src_loc);
  }
  machine.push(dynamic_cast<Upvalue*>(upval)->get());
}

static inline void storeUpvalue(Machine& machine, const Instruction& instruction) {
  auto* value = machine.pop();
  auto* upval = machine.getCurrentFunction()->getUpvalue(instruction.imm);
  if (upval == nullptr || upval->type() != ObjectType::Upvalue) {
    throwWithLocation("Upvalue not found", instruction.src_loc);
  }
  dynamic_cast<Upvalue*>(upval)->set(value);
}

static inline void jump(Machine& machine, const Instruction& instruction) {
  machine.setIP(instruction.imm);
}

static inline void jumpIfFalse(Machine& machine, const Instruction& instruction) {
  auto* value = machine.pop();
  if (!value->isTruthy()) {
    machine.setIP(instruction.imm);
  }
}

static inline void negate(Machine& machine, const Instruction& instruction) {
  auto* operand = machine.pop();
  auto* result = operand->negate(machine);
  if (result == nullptr) {
    throwWithLocation("Cannot negate this type", instruction.src_loc);
  }
  machine.push(result);
}

static inline void logicalNot(Machine& machine, [[maybe_unused]] const Instruction& instruction) {
  auto* operand = machine.pop();
  machine.push(machine.allocate<Boolean>(!operand->isTruthy()));
}

static inline void eq(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->eq(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type for ==", instruction.src_loc);
  }
  machine.push(result);
}

static inline void neq(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  auto* eq_result = lhs->eq(machine, rhs);
  if (eq_result == nullptr) {
    throwWithLocation("Invalid operand type for !=", instruction.src_loc);
  }
  auto* bool_result = dynamic_cast<Boolean*>(eq_result);
  machine.push(machine.allocate<Boolean>(!bool_result->value()));
}

static inline void lt(Machine& machine, const Instruction& instruction) {
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = lhs->lt(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type for <", instruction.src_loc);
  }
  machine.push(result);
}

static inline void gt(Machine& machine, const Instruction& instruction) {
  // a > b  is  b < a
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  const auto result = rhs->lt(machine, lhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type for >", instruction.src_loc);
  }
  machine.push(result);
}

static inline void lte(Machine& machine, const Instruction& instruction) {
  // a <= b  is  !(b < a)
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  auto* gt_result = rhs->lt(machine, lhs);
  if (gt_result == nullptr) {
    throwWithLocation("Invalid operand type for <=", instruction.src_loc);
  }
  auto* bool_result = dynamic_cast<Boolean*>(gt_result);
  machine.push(machine.allocate<Boolean>(!bool_result->value()));
}

static inline void gte(Machine& machine, const Instruction& instruction) {
  // a >= b  is  !(a < b)
  const auto rhs = machine.pop();
  const auto lhs = machine.pop();
  auto* lt_result = lhs->lt(machine, rhs);
  if (lt_result == nullptr) {
    throwWithLocation("Invalid operand type for >=", instruction.src_loc);
  }
  auto* bool_result = dynamic_cast<Boolean*>(lt_result);
  machine.push(machine.allocate<Boolean>(!bool_result->value()));
}

using InstructionHandler = void (*)(Machine&, const Instruction&);
static std::unordered_map<Opcode, InstructionHandler> instruction_handlers = {
    {Opcode::LOAD_GLOBAL, loadGlobal},
    {Opcode::STORE_GLOBAL, storeGlobal},
    {Opcode::LOAD_CONST, loadConst},
    {Opcode::STORE_LOCAL, storeLocal},
    {Opcode::LOAD_LOCAL, loadLocal},
    {Opcode::CALL, callFunction},
    {Opcode::RETURN_CONST, returnConst},
    {Opcode::RETURN_LOCAL, returnLocal},
    {Opcode::RETURN_VALUE, returnValue},
    {Opcode::ADD, add},
    {Opcode::SUB, sub},
    {Opcode::MUL, mul},
    {Opcode::DIV, div},
    {Opcode::MOD, mod},
    {Opcode::GET_FIELD, getField},
    {Opcode::SET_FIELD, setField},
    {Opcode::INDEX_GET, indexGet},
    {Opcode::INDEX_SET, indexSet},
    {Opcode::LOAD_UPVALUE, loadUpvalue},
    {Opcode::STORE_UPVALUE, storeUpvalue},
    {Opcode::POP, pop},
    {Opcode::POW, power},
    {Opcode::SHL, shl},
    {Opcode::SHR, shr},
    {Opcode::BIT_AND, bitAnd},
    {Opcode::BIT_XOR, bitXor},
    {Opcode::BIT_OR, bitOr},
    {Opcode::NEGATE, negate},
    {Opcode::NOT, logicalNot},
    {Opcode::JUMP, jump},
    {Opcode::JUMP_IF_FALSE, jumpIfFalse},
    {Opcode::EQ, eq},
    {Opcode::NEQ, neq},
    {Opcode::LT, lt},
    {Opcode::GT, gt},
    {Opcode::LTE, lte},
    {Opcode::GTE, gte}};

void Machine::executeInstruction(const Instruction& instruction) {
  const auto handler = instruction_handlers.at(instruction.opcode);
  handler(*this, instruction);
}
const Instruction& Machine::nextInstruction() {
  auto* function = getCurrentFunction();
  if (!function) {
    throw std::runtime_error("No function to execute");
  }
  const auto ip = call_frames_.back().ip;
  const auto& instr = function->getInstruction(ip);
  call_frames_.back().ip++;
  return instr;
}

// END INSTRUCTION EXECUTION

void Machine::gc() {
  // gather all root objects
  const auto roots = getRoots();
  // mark all objects reachable from roots
  heap_.markFromRoots(roots);
  // sweep unmarked objects
  heap_.sweep();
}

std::vector<BaseObject*> Machine::getRoots() const {
  std::vector<BaseObject*> roots;
  // add globals
  roots.reserve(globals_.size());
for (auto* global : globals_) {
    roots.push_back(global);
  }

  return roots;
}

uint32_t Machine::addGlobal(BaseObject* global) {
  globals_.push_back(global);
  return static_cast<uint32_t>(globals_.size() - 1);
}

BaseObject* Machine::getGlobal(const uint32_t index) const {
  if (index >= globals_.size()) {
    return nullptr;
  }
  return globals_[index];
}

void Machine::setGlobal(const uint32_t index, BaseObject* value) {
  if (index >= globals_.size()) {
    throw std::runtime_error("Global index out of bounds");
  }
  globals_[index] = value;
}

void Machine::pushCallFrame(Function* function) {
  call_frames_.emplace_back(function, getStackPointer());
}

void Machine::popCallFrame() {
  call_frames_.pop_back();
}

void Machine::setIP(size_t ip) {
  call_frames_.back().ip = ip;
}

void Machine::registerNative(const std::string& name, size_t arity,
                             object::NativeFn fn) {
  auto* native =
      allocate<NativeFunction>(name, arity, std::move(fn));
  const auto index = addGlobal(native);
  function_table_[name] = index;
}

void Machine::registerBuiltins() {
  registerNative("println", 1,
                 [](Machine& machine,
                    const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   for (const auto* arg : fn_args) {
                     std::cout << arg->toString();
                   }
                   std::cout << "\n";
                   return machine.allocate<Null>();
                 });

  registerNative("print", 1,
                 [](Machine& machine,
                    const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   for (const auto* arg : fn_args) {
                     std::cout << arg->toString();
                   }
                   return machine.allocate<Null>();
                 });

  registerNative("type", 1,
                 [](Machine& machine,
                    const std::vector<BaseObject*>& args) -> BaseObject* {
                   const auto* obj = args[0];
                   // Map internal names to spec names
                   std::string name;
                   switch (obj->type()) {
                     case ObjectType::Integer: name = "int"; break;
                     case ObjectType::Float: name = "float"; break;
                     case ObjectType::String: name = "string"; break;
                     case ObjectType::Char: name = "char"; break;
                     case ObjectType::Boolean: name = "bool"; break;
                     case ObjectType::Byte: name = "byte"; break;
                     case ObjectType::Null: name = "null"; break;
                     case ObjectType::Object: name = "object"; break;
                     case ObjectType::Vec: name = "vec"; break;
                     case ObjectType::Map: name = "map"; break;
                     case ObjectType::List: name = "list"; break;
                     case ObjectType::Upvalue: name = "upvalue"; break;
                     case ObjectType::Thunk: name = "thunk"; break;
                     case ObjectType::Function:
                     case ObjectType::NativeFunction: name = "function"; break;
                     default: name = "unknown"; break;
                   }
                   return machine.allocate<String>(std::move(name));
                 });

  registerNative("vec", 0,
                 [](Machine& machine,
                    const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   auto* v = machine.allocate<Vec>(
                       std::vector<BaseObject*>(fn_args.begin(), fn_args.end()));
                   return v;
                 });

  registerNative("map", 0,
                 [](Machine& machine,
                    [[maybe_unused]] const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   return machine.allocate<Map>();
                 });

  registerNative("len", 1,
                 [](Machine& machine,
                    const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   auto* obj = fn_args[0];
                   if (obj->type() == ObjectType::Vec) {
                     return machine.allocate<Integer>(
                         static_cast<int64_t>(dynamic_cast<Vec*>(obj)->length()));
                   }
                   if (obj->type() == ObjectType::String) {
                     return machine.allocate<Integer>(
                         static_cast<int64_t>(dynamic_cast<String*>(obj)->value().size()));
                   }
                   if (obj->type() == ObjectType::Map) {
                     return machine.allocate<Integer>(
                         static_cast<int64_t>(dynamic_cast<Map*>(obj)->length()));
                   }
                   if (obj->type() == ObjectType::List) {
                     return machine.allocate<Integer>(
                         static_cast<int64_t>(dynamic_cast<ListNode*>(obj)->length()));
                   }
                   if (obj->type() == ObjectType::Null) {
                     return machine.allocate<Integer>(0);  // empty list
                   }
                   throw std::runtime_error("TypeError: len() not supported for this type");
                 });

  registerNative("push", 2,
                 [](Machine& machine,
                    const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   if (fn_args[0]->type() != ObjectType::Vec) {
                     throw std::runtime_error("TypeError: push() requires a vec");
                   }
                   dynamic_cast<Vec*>(fn_args[0])->push(fn_args[1]);
                   return machine.allocate<Null>();
                 });

  registerNative("pop", 1,
                 []([[maybe_unused]] Machine& machine,
                    const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   if (fn_args[0]->type() != ObjectType::Vec) {
                     throw std::runtime_error("TypeError: pop() requires a vec");
                   }
                   return dynamic_cast<Vec*>(fn_args[0])->pop();
                 });

  registerNative("byte", 1,
                 [](Machine& machine,
                    const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   if (fn_args[0]->type() == ObjectType::Integer) {
                     auto val = dynamic_cast<Integer*>(fn_args[0])->value();
                     return machine.allocate<Byte>(static_cast<uint8_t>(val & 0xFF));
                   }
                   throw std::runtime_error("TypeError: byte() expects an integer");
                 });

  registerNative("list", 0,
                 [](Machine& machine,
                    const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   if (fn_args.empty()) {
                     return machine.allocate<Null>();
                   }
                   // Build linked list from args (right to left)
                   BaseObject* tail = machine.allocate<Null>();
                   for (auto it = fn_args.rbegin(); it != fn_args.rend(); ++it) {
                     tail = machine.allocate<ListNode>(*it, tail);
                   }
                   return tail;
                 });

  registerNative("head", 1,
                 []([[maybe_unused]] Machine& machine,
                    const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   if (fn_args[0]->type() != ObjectType::List) {
                     throw std::runtime_error("TypeError: head() requires a list");
                   }
                   return dynamic_cast<ListNode*>(fn_args[0])->head();
                 });

  registerNative("tail", 1,
                 []([[maybe_unused]] Machine& machine,
                    const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   if (fn_args[0]->type() != ObjectType::List) {
                     throw std::runtime_error("TypeError: tail() requires a list");
                   }
                   return dynamic_cast<ListNode*>(fn_args[0])->tail();
                 });

  registerNative("cons", 2,
                 [](Machine& machine,
                    const std::vector<BaseObject*>& fn_args) -> BaseObject* {
                   return machine.allocate<ListNode>(fn_args[0], fn_args[1]);
                 });

  registerNative("throw_err", 1,
                 []([[maybe_unused]] Machine& machine,
                    const std::vector<BaseObject*>& args) -> BaseObject* {
                   throw std::runtime_error(args[0]->toString());
                 });
}

}  // namespace vulpes::vm
