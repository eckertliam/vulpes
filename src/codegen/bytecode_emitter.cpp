#include "bytecode_emitter.hpp"
#include <cstdint>
#include "vm/object/null.hpp"
#include "vm/object/integer.hpp"
#include "vm/object/float.hpp"
#include "vm/object/function.hpp"
#include "vm/object/string.hpp"
#include "vm/object/boolean.hpp"

namespace vulpes::codegen {

vm::object::Function* BytecodeEmitter::emit_program(const std::vector<std::unique_ptr<frontend::Stmt>>& statements) {
    current_function = machine.buildFunction("__entry__", 0);
    scope_stack.clear();
    scope_stack.emplace_back();
    next_local_index = 0;

    for (const auto& stmt : statements) {
        stmt->accept(*this);
    }

    // Auto-call main() if it was defined
    auto main_it = machine.getFunctionTable().find("main");
    if (main_it != machine.getFunctionTable().end()) {
        current_function->addInstruction(vm::Instruction(vm::Opcode::LOAD_GLOBAL, main_it->second));
        current_function->addInstruction(vm::Instruction(vm::Opcode::CALL));
        current_function->addInstruction(vm::Instruction(vm::Opcode::POP));
    }

    current_function->addInstruction(vm::Instruction(vm::Opcode::EOP));

    return current_function;
}

void BytecodeEmitter::emit_constant(vm::object::BaseObject* value) {
    // Add the constant to the function's constant pool
    uint32_t constant_index = current_function->addConstant(value);
    // Emit LOAD_CONST instruction
    current_function->addInstruction(vm::Instruction(vm::Opcode::LOAD_CONST, constant_index));
}

// Look up a local variable in the scope stack (innermost first)
std::optional<uint32_t> BytecodeEmitter::find_local(std::string_view name) const {
    for (auto it = scope_stack.rbegin(); it != scope_stack.rend(); ++it) {
        auto found = it->find(name);
        if (found != it->end()) {
            return found->second;
        }
    }
    return std::nullopt;
}

void BytecodeEmitter::emit_load_local(std::string_view name) {
    auto index = find_local(name);
    if (index) {
        current_function->addInstruction(vm::Instruction(vm::Opcode::LOAD_LOCAL, *index));
    } else {
        // TODO: Handle undefined variable error
    }
}

void BytecodeEmitter::emit_store_local(std::string_view name) {
    auto index = find_local(name);
    if (index) {
        current_function->addInstruction(vm::Instruction(vm::Opcode::STORE_LOCAL, *index));
    } else {
        emit_declare_local(name);
    }
}

void BytecodeEmitter::emit_declare_local(std::string_view name) {
    // Always allocate a new slot in the current (innermost) scope
    uint32_t new_index = next_local_index++;
    scope_stack.back()[name] = new_index;
    current_function->addInstruction(vm::Instruction(vm::Opcode::STORE_LOCAL, new_index));
}

void BytecodeEmitter::emit_load_arg(std::string_view name) {
    auto it = args.find(name);
    if (it != args.end()) {
        current_function->addInstruction(vm::Instruction(vm::Opcode::LOAD_LOCAL, it->second));
    } else {
        // TODO: Handle undefined argument error
    }
}

void BytecodeEmitter::emit_store_arg(std::string_view name) {
    auto it = args.find(name);
    if (it != args.end()) {
        current_function->addInstruction(vm::Instruction(vm::Opcode::STORE_LOCAL, it->second));
    } else {
        // TODO: Handle undefined argument error
    }
}

void BytecodeEmitter::emit_binary_op(const frontend::Token& op) {
    if (op.lexeme() == "+") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::ADD));
    } else if (op.lexeme() == "-") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::SUB));
    } else if (op.lexeme() == "*") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::MUL));
    } else if (op.lexeme() == "/") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::DIV));
    } else if (op.lexeme() == "%") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::MOD));
    } else if (op.lexeme() == "==") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::EQ));
    } else if (op.lexeme() == "!=") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::NEQ));
    } else if (op.lexeme() == "<") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::LT));
    } else if (op.lexeme() == ">") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::GT));
    } else if (op.lexeme() == "<=") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::LTE));
    } else if (op.lexeme() == ">=") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::GTE));
    }
}

