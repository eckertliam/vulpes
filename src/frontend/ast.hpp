#pragma once

#include "location.hpp"
#include "token.hpp"

#include <memory>
#include <vector>

namespace vulpes::frontend {

// Forward declarations
struct Expr;
struct Stmt;
struct IntegerLiteral;
struct FloatLiteral;
struct StringLiteral;
struct CharLiteral;
struct BoolLiteral;
struct NullLiteral;
struct UnaryExpr;
struct BinaryExpr;
struct GroupingExpr;
struct VarExpr;
struct AssignExpr;
struct LogicalExpr;
struct CallExpr;
struct GetExpr;
struct SetExpr;
struct ExpressionStmt;
struct LetStmt;
struct ConstStmt;
struct BlockStmt;
struct IfStmt;
struct WhileStmt;
struct ForStmt;
struct ReturnStmt;
struct FunctionStmt;
struct ClassStmt;

struct AstVisitor {
  virtual ~AstVisitor() = default;
  virtual void visit(const IntegerLiteral& expr) = 0;
  virtual void visit(const FloatLiteral& expr) = 0;
  virtual void visit(const StringLiteral& expr) = 0;
  virtual void visit(const CharLiteral& expr) = 0;
  virtual void visit(const BoolLiteral& expr) = 0;
  virtual void visit(const NullLiteral& expr) = 0;
  virtual void visit(const UnaryExpr& expr) = 0;
  virtual void visit(const BinaryExpr& expr) = 0;
  virtual void visit(const GroupingExpr& expr) = 0;
  virtual void visit(const VarExpr& expr) = 0;
  virtual void visit(const AssignExpr& expr) = 0;
  virtual void visit(const LogicalExpr& expr) = 0;
  virtual void visit(const CallExpr& expr) = 0;
  virtual void visit(const GetExpr& expr) = 0;
  virtual void visit(const SetExpr& expr) = 0;
  virtual void visit(const ExpressionStmt& stmt) = 0;
  virtual void visit(const LetStmt& stmt) = 0;
  virtual void visit(const ConstStmt& stmt) = 0;
  virtual void visit(const BlockStmt& stmt) = 0;
  virtual void visit(const IfStmt& stmt) = 0;
  virtual void visit(const WhileStmt& stmt) = 0;
  virtual void visit(const ForStmt& stmt) = 0;
  virtual void visit(const ReturnStmt& stmt) = 0;
  virtual void visit(const FunctionStmt& stmt) = 0;
  virtual void visit(const ClassStmt& stmt) = 0;
};

struct AstNode {
  virtual ~AstNode() = default;
  virtual void accept(AstVisitor& visitor) const = 0;
  Location location;

