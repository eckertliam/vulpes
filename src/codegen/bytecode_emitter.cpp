#include "bytecode_emitter.hpp"
#include <cstdint>
#include "vm/object/null.hpp"
#include "vm/object/integer.hpp"
#include "vm/object/float.hpp"
#include "vm/object/function.hpp"

namespace vulpes::codegen {

vm::object::Function* BytecodeEmitter::emit_program(const std::vector<std::unique_ptr<frontend::Stmt>>& statements) {
    // Create a main function to hold the program
    current_function = machine.buildFunction("main", 0);
    
    // Visit each statement in the program
    for (const auto& stmt : statements) {
        stmt->accept(*this);
    }
    
    // Add a return instruction at the end
    emit_return_value();
    
    return current_function;
}

void BytecodeEmitter::emit_constant(vm::object::BaseObject* value) {
    // Add the constant to the function's constant pool
    uint32_t constant_index = current_function->addConstant(value);
    // Emit LOAD_CONST instruction
    current_function->addInstruction(vm::Instruction(vm::Opcode::LOAD_CONST, constant_index));
}

void BytecodeEmitter::emit_load_local(std::string_view name) {
    auto it = locals.find(name);
    if (it != locals.end()) {
        current_function->addInstruction(vm::Instruction(vm::Opcode::LOAD_LOCAL, it->second));
    } else {
        // TODO: Handle undefined variable error
    }
}

void BytecodeEmitter::emit_store_local(std::string_view name) {
    auto it = locals.find(name);
    if (it != locals.end()) {
        current_function->addInstruction(vm::Instruction(vm::Opcode::STORE_LOCAL, it->second));
    } else {
        // Allocate new local
        uint32_t local_index = locals.size();
        locals[name] = local_index;
        current_function->addInstruction(vm::Instruction(vm::Opcode::STORE_LOCAL, local_index));
    }
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
    }
    // TODO: Implement comparison operators
}

void BytecodeEmitter::emit_unary_op(const frontend::Token& op) {
    // TODO: Implement unary operators (negate, not)
    // Current instruction set doesn't support these
}

void BytecodeEmitter::emit_jump(size_t offset) {
    // TODO: Implement jump instruction
    // Current instruction set doesn't support jumps
}

void BytecodeEmitter::emit_jump_if_false(size_t offset) {
    // TODO: Implement conditional jump
    // Current instruction set doesn't support conditional jumps
}

void BytecodeEmitter::emit_call(size_t arg_count) {
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
    auto it = locals.find(name);
    if (it != locals.end()) {
        current_function->addInstruction(vm::Instruction(vm::Opcode::RETURN_LOCAL, it->second));
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
    if (auto* null_lit = dynamic_cast<const frontend::NullLiteral*>(&expr)) {
        return machine.allocate<vm::object::Null>();
    }
    if (auto* bool_lit = dynamic_cast<const frontend::BoolLiteral*>(&expr)) {
        // TODO: Implement boolean objects
        return machine.allocate<vm::object::Null>();
    }
    if (auto* string_lit = dynamic_cast<const frontend::StringLiteral*>(&expr)) {
        // TODO: Implement string objects
        return machine.allocate<vm::object::Null>();
    }
    if (auto* char_lit = dynamic_cast<const frontend::CharLiteral*>(&expr)) {
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
    // TODO: Implement string literal emission
    auto* null_obj = machine.allocate<vm::object::Null>();
    emit_constant(null_obj);
}

void BytecodeEmitter::visit(const frontend::CharLiteral& expr) {
    // TODO: Implement char literal emission
    auto* null_obj = machine.allocate<vm::object::Null>();
    emit_constant(null_obj);
}

void BytecodeEmitter::visit(const frontend::BoolLiteral& expr) {
    // TODO: Implement boolean literal emission
    auto* null_obj = machine.allocate<vm::object::Null>();
    emit_constant(null_obj);
}

void BytecodeEmitter::visit(const frontend::NullLiteral& expr) {
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
    // Try to load from locals first, then args, then globals
    auto local_it = locals.find(expr.name);
    if (local_it != locals.end()) {
        emit_load_local(expr.name);
    } else {
        auto arg_it = args.find(expr.name);
        if (arg_it != args.end()) {
            emit_load_arg(expr.name);
        } else {
            // Check if it's a global function
            auto global_it = machine.getFunctionTable().find(std::string(expr.name));
            if (global_it != machine.getFunctionTable().end()) {
                // Load the function from global table
                current_function->addInstruction(vm::Instruction(vm::Opcode::LOAD_GLOBAL, global_it->second));
            } else {
                // TODO: Handle undefined variable error
            }
        }
    }
}

void BytecodeEmitter::visit(const frontend::AssignExpr& expr) {
    // Visit the value expression first
    expr.value->accept(*this);
    // Then store to the variable
    auto local_it = locals.find(expr.name);
    if (local_it != locals.end()) {
        emit_store_local(expr.name);
    } else {
        auto arg_it = args.find(expr.name);
        if (arg_it != args.end()) {
            emit_store_arg(expr.name);
        } else {
            // Create new local
            emit_store_local(expr.name);
        }
    }
}

void BytecodeEmitter::visit(const frontend::LogicalExpr& expr) {
    // TODO: Implement logical expressions (&&, ||)
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

void BytecodeEmitter::visit(const frontend::GetExpr& expr) {
    // TODO: Implement property access
}

void BytecodeEmitter::visit(const frontend::SetExpr& expr) {
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
    emit_store_local(stmt.name);
}

void BytecodeEmitter::visit(const frontend::ConstStmt& stmt) {
    if (stmt.initializer) {
        stmt.initializer->accept(*this);
    } else {
        // TODO: Error - const must be initialized
        auto* null_obj = machine.allocate<vm::object::Null>();
        emit_constant(null_obj);
    }
    emit_store_local(stmt.name);
}

void BytecodeEmitter::visit(const frontend::BlockStmt& stmt) {
    for (const auto& statement : stmt.statements) {
        statement->accept(*this);
    }
}

void BytecodeEmitter::visit(const frontend::IfStmt& stmt) {
    // TODO: Implement conditional jumps
    // Current instruction set doesn't support conditional jumps
}

void BytecodeEmitter::visit(const frontend::WhileStmt& stmt) {
    // TODO: Implement while loops
    // Current instruction set doesn't support jumps
}

void BytecodeEmitter::visit(const frontend::ForStmt& stmt) {
    // TODO: Implement for loop
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
            // Check if it's a local variable
            auto local_it = locals.find(var_expr->name);
            if (local_it != locals.end()) {
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
    
    // Save current function and switch to new one
    vm::object::Function* prev_function = current_function;
    current_function = fn;
    
    // Clear symbol tables for new function
    locals.clear();
    args.clear();
    constants.clear();
    
    // Set up argument mapping
    for (size_t i = 0; i < stmt.params.size(); i++) {
        args[stmt.params[i]] = i;
    }
    
    // Visit function body
    stmt.body->accept(*this);
    
    // Add return instruction if not already present
    emit_return_value();
    
    // Restore previous function
    current_function = prev_function;
    
    // Add the function to current function's constants
    emit_constant(fn);
}

void BytecodeEmitter::visit(const frontend::ClassStmt& stmt) {
    // TODO: Implement class definition
    for (const auto& method : stmt.methods) {
        method->accept(*this);
    }
}

}  // namespace vulpes::codegen