void BytecodeEmitter::emit_unary_op(const frontend::Token& op) {
    if (op.lexeme() == "-") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::NEGATE));
    } else if (op.lexeme() == "!") {
        current_function->addInstruction(vm::Instruction(vm::Opcode::NOT));
    }
    // unary + is a no-op
}

void BytecodeEmitter::emit_jump([[maybe_unused]] size_t offset) {
    // TODO: Implement jump instruction
    // Current instruction set doesn't support jumps
}

void BytecodeEmitter::emit_jump_if_false([[maybe_unused]] size_t offset) {
    // TODO: Implement conditional jump
    // Current instruction set doesn't support conditional jumps
}

void BytecodeEmitter::emit_call([[maybe_unused]] size_t arg_count) {
    // Emit CALL instruction - function object should already be on stack
    // The VM will pop the function object and arguments from the stack
    current_function->addInstruction(vm::Instruction(vm::Opcode::CALL));
}

void BytecodeEmitter::emit_return() {
    // Emit RETURN_VALUE to pop and return the top value from the stack
    current_function->addInstruction(vm::Instruction(vm::Opcode::RETURN_VALUE));
}

void BytecodeEmitter::emit_return_constant(vm::object::BaseObject* value) {
    // Add the constant to the function's constant pool
    uint32_t constant_index = current_function->addConstant(value);
    // Emit RETURN_CONST instruction
    current_function->addInstruction(vm::Instruction(vm::Opcode::RETURN_CONST, constant_index));
}

void BytecodeEmitter::emit_return_local(std::string_view name) {
    auto it = find_local(name);
    if (it) {
        current_function->addInstruction(vm::Instruction(vm::Opcode::RETURN_LOCAL, *it));
    } else {
        // Fall back to RETURN_VALUE if local not found
        emit_return();
    }
}

void BytecodeEmitter::emit_return_value() {
    // Emit RETURN_VALUE to pop and return the top value from the stack
    current_function->addInstruction(vm::Instruction(vm::Opcode::RETURN_VALUE));
}

vm::object::BaseObject* BytecodeEmitter::try_get_constant(const frontend::Expr& expr) {
    // Check for literal expressions that can be constants
    if (auto* int_lit = dynamic_cast<const frontend::IntegerLiteral*>(&expr)) {
        return machine.allocate<vm::object::Integer>(int_lit->value);
    }
    if (auto* float_lit = dynamic_cast<const frontend::FloatLiteral*>(&expr)) {
        return machine.allocate<vm::object::Float>(float_lit->value);
    }
    if (dynamic_cast<const frontend::NullLiteral*>(&expr)) {
        return machine.allocate<vm::object::Null>();
    }
    if (auto* bool_lit = dynamic_cast<const frontend::BoolLiteral*>(&expr)) {
        return machine.allocate<vm::object::Boolean>(bool_lit->value);
    }
    if (auto* string_lit = dynamic_cast<const frontend::StringLiteral*>(&expr)) {
        return machine.allocate<vm::object::String>(std::string(string_lit->value));
    }
    if (dynamic_cast<const frontend::CharLiteral*>(&expr)) {
        // TODO: Implement char objects
        return machine.allocate<vm::object::Null>();
    }
    
    // For now, only simple literals are considered constants
    // TODO: Could extend this to detect more complex constant expressions
    return nullptr;
}

// Expression visitors
void BytecodeEmitter::visit(const frontend::IntegerLiteral& expr) {
    auto* int_obj = machine.allocate<vm::object::Integer>(expr.value);
    emit_constant(int_obj);
}

void BytecodeEmitter::visit(const frontend::FloatLiteral& expr) {
    auto* float_obj = machine.allocate<vm::object::Float>(expr.value);
    emit_constant(float_obj);
}

