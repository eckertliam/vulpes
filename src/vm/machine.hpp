#pragma once

#include "call_frame.hpp"
#include "heap.hpp"
#include "instruction.hpp"

#include <stack>

namespace vulpes::vm {

#define STACK_SIZE 1024

class Machine {
 public:
  Machine()
      : heap_(), globals_(), function_table_(), call_frames_(), stack_() {}

  ~Machine() = default;

  void run();

  // Used for building functions from the frontend
  // Builds a hollow function and returns its pointer
  // Also enters the function into the function table
  // The function is not yet compiled, and the instructions are empty
  Function* buildFunction(const std::string& name, size_t arity);

  // Add a global and return the index
  uint32_t addGlobal(BaseObject* global);
  // Get a global by index
  [[nodiscard]] BaseObject* getGlobal(uint32_t index) const;
  // Set a value at a global index
  void setGlobal(uint32_t index, BaseObject* value);

  void push(BaseObject* object);
  BaseObject* pop();

  [[nodiscard]] Function* getCurrentFunction() const;

  [[nodiscard]] uint32_t getStackPointer() const;

  template <typename T, typename... Args>
  T* allocate(Args&&... args) {
    return heap_.allocate<T>(std::forward<Args>(args)...);
  }

  void pushCallFrame(Function* function);
  void popCallFrame();

  // peek pack with offset from the top of the stack
  // used for loading args into functions from previous call frames
  [[nodiscard]] BaseObject* peek(size_t offset = 0) const;
  [[nodiscard]] BaseObject* peek() const;

 private:
  Heap heap_;
  std::vector<BaseObject*> globals_;
  std::unordered_map<std::string, uint32_t> function_table_;
  std::deque<CallFrame> call_frames_;
  std::array<BaseObject*, STACK_SIZE> stack_;

  void incrStackPointer();
  void decrStackPointer();

  void executeInstruction(const Instruction& instruction);
 const Instruction& nextInstruction();

  /* Garbage collection */
  void gc();

  // Returns all objects that are reachable from the roots.
  // Including global variables, functions, etc.
  [[nodiscard]] std::vector<BaseObject*> getRoots() const;
};
}  // namespace vulpes::vm