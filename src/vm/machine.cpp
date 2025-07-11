#include "machine.hpp"
#include <string>
#include "vm/instruction.hpp"
#include "vm/object/integer.hpp"

namespace vulpes::vm {

using namespace object;

Function* Machine::getCurrentFunction() const {
  return call_frames_.top().function;
}

void Machine::run() {
  // TODO: implement
}

Function* Machine::buildFunction(const std::string& name, size_t arity) {
  // create a new function
  auto function = allocate<Function>(name, arity);
  // push the function to the global table
  auto index = addGlobal(function);
  // add the function to the function table
  function_table_[name] = index;
  // return the function
  return function;
}

uint32_t Machine::getStackPointer() const {
  return call_frames_.top().sp;
}

void Machine::incrStackPointer() {
  call_frames_.top().sp++;
}

void Machine::decrStackPointer() {
  call_frames_.top().sp--;
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
  auto object = stack_[getStackPointer()];
  return object;
}

BaseObject* Machine::peek(size_t offset) {
  if (getStackPointer() - offset < 0) [[unlikely]] {
    throw std::runtime_error("Stack underflow");
  }
  return stack_[getStackPointer() - offset];
}

// BEGIN INSTRUCTION EXECUTION
static inline void throwWithLocation(const std::string& message,
                                     const std::optional<Location>& src_loc) {
  if (src_loc.has_value()) {
    throw std::runtime_error(message + ": " + src_loc.value().toString());
  }
  throw std::runtime_error(message);
}

static inline void loadGlobal(Machine& machine,
                              const Instruction& instruction) {
  auto global = machine.getGlobal(instruction.imm);
  if (global == nullptr) {
    throwWithLocation("Global not found", instruction.src_loc);
  }
  machine.push(global);
}

static inline void storeGlobal(Machine& machine,
                               const Instruction& instruction) {
  // pop the value from the stack
  auto value = machine.pop();
  // store the value at the global index
  machine.setGlobal(instruction.imm, value);
}

static inline void loadConst(Machine& machine, const Instruction& instruction) {
  auto constant = machine.getCurrentFunction()->getConstant(instruction.imm);
  if (constant == nullptr) {
    throwWithLocation("Constant not found", instruction.src_loc);
  }
  machine.push(constant);
}

static inline void storeLocal(Machine& machine,
                              const Instruction& instruction) {
  // pop the value from the stack
  auto value = machine.pop();
  // store the value at the local index
  auto local_index = machine.getCurrentFunction()->addLocal(value);
  // allocate the local index as an integer
  auto local_index_obj = machine.allocate<Integer>(local_index);
  // push the local index to the stack
  machine.push(local_index_obj);
}

static inline void loadLocal(Machine& machine, const Instruction& instruction) {
  // get the local from the function
  auto local = machine.getCurrentFunction()->getLocal(instruction.imm);
  if (local == nullptr) {
    throwWithLocation("Local not found", instruction.src_loc);
  }
  // push the local to the stack
  machine.push(local);
}

static inline void callFunction(Machine& machine,
                                const Instruction& instruction) {
  // pop the function from the stack
  auto functionObj = machine.pop();
  // NOTE: in the future this will be more flexible
  if (functionObj->type() != ObjectType::Function) {
    throwWithLocation("Expected function object", instruction.src_loc);
  }
  // cast the function object to a function
  auto function = static_cast<Function*>(functionObj);
  // get the number of arguments
  auto arity = function->getArity();
  // pop the args from the stack and save them to local slots
  for (size_t i = 0; i < arity; i++) {
    auto arg = machine.pop();
    machine.getCurrentFunction()->addLocal(arg);
  }
  // make a new call frame
  machine.pushCallFrame(function);
}

static inline void returnConst(Machine& machine,
                               const Instruction& instruction) {
  // pop the constant from the stack
  auto constant = machine.getCurrentFunction()->getConstant(instruction.imm);
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
  auto local = machine.getCurrentFunction()->getLocal(instruction.imm);
  if (local == nullptr) {
    throwWithLocation("Local not found", instruction.src_loc);
  }
  // pop back to the previous call frame
  machine.popCallFrame();
  // push the local to the stack
  machine.push(local);
}

static inline void returnValue(Machine& machine,
                               const Instruction& instruction) {
  // pop the value from the stack
  auto value = machine.pop();
  // pop back to the previous call frame
  machine.popCallFrame();
  // push the value to the stack
  machine.push(value);
}

static inline void add(Machine& machine, const Instruction& instruction) {
  auto rhs = machine.pop();
  auto lhs = machine.pop();
  auto result = lhs->add(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type", instruction.src_loc);
  }
  machine.push(result);
}

static inline void sub(Machine& machine, const Instruction& instruction) {
  auto rhs = machine.pop();
  auto lhs = machine.pop();
  auto result = lhs->sub(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type", instruction.src_loc);
  }
  machine.push(result);
}

static inline void mul(Machine& machine, const Instruction& instruction) {
  auto rhs = machine.pop();
  auto lhs = machine.pop();
  auto result = lhs->mul(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type", instruction.src_loc);
  }
  machine.push(result);
}

static inline void div(Machine& machine, const Instruction& instruction) {
  auto rhs = machine.pop();
  auto lhs = machine.pop();
  auto result = lhs->div(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type", instruction.src_loc);
  }
  machine.push(result);
}

static inline void mod(Machine& machine, const Instruction& instruction) {
  auto rhs = machine.pop();
  auto lhs = machine.pop();
  auto result = lhs->mod(machine, rhs);
  if (result == nullptr) {
    throwWithLocation("Invalid operand type", instruction.src_loc);
  }
  machine.push(result);
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
    {Opcode::MOD, mod}};

void Machine::executeInstruction(Instruction instruction) {
  auto handler = instruction_handlers.at(instruction.opcode);
  handler(*this, instruction);
}

// END INSTRUCTION EXECUTION

void Machine::gc() {
  // gather all root objects
  auto roots = getRoots();
  // mark all objects reachable from roots
  heap_.markFromRoots(roots);
  // sweep unmarked objects
  heap_.sweep();
}

std::vector<BaseObject*> Machine::getRoots() {
  std::vector<BaseObject*> roots;
  // add globals
  for (auto* global : globals_) {
    roots.push_back(global);
  }

  return roots;
}

uint32_t Machine::addGlobal(BaseObject* global) {
  globals_.push_back(global);
  return globals_.size() - 1;
}

BaseObject* Machine::getGlobal(uint32_t index) {
  if (index >= globals_.size()) {
    return nullptr;
  }
  return globals_[index];
}

void Machine::setGlobal(uint32_t index, BaseObject* value) {
  if (index >= globals_.size()) {
    throw std::runtime_error("Global index out of bounds");
  }
  globals_[index] = value;
}

void Machine::pushCallFrame(Function* function) {
  call_frames_.push(CallFrame(function, getStackPointer()));
}

void Machine::popCallFrame() {
  call_frames_.pop();
}

}  // namespace vulpes::vm