void BytecodeEmitter::visit(const frontend::StringLiteral& expr) {
    auto* str_obj = machine.allocate<vm::object::String>(std::string(expr.value));
    emit_constant(str_obj);
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::CharLiteral& expr) {
    // TODO: Implement char literal emission
    auto* null_obj = machine.allocate<vm::object::Null>();
    emit_constant(null_obj);
}

void BytecodeEmitter::visit(const frontend::BoolLiteral& expr) {
    auto* bool_obj = machine.allocate<vm::object::Boolean>(expr.value);
    emit_constant(bool_obj);
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::NullLiteral& expr) {
    auto* null_obj = machine.allocate<vm::object::Null>();
    emit_constant(null_obj);
}

void BytecodeEmitter::visit(const frontend::UnaryExpr& expr) {
    // Visit the right operand first
    expr.right->accept(*this);
    // Then emit the unary operator
    emit_unary_op(expr.op);
}

void BytecodeEmitter::visit(const frontend::BinaryExpr& expr) {
    // Visit left operand first
    expr.left->accept(*this);
    // Visit right operand
    expr.right->accept(*this);
    // Emit binary operator
    emit_binary_op(expr.op);
}

void BytecodeEmitter::visit(const frontend::GroupingExpr& expr) {
    // Just visit the inner expression
    expr.expr->accept(*this);
}

void BytecodeEmitter::visit(const frontend::VarExpr& expr) {
    // Try locals (scope stack), then args, then globals
    auto local_idx = find_local(expr.name);
    if (local_idx) {
        emit_load_local(expr.name);
    } else {
        auto arg_it = args.find(expr.name);
        if (arg_it != args.end()) {
            emit_load_arg(expr.name);
        } else {
            auto global_it = machine.getFunctionTable().find(std::string(expr.name));
            if (global_it != machine.getFunctionTable().end()) {
                current_function->addInstruction(vm::Instruction(vm::Opcode::LOAD_GLOBAL, global_it->second));
            }
        }
    }
}

void BytecodeEmitter::visit(const frontend::AssignExpr& expr) {
    expr.value->accept(*this);
    // Store and reload (assignment is an expression that leaves value on stack)
    auto local_idx = find_local(expr.name);
    if (local_idx) {
        emit_store_local(expr.name);
        emit_load_local(expr.name);
    } else {
        auto arg_it = args.find(expr.name);
        if (arg_it != args.end()) {
            emit_store_arg(expr.name);
            emit_load_arg(expr.name);
        } else {
            emit_store_local(expr.name);
            emit_load_local(expr.name);
        }
    }
}

void BytecodeEmitter::visit(const frontend::LogicalExpr& expr) {
    if (expr.op.lexeme() == "&&") {
        // Short-circuit AND: if left is falsy, skip right and push false
        expr.left->accept(*this);
        auto false_jump = current_function->instructionCount();
        current_function->addInstruction(vm::Instruction(vm::Opcode::JUMP_IF_FALSE, 0));

        // Left was truthy — evaluate right (its value is the result)
        expr.right->accept(*this);
        auto end_jump = current_function->instructionCount();
        current_function->addInstruction(vm::Instruction(vm::Opcode::JUMP, 0));

        // Short-circuit: push false
        current_function->patchInstruction(false_jump, current_function->instructionCount());
        auto* false_obj = machine.allocate<vm::object::Boolean>(false);
        emit_constant(false_obj);

        current_function->patchInstruction(end_jump, current_function->instructionCount());
    } else if (expr.op.lexeme() == "||") {
        // Short-circuit OR: if left is truthy, skip right and push true
        expr.left->accept(*this);
        // NOT + JUMP_IF_FALSE = jump if truthy
        current_function->addInstruction(vm::Instruction(vm::Opcode::NOT));
        auto true_jump = current_function->instructionCount();
        current_function->addInstruction(vm::Instruction(vm::Opcode::JUMP_IF_FALSE, 0));

        // Left was falsy — evaluate right (its value is the result)
        expr.right->accept(*this);
        auto end_jump = current_function->instructionCount();
        current_function->addInstruction(vm::Instruction(vm::Opcode::JUMP, 0));

        // Short-circuit: push true
        current_function->patchInstruction(true_jump, current_function->instructionCount());
        auto* true_obj = machine.allocate<vm::object::Boolean>(true);
        emit_constant(true_obj);

        current_function->patchInstruction(end_jump, current_function->instructionCount());
    }
}