 protected:
  AstNode() = default;
};

struct Expr : AstNode {};
struct Stmt : AstNode {};

struct IntegerLiteral : Expr {
  IntegerLiteral(const Token& token) { location = token.location; }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct FloatLiteral : Expr {
  FloatLiteral(const Token& token) { location = token.location; }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct StringLiteral : Expr {
  StringLiteral(const Token& token) { location = token.location; }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct CharLiteral : Expr {
  CharLiteral(const Token& token) { location = token.location; }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct BoolLiteral : Expr {
  BoolLiteral(const Token& token) { location = token.location; }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct NullLiteral : Expr {
  NullLiteral(const Token& token) { location = token.location; }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct UnaryExpr : Expr {
  UnaryExpr(const Token& op, std::unique_ptr<Expr> right)
      : op(op), right(std::move(right)) {
    location = op.location;
    location.end_line = this->right->location.end_line;
    location.end_column = this->right->location.end_column;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  Token op;
  std::unique_ptr<Expr> right;
};

struct BinaryExpr : Expr {
  BinaryExpr(std::unique_ptr<Expr> left, const Token& op,
             std::unique_ptr<Expr> right)
      : left(std::move(left)), op(op), right(std::move(right)) {
    location = this->left->location;
    location.end_line = this->right->location.end_line;
    location.end_column = this->right->location.end_column;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  std::unique_ptr<Expr> left;
  Token op;
  std::unique_ptr<Expr> right;
};

struct GroupingExpr : Expr {
  GroupingExpr(std::unique_ptr<Expr> expr) : expr(std::move(expr)) {
    location = this->expr->location;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  std::unique_ptr<Expr> expr;
};

struct VarExpr : Expr {
  VarExpr(const Token& name) : name(name) { location = name.location; }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  Token name;
};

struct AssignExpr : Expr {
  AssignExpr(const Token& name, std::unique_ptr<Expr> value)
      : name(name), value(std::move(value)) {
    location = name.location;
    location.end_line = this->value->location.end_line;
    location.end_column = this->value->location.end_column;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  Token name;
  std::unique_ptr<Expr> value;
};

struct LogicalExpr : Expr {
  LogicalExpr(std::unique_ptr<Expr> left, const Token& op,
              std::unique_ptr<Expr> right)
      : left(std::move(left)), op(op), right(std::move(right)) {
    location = this->left->location;
    location.end_line = this->right->location.end_line;
    location.end_column = this->right->location.end_column;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  std::unique_ptr<Expr> left;
  Token op;
  std::unique_ptr<Expr> right;
};

struct CallExpr : Expr {
  CallExpr(std::unique_ptr<Expr> callee, const Token& paren,
           std::vector<std::unique_ptr<Expr>> arguments)
      : callee(std::move(callee)),
        paren(paren),
        arguments(std::move(arguments)) {
    location = this->callee->location;
    location.end_line = paren.location.end_line;
    location.end_column = paren.location.end_column;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  std::unique_ptr<Expr> callee;
  Token paren;  // For location of ')'
  std::vector<std::unique_ptr<Expr>> arguments;
};

struct GetExpr : Expr {
  GetExpr(std::unique_ptr<Expr> object, const Token& name)
      : object(std::move(object)), name(name) {
    location = this->object->location;
    location.end_line = name.location.end_line;
    location.end_column = name.location.end_column;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  std::unique_ptr<Expr> object;
  Token name;
};

struct SetExpr : Expr {
  SetExpr(std::unique_ptr<Expr> object, const Token& name,
          std::unique_ptr<Expr> value)
      : object(std::move(object)), name(name), value(std::move(value)) {
    location = this->object->location;
    location.end_line = this->value->location.end_line;
    location.end_column = this->value->location.end_column;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  std::unique_ptr<Expr> object;
  Token name;
  std::unique_ptr<Expr> value;
};

struct ExpressionStmt : Stmt {
  ExpressionStmt(std::unique_ptr<Expr> expr) : expr(std::move(expr)) {
    location = this->expr->location;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  std::unique_ptr<Expr> expr;
};

struct LetStmt : Stmt {
  LetStmt(const Token& name, std::unique_ptr<Expr> initializer)
      : name(name), initializer(std::move(initializer)) {
    location = name.location;
    if (this->initializer) {
      location.end_line = this->initializer->location.end_line;
      location.end_column = this->initializer->location.end_column;
    }
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  Token name;
  std::unique_ptr<Expr> initializer;
};

struct ConstStmt : Stmt {
  ConstStmt(const Token& name, std::unique_ptr<Expr> initializer)
      : name(name), initializer(std::move(initializer)) {
    location = name.location;
    if (this->initializer) {
      location.end_line = this->initializer->location.end_line;
      location.end_column = this->initializer->location.end_column;
    }
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  Token name;
  std::unique_ptr<Expr> initializer;
};

struct BlockStmt : Stmt {
  BlockStmt(std::vector<std::unique_ptr<Stmt>> statements)
      : statements(std::move(statements)) {
    if (!this->statements.empty()) {
      location = this->statements.front()->location;
      location.end_line = this->statements.back()->location.end_line;
      location.end_column = this->statements.back()->location.end_column;
    }
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  std::vector<std::unique_ptr<Stmt>> statements;
};

struct IfStmt : Stmt {
  IfStmt(std::unique_ptr<Expr> condition, std::unique_ptr<Stmt> then_branch,
         std::unique_ptr<Stmt> else_branch)
      : condition(std::move(condition)),
        then_branch(std::move(then_branch)),
        else_branch(std::move(else_branch)) {
    location = this->condition->location;
    if (this->else_branch) {
      location.end_line = this->else_branch->location.end_line;
      location.end_column = this->else_branch->location.end_column;
    } else {
      location.end_line = this->then_branch->location.end_line;
      location.end_column = this->then_branch->location.end_column;
    }
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  std::unique_ptr<Expr> condition;
  std::unique_ptr<Stmt> then_branch;
  std::unique_ptr<Stmt> else_branch;
};

struct WhileStmt : Stmt {
  WhileStmt(std::unique_ptr<Expr> condition, std::unique_ptr<Stmt> body)
      : condition(std::move(condition)), body(std::move(body)) {
    location = this->condition->location;
    location.end_line = this->body->location.end_line;
    location.end_column = this->body->location.end_column;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  std::unique_ptr<Expr> condition;
  std::unique_ptr<Stmt> body;
};

struct ForStmt : Stmt {
  ForStmt(const Token& variable, std::unique_ptr<Expr> iterable,
          std::unique_ptr<Stmt> body)
      : variable(variable),
        iterable(std::move(iterable)),
        body(std::move(body)) {
    location = variable.location;
    location.end_line = this->body->location.end_line;
    location.end_column = this->body->location.end_column;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  Token variable;
  std::unique_ptr<Expr> iterable;
  std::unique_ptr<Stmt> body;
};

struct ReturnStmt : Stmt {
  ReturnStmt(const Token& keyword, std::unique_ptr<Expr> value)
      : keyword(keyword), value(std::move(value)) {
    location = keyword.location;
    if (this->value) {
      location.end_line = this->value->location.end_line;
      location.end_column = this->value->location.end_column;
    }
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  Token keyword;
  std::unique_ptr<Expr> value;
};

struct FunctionStmt : Stmt {
  FunctionStmt(const Token& name, const std::vector<Token>& params,
               std::vector<std::unique_ptr<Stmt>> body)
      : name(name), params(params), body(std::move(body)) {
    location = name.location;
    if (!this->body.empty()) {
      location.end_line = this->body.back()->location.end_line;
      location.end_column = this->body.back()->location.end_column;
    }
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  Token name;
  std::vector<Token> params;
  std::vector<std::unique_ptr<Stmt>> body;
};

struct ClassStmt : Stmt {
  ClassStmt(const Token& name,
            std::vector<std::unique_ptr<FunctionStmt>> methods)
      : name(name), methods(std::move(methods)) {
    location = name.location;
    if (!this->methods.empty()) {
      location.end_line = this->methods.back()->location.end_line;
      location.end_column = this->methods.back()->location.end_column;
    }
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
  Token name;
  std::vector<std::unique_ptr<FunctionStmt>> methods;
};

}  // namespace vulpes::frontend
