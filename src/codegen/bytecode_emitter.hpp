#pragma once

#include "frontend/ast.hpp"
#include "vm/machine.hpp"
#include "vm/object/function.hpp"
#include <optional>
#include <unordered_map>
#include <vector>

namespace vulpes::codegen {

// Tracks break/continue jump targets for the current loop
struct LoopContext {
  uint32_t continue_target;                  // instruction index for continue
  std::vector<uint32_t> break_patches;       // JUMP indices to patch when loop ends
};

class BytecodeEmitter : public frontend::AstVisitor {
 private:
  vm::Machine& machine;
  vm::object::Function* current_function;

  // Symbol tables for code generation
  std::vector<std::unordered_map<std::string_view, uint32_t>> scope_stack;
  uint32_t next_local_index = 0;
  std::unordered_map<std::string_view, uint32_t> args;
  std::unordered_map<std::string_view, uint32_t> constants;

  // Track whether we're in the top-level entry function
  bool in_top_level = false;
  // Top-level global variable name -> global index mapping
  std::unordered_map<std::string_view, uint32_t> global_vars;

  // Loop context stack for break/continue
  std::vector<LoopContext> loop_stack;
  
  // Scope helpers
  [[nodiscard]] std::optional<uint32_t> find_local(std::string_view name) const;

  // Helper methods for bytecode generation
  void emit_constant(vm::object::BaseObject* value);
  void emit_load_local(std::string_view name);
  void emit_store_local(std::string_view name);
  void emit_declare_local(std::string_view name);
  void emit_load_arg(std::string_view name);
  void emit_store_arg(std::string_view name);
  void emit_binary_op(const frontend::Token& op);
  void emit_unary_op(const frontend::Token& op);
  void emit_jump(size_t offset);
  void emit_jump_if_false(size_t offset);
  void emit_call(size_t arg_count);
  void emit_return();
  void emit_return_constant(vm::object::BaseObject* value);
  void emit_return_local(std::string_view name);
  void emit_return_value();
  
  // Helper to detect if an expression is a constant
  vm::object::BaseObject* try_get_constant(const frontend::Expr& expr);

 public:
  explicit BytecodeEmitter(vm::Machine& machine) 
      : machine(machine), current_function(nullptr) {}
  
  // Main entry point for code generation
  vm::object::Function* emit_program(const std::vector<std::unique_ptr<frontend::Stmt>>& statements);
  
  // AstVisitor implementation - Expression visitors
  void visit(const frontend::IntegerLiteral& expr) override;
  void visit(const frontend::FloatLiteral& expr) override;
  void visit(const frontend::StringLiteral& expr) override;
  void visit(const frontend::CharLiteral& expr) override;
  void visit(const frontend::BoolLiteral& expr) override;
  void visit(const frontend::NullLiteral& expr) override;
  void visit(const frontend::UnaryExpr& expr) override;
  void visit(const frontend::BinaryExpr& expr) override;
  void visit(const frontend::GroupingExpr& expr) override;
  void visit(const frontend::VarExpr& expr) override;
  void visit(const frontend::AssignExpr& expr) override;
  void visit(const frontend::LogicalExpr& expr) override;
  void visit(const frontend::CallExpr& expr) override;
  void visit(const frontend::IndexExpr& expr) override;
  void visit(const frontend::IndexSetExpr& expr) override;
  void visit(const frontend::GetExpr& expr) override;
  void visit(const frontend::SetExpr& expr) override;
  
  // AstVisitor implementation - Statement visitors
  void visit(const frontend::ExpressionStmt& stmt) override;
  void visit(const frontend::LetStmt& stmt) override;
  void visit(const frontend::ConstStmt& stmt) override;
  void visit(const frontend::BlockStmt& stmt) override;
  void visit(const frontend::IfStmt& stmt) override;
  void visit(const frontend::WhileStmt& stmt) override;
  void visit(const frontend::ForStmt& stmt) override;
  void visit(const frontend::ReturnStmt& stmt) override;
  void visit(const frontend::BreakStmt& stmt) override;
  void visit(const frontend::ContinueStmt& stmt) override;
  void visit(const frontend::FunctionStmt& stmt) override;
  void visit(const frontend::EnumStmt& stmt) override;
  void visit(const frontend::StructStmt& stmt) override;
  void visit(const frontend::ImportStmt& stmt) override;
  void visit(const frontend::ExportStmt& stmt) override;
  void visit(const frontend::ClassStmt& stmt) override;
};

}  // namespace vulpes::codegen