void BytecodeEmitter::visit(const frontend::CallExpr& expr) {
    // Visit all arguments first (in reverse order for stack-based calling)
    for (auto it = expr.arguments.rbegin(); it != expr.arguments.rend(); ++it) {
        (*it)->accept(*this);
    }
    // Visit the callee
    expr.callee->accept(*this);
    // Emit call instruction
    emit_call(expr.arguments.size());
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::IndexExpr& expr) {
    // TODO: Implement index access
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::IndexSetExpr& expr) {
    // TODO: Implement index assignment
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::GetExpr& expr) {
    // TODO: Implement property access
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::SetExpr& expr) {
    // TODO: Implement property assignment
}

// Statement visitors
void BytecodeEmitter::visit(const frontend::ExpressionStmt& stmt) {
    stmt.expr->accept(*this);
    // Pop the result of the expression
    current_function->addInstruction(vm::Instruction(vm::Opcode::POP));
}

void BytecodeEmitter::visit(const frontend::LetStmt& stmt) {
    if (stmt.initializer) {
        stmt.initializer->accept(*this);
    } else {
        // Initialize with null
        auto* null_obj = machine.allocate<vm::object::Null>();
        emit_constant(null_obj);
    }
    emit_declare_local(stmt.name);
}

void BytecodeEmitter::visit(const frontend::ConstStmt& stmt) {
    if (stmt.initializer) {
        stmt.initializer->accept(*this);
    } else {
        // TODO: Error - const must be initialized
        auto* null_obj = machine.allocate<vm::object::Null>();
        emit_constant(null_obj);
    }
    emit_declare_local(stmt.name);
}

void BytecodeEmitter::visit(const frontend::BlockStmt& stmt) {
    scope_stack.emplace_back();
    for (const auto& statement : stmt.statements) {
        statement->accept(*this);
    }
    scope_stack.pop_back();
}

void BytecodeEmitter::visit(const frontend::IfStmt& stmt) {
    // Emit condition
    stmt.condition->accept(*this);

    // Emit JUMP_IF_FALSE with placeholder
    auto jump_if_false_idx = current_function->instructionCount();
    current_function->addInstruction(vm::Instruction(vm::Opcode::JUMP_IF_FALSE, 0));

    // Emit then branch
    stmt.then_branch->accept(*this);

    if (stmt.else_branch) {
        // Emit JUMP to skip else branch (placeholder)
        auto jump_over_else_idx = current_function->instructionCount();
        current_function->addInstruction(vm::Instruction(vm::Opcode::JUMP, 0));

        // Patch JUMP_IF_FALSE to jump here (start of else)
        current_function->patchInstruction(jump_if_false_idx, current_function->instructionCount());

        // Emit else branch
        stmt.else_branch->accept(*this);

        // Patch JUMP to skip past else
        current_function->patchInstruction(jump_over_else_idx, current_function->instructionCount());
    } else {
        // Patch JUMP_IF_FALSE to jump past then
        current_function->patchInstruction(jump_if_false_idx, current_function->instructionCount());
    }
}

