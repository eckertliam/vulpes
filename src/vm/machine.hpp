#pragma once

#include "call_frame.hpp"
#include "heap.hpp"
#include "instruction.hpp"
#include "object/native_function.hpp"

#include <stack>
#include <unordered_map>
#include <unordered_set>

namespace vulpes::vm {

static constexpr size_t STACK_SIZE = 1024;

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
  Function* buildFunction(const std::string_view name, size_t arity);

  // Add a global and return the index
  uint32_t addGlobal(BaseObject* global);
  // Get a global by index
  [[nodiscard]] BaseObject* getGlobal(uint32_t index) const;
  // Set a value at a global index
  void setGlobal(uint32_t index, BaseObject* value);

  // Get the function table for code generation
  [[nodiscard]] const std::unordered_map<std::string, uint32_t>& getFunctionTable() const {
    return function_table_;
  }

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
  void setIP(size_t ip);

  void registerBuiltins();
  void registerNative(const std::string& name, size_t arity, object::NativeFn fn);

  // Module system
  using ModuleLoader = std::function<bool(Machine&, const std::string&)>;
  void setBaseDir(const std::string& dir) { base_dir_ = dir; }
  [[nodiscard]] const std::string& getBaseDir() const { return base_dir_; }
  void setModuleLoader(ModuleLoader loader) { module_loader_ = std::move(loader); }
  bool loadModule(const std::string& module_path);
  [[nodiscard]] bool isModuleLoaded(const std::string& module_path) const;
  [[nodiscard]] bool isModuleLoading(const std::string& module_path) const;
  void markModuleLoaded(const std::string& module_path);
  void markModuleLoading(const std::string& module_path);
  void unmarkModuleLoading(const std::string& module_path);

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
  std::string base_dir_;
  ModuleLoader module_loader_;
  std::unordered_set<std::string> loaded_modules_;
  std::unordered_set<std::string> loading_modules_;  // for cycle detection

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
