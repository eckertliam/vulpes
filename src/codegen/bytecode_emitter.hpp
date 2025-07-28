#pragma once

#include "frontend/ast.hpp"
#include "vm/machine.hpp"
#include "vm/object/function.hpp"
#include <unordered_map>

namespace vulpes::codegen {

class BytecodeEmitter : public frontend::AstVisitor {
 private:
  vm::Machine& machine;
  vm::object::Function* current_function;
  
  // Symbol tables for code generation
  std::unordered_map<std::string_view, uint32_t> locals;
  std::unordered_map<std::string_view, uint32_t> args;
  std::unordered_map<std::string_view, uint32_t> constants;
  
  // Helper methods for bytecode generation
  void emit_constant(vm::object::BaseObject* value);
  void emit_load_local(std::string_view name);
  void emit_store_local(std::string_view name);
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
  void visit(const frontend::FunctionStmt& stmt) override;
  void visit(const frontend::ClassStmt& stmt) override;
};

}  // namespace vulpes::codegen