void BytecodeEmitter::visit(const frontend::WhileStmt& stmt) {
    // Loop start — condition is re-evaluated here
    auto loop_start = current_function->instructionCount();

    // Push loop context
    loop_stack.push_back({loop_start, {}});

    // Emit condition
    stmt.condition->accept(*this);

    // Jump past body if false
    auto exit_jump = current_function->instructionCount();
    current_function->addInstruction(vm::Instruction(vm::Opcode::JUMP_IF_FALSE, 0));

    // Emit body
    stmt.body->accept(*this);

    // Jump back to condition
    current_function->addInstruction(vm::Instruction(vm::Opcode::JUMP, loop_start));

    // Patch exit jump
    auto loop_end = current_function->instructionCount();
    current_function->patchInstruction(exit_jump, loop_end);

    // Patch all break jumps
    for (auto break_idx : loop_stack.back().break_patches) {
        current_function->patchInstruction(break_idx, loop_end);
    }

    loop_stack.pop_back();
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::ForStmt& stmt) {
    // TODO: Implement for loop
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::BreakStmt& stmt) {
    // Emit a JUMP placeholder — will be patched when loop ends
    auto break_idx = current_function->instructionCount();
    current_function->addInstruction(vm::Instruction(vm::Opcode::JUMP, 0));
    loop_stack.back().break_patches.push_back(break_idx);
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::ContinueStmt& stmt) {
    // Jump back to loop condition
    current_function->addInstruction(
        vm::Instruction(vm::Opcode::JUMP, loop_stack.back().continue_target));
}

void BytecodeEmitter::visit(const frontend::ReturnStmt& stmt) {
    if (stmt.value) {
        // First check if it's a constant expression
        vm::object::BaseObject* constant = try_get_constant(*stmt.value);
        if (constant) {
            emit_return_constant(constant);
            return;
        }
        
        // Check if the value is a simple variable reference
        if (auto* var_expr = dynamic_cast<const frontend::VarExpr*>(stmt.value.get())) {
            auto local_idx = find_local(var_expr->name);
            if (local_idx) {
                emit_return_local(var_expr->name);
                return;
            }
        }
        
        // For complex expressions, evaluate and return value
        stmt.value->accept(*this);
        emit_return_value();
    } else {
        // Return null constant
        auto* null_obj = machine.allocate<vm::object::Null>();
        emit_return_constant(null_obj);
    }
}

void BytecodeEmitter::visit(const frontend::FunctionStmt& stmt) {
    // Create a new function
    vm::object::Function* fn = machine.buildFunction(stmt.name, stmt.params.size());
    
    // Save current state and switch to new function
    vm::object::Function* prev_function = current_function;
    auto prev_scope_stack = std::move(scope_stack);
    auto prev_next_local = next_local_index;
    auto prev_args = std::move(args);
    auto prev_constants = std::move(constants);

    current_function = fn;
    scope_stack.clear();
    scope_stack.emplace_back();
    next_local_index = 0;
    args.clear();
    constants.clear();

    // Set up argument mapping
    for (size_t i = 0; i < stmt.params.size(); i++) {
        args[stmt.params[i]] = static_cast<uint32_t>(i);
    }
    
    // Visit function body
    stmt.body->accept(*this);

    // Implicit return null at end of function
    auto* null_obj = machine.allocate<vm::object::Null>();
    emit_return_constant(null_obj);
    
    // Restore previous state
    current_function = prev_function;
    scope_stack = std::move(prev_scope_stack);
    next_local_index = prev_next_local;
    args = std::move(prev_args);
    constants = std::move(prev_constants);
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::EnumStmt& stmt) {
    // Enums are backed by integers: each tag gets an integer value starting at 0
    for (size_t i = 0; i < stmt.tags.size(); i++) {
        auto* int_obj = machine.allocate<vm::object::Integer>(static_cast<int64_t>(i));
        emit_constant(int_obj);
        emit_declare_local(stmt.tags[i]);
    }
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::StructStmt& stmt) {
    // TODO: Implement struct definition
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::ImportStmt& stmt) {
    // TODO: Implement module imports
}

void BytecodeEmitter::visit([[maybe_unused]] const frontend::ExportStmt& stmt) {
    // TODO: Implement module exports
}

void BytecodeEmitter::visit(const frontend::ClassStmt& stmt) {
    // TODO: Implement class definition
    for (const auto& method : stmt.methods) {
        method->accept(*this);
    }
}

}  // namespace vulpes::codegen
